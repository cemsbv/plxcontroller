from __future__ import annotations

import os
import subprocess
from typing import Literal

from plxscripting.plxproxy import PlxProxyGlobalObject, PlxProxyObject
from plxscripting.server import Server, new_server

from plxcontroller.results_2d.point_time_history_result_2d import (
    MultiPhaseMultiPointTimeHistoryResult2D,
    SinglePhaseMultiPointTimeHistoryResult2D,
    SinglePhaseSinglePointTimeHistoryResult2D,
    SinglePointTimeHistoryResult2D,
)


class Plaxis2DOutputController:
    def __init__(self) -> None:
        """Creates a new Plaxis2DOutputController instance."""
        self._server: Server | None = None
        self._subprocess: subprocess.Popen | None = None
        self._filepath: str | None = None
        self._precalculated_nodes: dict[str, PlxProxyObject] = {}
        self._precalculated_stress_points: dict[str, PlxProxyObject] = {}
        self._node_time_history_results: dict[
            str, list[SinglePhaseSinglePointTimeHistoryResult2D]
        ] = {}

    @property
    def s_o(self) -> Server | None:
        """Returns the server object. This is a typical alias for the server object."""
        return self._server

    @property
    def g_o(self) -> PlxProxyGlobalObject:
        """Returns the global project object. This is a typical alias for the global project object."""
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")
        return self._server.plx_global

    def connect(self, ip_address: str = "localhost", port: int = 10001) -> None:
        """Starts a new Plaxis instance and a new server connection with the given IP address and port and
        connect to it.

        Args:
            ip_address (str): the IP address of the Plaxis server. Defaults to "localhost".
            port (int, optional): the port to of the Plaxis server. Defaults to 10001.
        """

        plaxis_path = os.getenv("PLAXIS_2D_OUTPUT_PROGRAM")
        if not plaxis_path:
            raise ValueError(
                'Environmental variable "PLAXIS_2D_OUTPUT_PROGRAM" is not set.'
            )
        if not os.path.exists(plaxis_path):
            raise ValueError(
                f'PLAXIS 2D Output program path "{plaxis_path}" does not exist.'
            )

        password = os.getenv("PLAXIS_2D_PASSWORD")
        if not password:
            raise ValueError('Environmental variable "PLAXIS_2D_PASSWORD" is not set.')

        # Create subprocess
        self._subprocess = subprocess.Popen(
            [
                plaxis_path,
                f"--AppServerPort={port}",
                f"--AppServerPassword={password}",
            ],
        )

        # Connect to PLAXIS remote server
        server, _ = new_server(ip_address, port, password=password)

        # Store the server
        self._server = server

    def open(self, filepath: str) -> None:
        """Open a PLAXIS model file.

        Args:
            filepath (str): the path to the PLAXIS model file.
        """
        if not self._server:
            raise ValueError("No server connection available.")

        self._server.open(filepath)
        self._filepath = filepath

    def close(self) -> None:
        """Close the PLAXIS model file."""
        if not self._server:
            raise ValueError("No server connection available.")

        self._server.close()
        self._filepath = None

    def disconnect(self) -> None:
        """Disconnect from the PLAXIS server."""

        if self._subprocess is not None and self._subprocess.stdin is not None:
            plaxis_path = os.getenv("PLAXIS_2D_OUTPUT_PROGRAM")
            if isinstance(plaxis_path, str):
                self._subprocess.stdin.write(f"taskkill /IM {plaxis_path}\n".encode())
            self._subprocess.terminate()

        self._server = None
        self._subprocess = None
        self._filepath = None
        self._precalculated_nodes = {}
        self._precalculated_stress_points = {}

    def get_phase_number_from_phase_name(self, phase: PlxProxyObject) -> int:
        """Get the phase number from the phase.

        Parameters
        ----------
        phase : PlxProxyObject
            the phase object.
        Returns
        -------
        int
            the number of the phase.
        """
        try:
            return int(phase.Name.value.split("Phase_")[-1])
        except ValueError:
            raise ValueError(
                f"Unexpected phase name: {phase.Name.value}. Expected to end with an integer after 'Phase_'."
            )

    def get_phase_from_phase_number(self, phase_number: int) -> PlxProxyObject:
        """Get the phase object from the phase number.

        Parameters
        ----------
        phase_number : int
            the number of the phase.
        Returns
        -------
        PlxProxyObject
            the phase object.
        """
        try:
            phase = getattr(self.g_o, f"Phase_{phase_number}")
        except AttributeError:
            raise ValueError(
                f"Unexpected phase number: {phase_number}. No such phase in PLAXIS model."
            )
        return phase

    def get_step_from_step_number(self, step_number: int) -> PlxProxyObject:
        """Get the step object from the step number.

        Parameters
        ----------
        step_number : int
            the number of the step.
        Returns
        -------
        PlxProxyObject
            the step object.
        """
        try:
            step = getattr(self.g_o, f"Step_{step_number}")
        except AttributeError:
            raise ValueError(
                f"Unexpected step number: {step_number}. No such step in PLAXIS model."
            )
        return step

    def get_result_type_from_string(self, result_type_str: str) -> PlxProxyObject:
        """Get the PLAXIS result type from a string.

        Parameters
        ----------
        result_type_str : str
            the string representing the result type. Expected format is "Category.Result", e.g. "Soil.X".

        Returns
        -------
        PlxProxyObject
            the PLAXIS result type object.
        """
        if "." not in result_type_str:
            raise ValueError(
                f"Unexpected result type string: {result_type_str}. Expected format is 'Category.Result', e.g. 'Soil.X'."
            )
        category_str, result_str = result_type_str.split(".")
        try:
            category = getattr(self.g_o.ResultTypes, category_str)
        except AttributeError:
            raise ValueError(
                f"Unexpected result category: {category_str}. No such category in PLAXIS ResultTypes."
            )
        try:
            result_type = getattr(category, result_str)
        except AttributeError:
            raise ValueError(
                f"Unexpected result type: {result_str}. No such result type in PLAXIS ResultTypes.{category_str}."
            )
        return result_type

    def request_precalculated_points(
        self, point_type: Literal["all", "node", "stresspoint"] = "all"
    ) -> None:
        """
        Request and store the precalculated points (nodes and/or stress points) in the PLAXIS model
        and store them in the controller instance.

        Parameters
        ----------
        point_type : Literal["all", "node", "stresspoint"], optional
            the type of points to request. If "all", both nodes and stress points are requested.
            (default is "all").
        """
        # Nodes
        if point_type in ["all", "node"]:
            for node in self.g_o.Nodes:
                self._precalculated_nodes[node.Name.value] = node

        # Stress points
        if point_type in ["all", "stresspoint"]:
            for stress_point in self.g_o.StressPoints:
                self._precalculated_stress_points[
                    stress_point.Name.value
                ] = stress_point

        return

    def get_node_time_history_results(
        self, phase_numbers: list[int], result_type_names: list[str]
    ) -> MultiPhaseMultiPointTimeHistoryResult2D:
        """
        Get the node time history results for the given phase numbers and result types in the PLAXIS model
        and store them in the controller instance.

        Parameters
        ----------
        phase_numbers : list[int]
            the numbers of the phases for which the results are requested.
        result_type_names : list[str]
            the list of result type names for which the results are requested. Expected format for each result
            type name is "Category.Result", e.g. "Soil.X".
        """
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")
        if not isinstance(self._filepath, str):
            raise ValueError("No PLAXIS model file is currently open.")

        # Get plaxis objects from input
        phases = [
            self.get_phase_from_phase_number(phase_number)
            for phase_number in phase_numbers
        ]
        result_types = [
            self.get_result_type_from_string(result_type_name)
            for result_type_name in result_type_names
        ]

        # Start input program to retrieve phase input data
        from plxcontroller.plaxis_2d_input_controller import Plaxis2DInputController

        ci = Plaxis2DInputController()
        ci.connect(
            ip_address=self._server.connection.host,
            port=self._server.connection.port + 1,  # TODO: improve this
        )
        ci.open(self._filepath)

        # Get step output and the step number to step object mapping for the given phase number
        step_number_to_step = {}
        step_numbers_per_phase = {}
        time_numbers_per_phase = {}
        for phase_number in phase_numbers:
            # Get first and last step number of the phase
            phase_input = ci.get_phase_from_phase_number(phase_number)
            phase_start_step = phase_input.FirstStep.value
            phase_end_step = phase_input.LastStep.value
            # Generate step output for the phase
            step_numbers_per_phase[phase_number] = list(
                range(phase_start_step, phase_end_step + 1, 1)
            )
            # Get time output and the step number mapping
            for step_number in step_numbers_per_phase[phase_number]:
                step_number_to_step[step_number] = self.get_step_from_step_number(
                    step_number
                )
                time_numbers_per_phase[phase_number] = step_number_to_step[
                    step_number
                ].Reached.Time.value

        # Close the input program and disconnect
        ci.close()
        ci.disconnect()

        # Request for each phase
        multi_phase_multi_point_results = MultiPhaseMultiPointTimeHistoryResult2D()
        for phase_number, phase in zip(phase_numbers, phases):
            phase_name = phase.Name.value
            phase_identification = phase.Identification.value
            single_phase_multi_point_results = SinglePhaseMultiPointTimeHistoryResult2D(
                phase_name=phase_name,
                phase_identification=phase_identification,
            )
            # Request for each node
            for node in self.g_o.Nodes:
                single_phase_single_point_results = (
                    SinglePhaseSinglePointTimeHistoryResult2D(
                        phase_name=phase_name,
                        phase_identification=phase_identification,
                        point_name=node.Name.value,
                        point_type="node",
                        point_x=node.x.value,
                        point_y=node.y.value,
                        step=step_numbers_per_phase[phase_number],
                        time=time_numbers_per_phase[phase_number],
                    )
                )
                # Request for each result type
                for result_type_name, result_type in zip(
                    result_type_names, result_types
                ):
                    result = list(
                        self.g_o.getcurveresultspath(
                            node,
                            phase,
                            step_number_to_step[phase_end_step],
                            result_type,
                        )
                    )
                    # Add result to single point and phase result
                    single_phase_single_point_results.add_result(
                        SinglePointTimeHistoryResult2D(
                            result_type=result_type_name,
                            value=result,
                        )
                    )
                # Add point result
                single_phase_multi_point_results.add_point_result(
                    point_result=single_phase_single_point_results
                )
            # Add phase result
            multi_phase_multi_point_results.add_phase_result(
                phase_result=single_phase_multi_point_results
            )

        return multi_phase_multi_point_results

    @property
    def node_time_history_results(
        self,
    ) -> dict[str, list[SinglePhaseSinglePointTimeHistoryResult2D]]:
        """Returns the node time history results stored in the controller instance.

        Returns
        -------
        dict[str, list[PointTimeHistoryResult2D]]
            the node time history results stored in the controller instance, in the format {node_name: [results]}.
        """
        return self._node_time_history_results
