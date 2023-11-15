from __future__ import annotations

from plxscripting.plxproxy import PlxProxyGlobalObject
from plxscripting.server import Server


class Plaxis3DOutputController:
    def __init__(self, server: Server):
        """Creates a new Plaxis3DOutputController instance based on a server connection with the Plaxis program.

        Args:
            server (Server): the server connection with the Plaxis program.
        """
        self.server = server

    @property
    def s_o(self) -> Server:
        """Returns the server object. This is a typical alias for the server object."""
        return self.server

    @property
    def g_o(self) -> PlxProxyGlobalObject:
        """Returns the global project object. This is a typical alias for the global project object."""
        return self.server.plx_global
