from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from scipy.optimize import OptimizeResult, least_squares

from plxcontroller.plaxis_2d_input_controller import Plaxis2DInputController
from plxcontroller.plaxis_2d_output_controller import Plaxis2DOutputController


@dataclass(frozen=True)
class MeasuredValueAtPoint:
    point_identification: str
    result_type: str
    time: float
    value: float
    point_type: Literal["node", "stresspoint"] = "node"
    weight: float = 1.0
    relative_to_point: str | None = None

    def __post_init__(self) -> None:
        if self.point_type not in ("node", "stresspoint"):
            raise ValueError("point_type must be either 'node' or 'stresspoint'.")
        if not 0 <= self.weight:
            raise ValueError("Weight must be non-negative.")


@dataclass(frozen=True)
class MaterialParameterInput:
    material_identification: str
    parameter_name: str
    initial_value: float
    min_value: float | None = None
    max_value: float | None = None
    dependent_parameters: list[
        DependentParameter
    ] | None = None  # List of ParameterDependency instances

    def __post_init__(self) -> None:
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError("min_value cannot be greater than max_value.")
            if not self.min_value <= self.initial_value <= self.max_value:
                raise ValueError(
                    "initial_value must be between min_value and max_value."
                )


@dataclass(frozen=True)
class MaterialParameterValue:
    material_identification: str
    parameter_name: str
    value: float


@dataclass(frozen=True)
class DependentParameter:
    name: str
    """The name of the dependent parameter."""
    ratio: float
    """The ratio of the dependent parameter value to the main parameter value.
    For example, if the dependent parameter should be half of the main parameter, 
    the ratio would be 0.5."""

    def __post_init__(self) -> None:
        if self.ratio <= 0:
            raise ValueError("Dependency ratio must be positive.")


@dataclass(frozen=True)
class OptimizationIterationResult:
    iteration_number: int
    material_parameters: list[MaterialParameterValue]
    measured_values: list[MeasuredValueAtPoint]
    result_values: list[float]
    scipy_optimize_result: OptimizeResult

    @property
    def material_parameters_dataframe(self) -> pd.DataFrame:
        """Returns the material parameters of this iteration result as a pandas DataFrame."""
        return pd.DataFrame(
            [
                {
                    "material_identification": param.material_identification,
                    "parameter_name": param.parameter_name,
                    "value": param.value,
                }
                for param in self.material_parameters
            ]
        )

    @property
    def residuals_dataframe(self) -> pd.DataFrame:
        """Returns the measured values and corresponding result values of this iteration result as a pandas DataFrame."""
        if len(self.measured_values) != len(self.result_values):
            raise ValueError(
                "The number of measured values must match the number of result values."
            )

        return pd.DataFrame(
            [
                {
                    "point_identification": measured_value.point_identification,
                    "result_type": measured_value.result_type,
                    "time": measured_value.time,
                    "measured_value": measured_value.value,
                    "result_value": self.result_values[i],
                    "unweighted_residual": self.result_values[i] - measured_value.value,
                    "weight": measured_value.weight,
                    "residual": residual,
                    "gradient": gradient,
                }
                for i, (measured_value, residual, gradient) in enumerate(
                    zip(
                        self.measured_values,
                        self.scipy_optimize_result.fun,
                        self.scipy_optimize_result.grad,
                    )
                )
            ]
        )

    def optimization_measures(self) -> dict[str, float]:
        """Returns a dictionary of optimization measures from the scipy OptimizeResult."""
        return {
            "iteration_number": self.iteration_number,
            "cost": self.scipy_optimize_result.cost,
            "optimality": self.scipy_optimize_result.optimality,
            "nfev": self.scipy_optimize_result.nfev,
            "njev": self.scipy_optimize_result.njev,
            "status": self.scipy_optimize_result.status,
            "message": self.scipy_optimize_result.message,
            "success": self.scipy_optimize_result.success,
        }

    def plot_measured_vs_result_time_histories(
        self, plots_per_figure: int = 3, iteration_number: int | None = None
    ) -> list[Figure]:
        """Plots the measured values and result values of this iteration result as a function of time."""
        if len(self.measured_values) != len(self.result_values):
            raise ValueError(
                "The number of measured values must match the number of result values."
            )

        # Get the unique combinations of measured node names and result types in the residuals dataframe
        unique_measured_node_and_result_type_combinations = (
            self.residuals_dataframe[["point_identification", "result_type"]]
            .drop_duplicates()
            .values.tolist()
        )

        # For each unique_measured_node_and_result_type_combinations, get the time history and plot it in a separate plot.
        # Save them to a PDF with 3 plots per page and return the PDF as bytes.
        figures = []
        for i, (point_identification, result_type) in enumerate(
            unique_measured_node_and_result_type_combinations
        ):
            df = self.residuals_dataframe
            df_subset = df[
                (df["point_identification"] == point_identification)
                & (df["result_type"] == result_type)
            ]
            i_axes = i % plots_per_figure
            if i_axes == 0:
                fig, axes = plt.subplots(
                    plots_per_figure, 1, sharex=True, figsize=(10, 5 * plots_per_figure)
                )
                figures.append(fig)
            axes[i_axes].plot(
                df_subset["time"], df_subset["measured_value"], label="Measured"
            )
            axes[i_axes].plot(
                df_subset["time"], df_subset["result_value"], label="Result"
            )
            axes[i_axes].set_xlabel("Time")
            axes[i_axes].set_ylabel(f"{result_type} at {point_identification}")
            if iteration_number is not None:
                axes[i_axes].set_title(
                    f"Measured vs Result {result_type} at {point_identification} for iteration {iteration_number}"
                )
            else:
                axes[i_axes].set_title(
                    f"Measured vs Result {result_type} at {point_identification}"
                )
            axes[i_axes].legend()
            axes[i_axes].grid()

        return figures


