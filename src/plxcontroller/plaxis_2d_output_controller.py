from __future__ import annotations

import os
import subprocess

from plxscripting.plxproxy import PlxProxyGlobalObject
from plxscripting.server import Server, new_server


class Plaxis2DOutputController:
    def __init__(self) -> None:
        """Creates a new Plaxis2DOutputController instance."""
        self._server: Server | None = None
        self._subprocess: subprocess.Popen | None = None
        self._filepath: str | None = None

    @property
    def s_o(self) -> Server | None:
        """Returns the server object. This is a typical alias for the server object."""
        return self._server

    @property
    def g_o(self) -> PlxProxyGlobalObject | None:
        """Returns the global project object. This is a typical alias for the global project object."""
        if isinstance(self._server, PlxProxyGlobalObject):
            return self._server.plx_global
        return None

    def connect(self, ip_address: str = "localhost", port: int = 10001) -> None:
        """Starts a new Plaxis instance and a new server connection with the given IP address and port and
        connect to it.

        Args:
            ip_address (str): the IP address of the Plaxis server. Defaults to "localhost".
            port (int, optional): the port to of the Plaxis server. Defaults to 10001.

        Returns:
            Plaxis2DOutputController: the Plaxis2DOutputController instance.
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
            plaxis_path = os.getenv("PLAXIS_2D_PROGRAM_PATH")
            if isinstance(plaxis_path, str):
                self._subprocess.stdin.write(f"taskkill /IM {plaxis_path}\n".encode())
            self._subprocess.terminate()

        self._server = None
        self._subprocess = None
        self._filepath = None
