from __future__ import annotations

import os
import shutil
import subprocess

from plxscripting.plxproxy import PlxProxyGlobalObject, PlxProxyObject
from plxscripting.server import Server, new_server

from plxcontroller.plaxis_2d_output_controller import Plaxis2DOutputController
from plxcontroller.precalculation_point_2d import PrecalculationPoint2D


class Plaxis2DInputController:
    def __init__(self) -> None:
        """Creates a new Plaxis2DInputController instance."""
        self._server: Server | None = None
        self._subprocess: subprocess.Popen | None = None
        self._filepath: str | None = None

    @property
    def s_i(self) -> Server | None:
        """Returns the server object. This is a typical alias for the server object."""
        return self._server

    @property
    def g_i(self) -> PlxProxyGlobalObject:
        """Returns the global project object. This is a typical alias for the global project object."""
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")
        return self._server.plx_global

    def connect(self, ip_address: str = "localhost", port: int = 10000) -> None:
        """Starts a new Plaxis instance and a new server connection with the given IP address and port and
        connect to it.

        Args:
            ip_address (str): the IP address of the Plaxis server. Defaults to "localhost".
            port (int, optional): the port to of the Plaxis server. Defaults to 10000.
        """

        plaxis_path = os.getenv("PLAXIS_2D_INPUT_PROGRAM")
        if not plaxis_path:
            raise ValueError(
                'Environmental variable "PLAXIS_2D_INPUT_PROGRAM" is not set.'
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
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")

        self._server.open(filepath)
        self._filepath = filepath

    def close(self) -> None:
        """Close the PLAXIS model file."""
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")

        self._server.close()
        self._filepath = None

    # TODO: deprecate this function
    def disconnect(self) -> None:
        """Disconnect from the PLAXIS server."""

        if self._subprocess is not None and self._subprocess.stdin is not None:
            plaxis_path = os.getenv("PLAXIS_2D_INPUT_PROGRAM")
            if isinstance(plaxis_path, str):
                self._subprocess.stdin.write(f"taskkill /IM {plaxis_path}\n".encode())
            self._subprocess.terminate()

        self._server = None
        self._subprocess = None
        self._filepath = None

    def kill(self) -> None:
        """Kill the PLAXIS process and disconnect from the server."""
        if self._subprocess is not None:
            self._subprocess.kill()
        self._server = None
        self._subprocess = None
        self._filepath = None

    def copy_current_model(self, new_filepath: str) -> None:
        """Copy the current PLAXIS model file to a new location.

        Args:
            new_filepath (str): the path to the new PLAXIS model file.
        """
        if self._filepath is None:
            raise ValueError("No PLAXIS model file is currently open.")

        shutil.copyfile(self._filepath, new_filepath)
        shutil.copytree(
            self._filepath.replace(".p2dx", ".p2dxdat"),
            new_filepath.replace(".p2dx", ".p2dxdat"),
        )

    def select_precalculation_points(
        self,
        points: list[PrecalculationPoint2D],
        delete_previously_selected: bool = True,
    ) -> None:
        """Select precalculation points in the PLAXIS model.

        Parameters
        ----------
            points: list[PrecalculationPoint2D]
                The precalculation points to select.
                The nodes to select as precalculation points.
            delete_previously_selected: bool, optional
                Whether to delete previously selected points.
                Defaults to True.
        """
        if not isinstance(self._server, Server):
            raise ValueError("No server connection available.")

        # Validate precalculation points
        for point in points:
            if not isinstance(point, PrecalculationPoint2D):
                raise ValueError(
                    f"Unexpected point type: {type(point)}. Expected PrecalculationPoint2D."
                )

        # Go to mesh and start PLAXIS output program
        self.g_i.gotomesh()
        output_server_port = self.g_i.selectmeshpoints()

        co = Plaxis2DOutputController()
        co.connect(
            ip_address=self._server.connection.host,
            port=output_server_port,
        )

        # Clear previously selected points (if applicable)
        if delete_previously_selected:
            co.g_o.clearcurvepoints()

        # Add new points to the selection
        if len(points) > 0:
            for point in points:
                if point.point_type == "node":
                    plaxis_node = co.g_o.addcurvepoint("node", point.x, point.y)
                    print(
                        f"Requested node: (x={point.x:.3f}, y={point.y:.3f}) -> Selected node: (x={plaxis_node.x.value:.3f}, y={plaxis_node.y.value:.3f})"
                    )
                    if isinstance(point.identification, str):
                        plaxis_node.Identification = point.identification
                else:
                    plaxis_stress_point = co.g_o.addcurvepoint(
                        "stresspoint", point.x, point.y
                    )
                    print(
                        f"Requested stress point: (x={point.x:.3f}, y={point.y:.3f} -> "
                        + f"Selected stress point: (x={plaxis_stress_point.x.value:.3f}, y={plaxis_stress_point.y.value:.3f})"
                    )
                    if isinstance(point.identification, str):
                        plaxis_stress_point.Identification = point.identification

        # Update and save
        co.g_o.update()
        co.kill()

        print("Selected points sucessfully!!")

        return

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
            phase = getattr(self.g_i, f"Phase_{phase_number}")
        except AttributeError:
            raise ValueError(
                f"Unexpected phase number: {phase_number}. No such phase in PLAXIS model."
            )
        return phase

    def recalculate_all_phases(self) -> None:
        """Recalculate all phases in the PLAXIS model."""
        self.g_i.gotostages()
        for phase in self.g_i.Phases:
            phase.ShouldCalculate = True
        self.g_i.calculate()
        self.g_i.save()

    def get_all_materials_by_identification(self) -> dict[str, PlxProxyObject]:
        """Get a material object by its identification.

        Returns
        -------
        dict[str, PlxProxyObject]
            A dictionary where keys are material identifications and values are the corresponding material objects.
        """
        materials_dict = {}
        for material in self.g_i.Materials:
            material_identification = material.Identification.value
            if material_identification in materials_dict:
                raise ValueError(
                    f"Duplicate material identification found: '{material_identification}'. Material identifications must be unique."
                )
            materials_dict[material_identification] = material
        return materials_dict

    def get_material_parameter_value(
        self, material: PlxProxyObject, parameter_name: str
    ) -> float:
        """Returns the value of a specific material parameter.

        Parameters
        ----------
        material : PlxProxyObject
            The material object.
        parameter_name : str
            The name of the parameter.

        Returns
        -------
        float
            The value of the specified material parameter.
        """
        try:
            parameter_value = getattr(material, parameter_name).value
        except AttributeError:
            raise ValueError(
                f"Unexpected parameter name: {parameter_name}. No such parameter in material {material.Identification.value}."
            )
        return parameter_value

    def set_material_parameter_value(
        self, material: PlxProxyObject, parameter_name: str, value: float
    ) -> None:
        """Sets the value of a specific material parameter.

        Parameters
        ----------
        material : PlxProxyObject
            The material object.
        parameter_name : str
            The name of the parameter.
        value : float
            The new value of the specified material parameter.
        """
        try:
            parameter = getattr(material, parameter_name)
        except AttributeError:
            raise ValueError(
                f"Unexpected parameter name: {parameter_name}. No such parameter in material {material.Identification.value}."
            )

        try:
            self.g_i.set(parameter, value)
        except Exception as e:
            raise ValueError(
                f"Failed to set parameter '{parameter_name}' for material '{material.Identification.value}': {e}"
            )