class ParameterOptimization2D:
    def __init__(
        self,
        model_path: str,
        ip_address: str = "localhost",
        input_port: int = 10000,
        output_port: int = 10001,
    ) -> None:
        self._input_controller = Plaxis2DInputController()
        self._output_controller = Plaxis2DOutputController()
        self._model_path = model_path
        self.ip_address = ip_address
        self.input_port = input_port
        self.output_port = output_port

        self._optimization_model_path = model_path.replace(
            ".p2dx", "_optimization.p2dx"
        )

        self._measured_values: list[MeasuredValueAtPoint] | None = None
        self._material_parameter_inputs: list[MaterialParameterInput] | None = None

        # Relevant for post-processing and logging during optimization
        self._iterations_directory = os.path.join(
            os.path.dirname(model_path), "iterations"
        )
        self._iteration_number = 0
        self._iteration_result_values: list[float] | None = None
        self._save_intermediate_models = False

    @property
    def input_controller(self) -> Plaxis2DInputController:
        """Returns the input controller."""
        return self._input_controller

    @property
    def output_controller(self) -> Plaxis2DOutputController:
        """Returns the output controller."""
        return self._output_controller

    @property
    def ci(self) -> Plaxis2DInputController:
        """Alias of input_controller."""
        return self._input_controller

    @property
    def co(self) -> Plaxis2DOutputController:
        """Alias of output_controller."""
        return self._output_controller

    @property
    def model_path(self) -> str:
        """Returns the original model path."""
        return self._model_path

    @property
    def optimization_model_path(self) -> str:
        """Returns the path for the optimization model."""
        return self._optimization_model_path

    @property
    def iterations_directory(self) -> str:
        """Returns the directory where iteration models are stored."""
        return self._iterations_directory

    @property
    def measured_values(self) -> list[MeasuredValueAtPoint] | None:
        """Returns the list of measured point results."""
        return self._measured_values

    @measured_values.setter
    def measured_values(self, measured_values: list[MeasuredValueAtPoint]) -> None:
        """Sets the list of measured point results."""
        self._measured_values = measured_values

    @property
    def unique_measured_nodes(self) -> set[str]:
        """Returns a set of unique measured node names."""
        if self.measured_values is None:
            return set()
        return set(
            result.point_identification
            for result in self.measured_values
            if result.point_type == "node"
        )

    @property
    def unique_measured_stresspoints(self) -> set[str]:
        """Returns a set of unique measured stress point names."""
        if self.measured_values is None:
            return set()
        return set(
            result.point_identification
            for result in self.measured_values
            if result.point_type == "stresspoint"
        )

    @property
    def unique_measured_node_and_result_type_combinations(self) -> set[tuple[str, str]]:
        """Returns a set of unique combinations of measured node names and result types."""
        if self.measured_values is None:
            return set()
        return set(
            (result.point_identification, result.result_type)
            for result in self.measured_values
            if result.point_type == "node"
        )

    @property
    def material_parameter_inputs(self) -> list[MaterialParameterInput] | None:
        """Returns the list of material parameter bounds."""
        return self._material_parameter_inputs

    @material_parameter_inputs.setter
    def material_parameter_inputs(
        self, material_parameter_inputs: list[MaterialParameterInput]
    ) -> None:
        """Sets the list of material parameter bounds."""
        self._material_parameter_inputs = material_parameter_inputs

    @property
    def lower_bounds(self) -> list[float] | float:
        """Returns a list of lower bounds for the material parameters, in the same order as self.material_parameter_inputs."""
        if self.material_parameter_inputs is None:
            return -np.inf
        return [
            bound.min_value if bound.min_value is not None else -np.inf
            for bound in self.material_parameter_inputs
        ]

    @property
    def upper_bounds(self) -> list[float] | float:
        """Returns a list of upper bounds for the material parameters, in the same order as self.material_parameter_input."""
        if self.material_parameter_inputs is None:
            return np.inf
        return [
            bound.max_value if bound.max_value is not None else np.inf
            for bound in self.material_parameter_inputs
        ]

    @property
    def initial_values(self) -> list[float]:
        """Returns a list of initial values for the material parameters, in the same order as self.material_parameter_input."""
        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter input must be defined before accessing initial values."
            )
        return [input.initial_value for input in self.material_parameter_inputs]

    @property
    def material_parameter_inputs_dictionary(
        self,
    ) -> dict[tuple[str, str], MaterialParameterInput] | None:
        """Returns a dictionary mapping (material_identification, parameter_name) to MaterialParameterInput."""
        if self.material_parameter_inputs is None:
            return None
        return {
            (input.material_identification, input.parameter_name): input
            for input in self.material_parameter_inputs
        }

    def _create_optimization_model(self) -> None:
        """Creates the optimization model by copying the original model."""
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(f"Original model file not found: {self.model_path}")
        if not os.path.isdir(self.model_path.replace(".p2dx", ".p2dxdat")):
            raise FileNotFoundError(
                f"Original model data directory not found: {self.model_path.replace('.p2dx', '.p2dxdat')}"
            )

        shutil.copyfile(self.model_path, self.optimization_model_path)
        shutil.copytree(
            self.model_path.replace(".p2dx", ".p2dxdat"),
            self.optimization_model_path.replace(".p2dx", ".p2dxdat"),
        )

    def check_all_measured_points_exist(self, model_path: str) -> None:
        """Checks if all measured points (nodes and stress points) exist in the PLAXIS model."""
        if self.co._server is None:
            raise ValueError(
                "Cannot check measured points because the output controller is not connected to the PLAXIS model."
            )

        if self.measured_values is None:
            raise ValueError("No measured values defined.")

        self.co.open(model_path)
        self.co.request_precalculated_points(point_type="all")
        self.co.close()

        existing_nodes = self.co._precalculated_nodes.keys()
        existing_stresspoints = self.co._precalculated_stress_points.keys()

        for measured_value in self.measured_values:
            if (
                measured_value.point_type == "node"
                and measured_value.point_identification not in existing_nodes
            ):
                raise ValueError(
                    f"Measured node '{measured_value.point_identification}' does not exist in the model."
                )
            elif (
                measured_value.point_type == "stresspoint"
                and measured_value.point_identification not in existing_stresspoints
            ):
                raise ValueError(
                    f"Measured stress point '{measured_value.point_identification}' does not exist in the model."
                )

        # Check unique relative points
        unique_relative_points = set(
            (result.relative_to_point, result.point_type)
            for result in self.measured_values
            if result.relative_to_point is not None
        )
        for relative_point, point_type in unique_relative_points:
            if (point_type == "node" and relative_point not in existing_nodes) or (
                point_type == "stresspoint"
                and relative_point not in existing_stresspoints
            ):
                raise ValueError(
                    f"Relative {point_type} '{relative_point}' does not exist in the model."
                )

        return

    def kill(self) -> None:
        """Kills both the input and output controllers."""
        self.ci.kill()
        self.co.kill()

    def get_material_parameter_values(
        self, model_path: str
    ) -> list[MaterialParameterValue]:
        """Retrieves the initial material parameter values from the PLAXIS model.

        Returns
        -------
        list[MaterialParameterValue]
            A list of MaterialParameterValue objects representing the initial material parameter values.
        """
        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter bounds must be defined before getting material parameter values."
            )

        if self.ci._server is None:
            raise ValueError(
                "Cannot get material parameters because the input controller is not connected to the PLAXIS model."
            )

        self.ci.open(model_path)

        materials_dict = self.ci.get_all_materials_by_identification()

        material_parameters = []
        for material_parameter_bound in self.material_parameter_inputs:
            material_name = material_parameter_bound.material_identification
            parameter_name = material_parameter_bound.parameter_name

            if material_name not in materials_dict:
                raise ValueError(f"Material '{material_name}' not found in the model.")

            parameter_value = self.ci.get_material_parameter_value(
                material=materials_dict[material_name], parameter_name=parameter_name
            )

            material_parameters.append(
                MaterialParameterValue(
                    material_identification=material_name,
                    parameter_name=parameter_name,
                    value=parameter_value,
                )
            )

        self.ci.close()

        return material_parameters

    def check_all_parameters_within_bounds(
        self, material_parameters: list[MaterialParameterValue]
    ) -> None:
        """Checks if all material parameters are within their specified bounds.

        Parameters
        ----------
        material_parameters : list[MaterialParameterValue]
            A list of MaterialParameterValue objects representing the material parameters to check.

        Raises
        -------
        ValueError
            If material parameter bounds are not defined or if a parameter has no defined bounds.
        """
        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter bounds must be defined before checking parameter values."
            )

        inputs_dict = {
            (bound.material_identification, bound.parameter_name): bound
            for bound in self.material_parameter_inputs
        }

        for param in material_parameters:
            key = (param.material_identification, param.parameter_name)
            if key not in inputs_dict:
                raise ValueError(
                    f"No bounds defined for material '{param.material_identification}' and parameter '{param.parameter_name}'."
                )

            bound = inputs_dict[key]
            if (bound.min_value is not None and param.value < bound.min_value) or (
                bound.max_value is not None and param.value > bound.max_value
            ):
                raise ValueError(
                    f"Parameter '{param.parameter_name}' of material '{param.material_identification}' with value {param.value} is out of bounds (min: {bound.min_value}, max: {bound.max_value})."
                )

        return

    def material_parameters_to_list(
        self, material_parameters: list[MaterialParameterValue]
    ) -> list[float]:
        """Converts a list of MaterialParameterValue objects to a list of their values.

        Parameters
        ----------
        material_parameters : list[MaterialParameterValue]
            A list of MaterialParameterValue objects.

        Returns
        -------
        list[float]
            A list of the values of the material parameters, in the same order as the input list.
        """
        return [param.value for param in material_parameters]

    def map_values_to_material_parameters(
        self, values: list[float]
    ) -> list[MaterialParameterValue]:
        """Converts a list of numerical values to a list of MaterialParameterValue objects, using the material parameter bounds to determine the corresponding material and parameter names.

        Parameters
        ----------
        values : list[float]
            A list of numerical values representing material parameters, in the same order as self.material_parameter_bounds.

        Returns
        -------
        list[MaterialParameterValue]
            A list of MaterialParameterValue objects corresponding to the input values.
        """
        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter bounds must be defined before converting numerical values to material parameter values."
            )

        if len(values) != len(self.material_parameter_inputs):
            raise ValueError(
                f"The number of input values ({len(values)}) must match the number of material parameter bounds ({len(self.material_parameter_inputs)})."
            )

        material_parameter_values = []
        for value, bound in zip(values, self.material_parameter_inputs):
            material_parameter_values.append(
                MaterialParameterValue(
                    material_identification=bound.material_identification,
                    parameter_name=bound.parameter_name,
                    value=value,
                )
            )

        return material_parameter_values

    def update_material_parameter_values_in_model(
        self, material_parameter_values: list[MaterialParameterValue]
    ) -> None:
        """Updates the material parameter values in the PLAXIS model using the provided material parameter values."""
        if self.ci._server is None:
            raise ValueError(
                "Cannot change material parameters because the input controller is not connected to the PLAXIS model."
            )
        if self.ci._filepath != self.optimization_model_path:
            raise ValueError(
                "Input controller is not connected to the optimization model. Please connect to the optimization model before changing material parameters."
            )

        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter bounds must be defined before updating material parameter values."
            )

        if len(self.material_parameter_inputs) != len(material_parameter_values):
            raise ValueError(
                f"The number of material parameter values ({len(material_parameter_values)}) must match the number of material parameter bounds ({len(self.material_parameter_inputs)})."
            )

        materials_dict = self.ci.get_all_materials_by_identification()

        # Update material parameter values in the model
        for i, material_parameter in enumerate(material_parameter_values):
            if material_parameter.material_identification not in materials_dict:
                raise ValueError(
                    f"Material '{material_parameter.material_identification}' not found in the model."
                )

            # Update the materialvalue
            self.ci.set_material_parameter_value(
                material=materials_dict[material_parameter.material_identification],
                parameter_name=material_parameter.parameter_name,
                value=material_parameter.value,
            )

            # Update all the dependent parameters for this material parameter
            material_parameter_input = self.material_parameter_inputs[i]
            if material_parameter_input.dependent_parameters is not None:
                for dependency in material_parameter_input.dependent_parameters:
                    self.ci.set_material_parameter_value(
                        material=materials_dict[
                            material_parameter.material_identification
                        ],
                        parameter_name=dependency.name,
                        value=material_parameter.value * dependency.ratio,
                    )

    def get_results_at_measured_points(self) -> list[float]:
        """Retrieves the simulation results at the measured points.

        Returns
        -------
        list[float]
            A list of simulated values corresponding to the measured points, in the same order as self.measured_values.
        """
        if self.co._server is None:
            raise ValueError(
                "Cannot get results at measured points because the output controller is not connected to the PLAXIS model."
            )
        if self.co._filepath != self.optimization_model_path:
            raise ValueError(
                "Output controller is not connected to the optimization model. Please connect to the optimization model before getting results at measured points."
            )

        if self.measured_values is None:
            raise ValueError(
                "Measured values must be defined before getting results at measured points."
            )

        # TODO: Improve this. For now taking all phases, with exception of the initial
        phase_numbers = [
            self.co.get_phase_number_from_phase_name(phase)
            for phase in self.co.g_o.Phases[:-1]
        ]

        # TODO: Improve this. For now taking all the results for all the points
        result_type_names = list(
            set(measured_value.result_type for measured_value in self.measured_values)
        )

        results = self.co.get_node_time_history_results(
            phase_numbers=phase_numbers, result_type_names=result_type_names
        )

        # Result dataframe
        df = results.to_dataframe()

        # Map results to measured values
        # TODO: Improve this. Now it is assumed that the time is organized.
        raw_results_per_point_and_result_type: dict[
            tuple[str, str], dict[str, list[float]]
        ] = {}
        for (
            point_identification,
            result_type,
        ) in self.unique_measured_node_and_result_type_combinations:
            try:
                point_raw_results = df[
                    df["point_identification"] == point_identification
                ][["time", result_type]]
            except Exception as e:
                raise ValueError(
                    f"Error retrieving results for point '{point_identification}' and result type '{result_type}': {e}"
                )
            # Assuming time is the same for all results of the same point and result type
            raw_results_per_point_and_result_type[
                (point_identification, result_type)
            ] = {
                "time": point_raw_results["time"].values.tolist(),
                "value": point_raw_results[result_type].values.tolist(),
            }

        # Interpolate results at the measured times
        result_values = []
        for measured_value in self.measured_values:
            # Check that the measured time is within the range of the simulated times for the corresponding point and result type
            simulated_times = raw_results_per_point_and_result_type[
                (measured_value.point_identification, measured_value.result_type)
            ]["time"]
            if not (simulated_times[0] <= measured_value.time <= simulated_times[-1]):
                raise ValueError(
                    f"Measured time {measured_value.time} for point '{measured_value.point_identification}' and result type '{measured_value.result_type}' is out of bounds of the simulated times (min: {simulated_times[0]}, max: {simulated_times[-1]})."
                )
            result_value = np.interp(
                measured_value.time,
                simulated_times,
                raw_results_per_point_and_result_type[
                    (measured_value.point_identification, measured_value.result_type)
                ]["value"],
            )[0]

            # If there is a relative point, subtract the relative point value from the main point value
            relative_point_result_value = 0.0
            if measured_value.relative_to_point is not None:
                relative_point_simulated_times = raw_results_per_point_and_result_type[
                    (measured_value.relative_to_point, measured_value.point_type)
                ]["time"]
                if not (
                    relative_point_simulated_times[0]
                    <= measured_value.time
                    <= relative_point_simulated_times[-1]
                ):
                    raise ValueError(
                        f"Measured time {measured_value.time} for relative point '{measured_value.relative_to_point}' and result type '{measured_value.result_type}' is out of bounds of the simulated times for the relative point (min: {relative_point_simulated_times[0]}, max: {relative_point_simulated_times[-1]})."
                    )
                relative_point_result_value = np.interp(
                    measured_value.time,
                    relative_point_simulated_times,
                    raw_results_per_point_and_result_type[
                        (measured_value.relative_to_point, measured_value.point_type)
                    ]["value"],
                )[0]

            # Interpolate the simulated result at the measured time
            result_values.append(result_value - relative_point_result_value)
        return result_values

    def compute_residuals(self, x: list[float]) -> list[float]:
        """
        Computes the residuals between the simulated results at the measured points and the actual measured values, given a set of material parameter values.

        Parameters
        ----------
        x : list[float]
            A list of material parameter values to set in the model, in the same order as self.material_parameter_bounds.
        """

        if self.measured_values is None:
            raise ValueError(
                "Measured values must be defined before computing residuals."
            )

        if self.ci._server is None:
            raise ValueError(
                "Cannot compute residuals because the input controller is not connected to the PLAXIS model."
            )

        if self.ci._filepath != self.optimization_model_path:
            raise ValueError(
                "Input controller is not connected to the optimization model. Please connect to the optimization model before changing material parameters."
            )

        # Convert the input values to material parameter values and update the model
        material_parameter_values = self.map_values_to_material_parameters(x)

        # Update the material parameter values in the model
        self.update_material_parameter_values_in_model(material_parameter_values)

        # Recalculate the model with the new material parameter values
        self.ci.recalculate_all_phases()

        # Get the simulated results at the measured points
        simulated_values = self.get_results_at_measured_points()

        # Store the iteration result for post-processing and logging
        self._iteration_result_values = simulated_values

        # Compute the residuals (simulated - measured) for each measured point, applying the weights
        residuals = []
        for measured_value, simulated_value in zip(
            self.measured_values, simulated_values
        ):
            residuals.append(
                measured_value.weight * (simulated_value - measured_value.value)
            )

        return residuals

    def post_process_intermediate_result(
        self,
        intermediate_result: OptimizeResult,
    ) -> None:
        """
        Performs post-processing after each optimization iteration, such as saving the model with the current material parameter values and logging the results.

        Parameters
        ----------
        intermediate_result : OptimizeResult
            An object containing the results of the current optimization iteration, including the iteration number, material parameter values, and error metric.
        """
        # Update iteration number
        self._iteration_number += 1

        if self._save_intermediate_models:
            # Save the model with the current material parameter values
            current_model_basename = os.path.basename(self.optimization_model_path)
            self.ci.copy_current_model(
                new_filepath=os.path.join(
                    self._iterations_directory,
                    f"iteration_{self._iteration_number}_{current_model_basename}.p2dx",
                )
            )

        # Create the optimization iteration result for post-processing and logging
        optimization_iteration_result = OptimizationIterationResult(
            iteration_number=self._iteration_number,
            material_parameters=self.map_values_to_material_parameters(
                intermediate_result.x.tolist()
            ),
            measured_values=self.measured_values
            if self.measured_values is not None
            else [],
            result_values=self._iteration_result_values
            if self._iteration_result_values is not None
            else [],
            scipy_optimize_result=intermediate_result,
        )

        # Store dataframes to .csv and the optimization measures to .json for this iteration
        optimization_iteration_result.material_parameters_dataframe.to_csv(
            os.path.join(
                self._iterations_directory,
                f"iteration_{self._iteration_number}_material_parameters.csv",
            ),
            index=False,
        )
        optimization_iteration_result.residuals_dataframe.to_csv(
            os.path.join(
                self._iterations_directory,
                f"iteration_{self._iteration_number}_residuals.csv",
            ),
            index=False,
        )
        optimization_measures = optimization_iteration_result.optimization_measures()
        with open(
            os.path.join(
                self._iterations_directory,
                f"iteration_{self._iteration_number}_optimization_measures.json",
            ),
            "w",
        ) as f:
            json.dump(optimization_measures, f, indent=4)

        # Plot the measured vs result time histories for this iteration and save the plots to a PDF
        figures = optimization_iteration_result.plot_measured_vs_result_time_histories(
            plots_per_figure=3, iteration_number=self._iteration_number
        )
        with PdfPages(
            os.path.join(
                self._iterations_directory,
                f"iteration_{self._iteration_number}_measured_vs_result_time_histories.pdf",
            )
        ) as pdf:
            for fig in figures:
                pdf.savefig(fig)
                plt.close(fig)

        return

    def optimize(
        self,
        max_nfev: int = 100,
        method: str = "trf",
        ftol: float = 1e-8,
        xtol: float = 1e-8,
        gtol: float = 1e-8,
        verbose: int = 2,
        save_intermediate_models: bool = False,
    ) -> OptimizationIterationResult:
        """Performs the parameter optimization process."""
        # Check that measured values are defined
        if self.measured_values is None:
            raise ValueError("Measured values must be defined before optimization.")

        # Check that material parameter bounds are defined
        if self.material_parameter_inputs is None:
            raise ValueError(
                "Material parameter bounds must be defined before optimization."
            )

        # Check that iteration directory does not exist, to avoid overwriting previous optimization results
        if os.path.exists(self.iterations_directory):
            raise FileExistsError(
                f"Iteration directory '{self.iterations_directory}' already exists. Please remove or rename it before starting optimization to avoid overwriting previous results."
            )
        os.makedirs(self.iterations_directory)

        # Connect to the input and output controllers to their respective PLAXIS servers
        self.ci.connect(ip_address=self.ip_address, port=self.input_port)
        self.co.connect(ip_address=self.ip_address, port=self.output_port)

        # Check if all measured points exist in the model
        try:
            self.check_all_measured_points_exist(model_path=self.model_path)
        except ValueError as e:
            self.kill()
            raise ValueError(f"Error during optimization: {e}")
        print("All measured points exist in the model. Proceeding with optimization.")

        # Create the optimization model by copying the original model
        try:
            self._create_optimization_model()
        except Exception as e:
            self.kill()
            raise IOError(f"Failed to create optimization model: {e}")
        print("Optimization model created successfully.")

        # Start optimization using scipy's least_squares function, with the compute_residuals method as
        # the objective function and the initial material parameter values as the starting point
        self._iteration_number = 0
        self._iteration_result_values = None
        self._save_intermediate_models = save_intermediate_models

        try:
            optimization_result = least_squares(
                fun=self.compute_residuals,
                x0=self.initial_values,
                method=method,
                bounds=(self.lower_bounds, self.upper_bounds),
                xtol=xtol,
                ftol=ftol,
                gtol=gtol,
                max_nfev=max_nfev,
                callback=self.post_process_intermediate_result,
                verbose=verbose,
            )
        except Exception as e:
            self.kill()
            raise RuntimeError(f"Optimization failed: {e}")

        print("Optimization completed successfully.")

        # Kill processes
        self.kill()

        return optimization_result
