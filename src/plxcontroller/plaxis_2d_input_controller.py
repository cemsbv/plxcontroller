from __future__ import annotations

import os
import subprocess

from plxscripting.plxproxy import PlxProxyGlobalObject
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
        print("--------------------------")
        print("Node and stresspoint selection")
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
                        f"Requested node: (x={point.x:.3f}, y={point.y:.3f} -> Selected node: (x={plaxis_node.x.value:.3f}, y={plaxis_node.y.value:.3f})"
                    )
                    if isinstance(point.name, str):
                        plaxis_node.Identification = point.name
                        co.g_o.rename(plaxis_node, point.name)
                else:
                    plaxis_stress_point = co.g_o.addcurvepoint(
                        "stresspoint", point.x, point.y
                    )
                    print(
                        f"Requested stress point: (x={point.x:.3f}, y={point.y:.3f} -> "
                        + f"Selected stress point: (x={plaxis_stress_point.x.value:.3f}, y={plaxis_stress_point.y.value:.3f})"
                    )
                    if isinstance(point.name, str):
                        plaxis_stress_point.Identification = point.name
                        co.g_o.rename(plaxis_stress_point, point.name)

        # Update and save
        co.g_o.update()

        print("Selected points sucessfully!!")

        return
