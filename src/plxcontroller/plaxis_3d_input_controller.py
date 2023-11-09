from __future__ import annotations

from typing import Any

from plxscripting.server import Server


class Plaxis3DInputController:
    def __init__(self, server: Server):
        """Creates a new PlaxisInputController instance based on a server connection with the Plaxis program.

        Args:
            server (Server): the server connection with the Plaxis program.
        """
        self.server = server

    @property
    def s_i(self) -> Server:
        """Returns the server object. This is a typical alias for the server object."""
        return self.server

    @property
    def g_i(self) -> Any:
        """Returns the global project object. This is a typical alias for the global project object."""
        return self.server.plx_global
