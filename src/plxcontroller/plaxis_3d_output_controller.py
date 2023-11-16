from __future__ import annotations

from typing import Dict, List

from plxscripting.plxproxy import PlxProxyGlobalObject
from plxscripting.server import Server

from plxcontroller.geometry_3d.point_3d import Point3D


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

    def get_nodes_per_cut_volume(self) -> Dict[str, List[Point3D]]:
        """Get all the nodes per cut volume as points.

        Note that cut volumes are the volumes produced by the intersection
        of geometry in Plaxis (this takes place when the tab Mesh is clicked).

        Returns
        -------
        Dict[str, List[Point3D]]
            the dictionary with all the nodes per cut volume in the following
            format {cut_volume_name: points}
        """
        # Map all nodes per soil volume
        nodes_per_cut_volume = {}
        for volume in list(set(list(self.g_o.SoilVolumes) + list(self.g_o.Volumes))):
            # Volumes deepest level (cutted in Mesh, present also in Stages)
            for cut_volume in volume:
                # Request x, y and z values
                plaxis_xs = self.g_o.getresults(
                    cut_volume, self.g_o.ResultTypes.Soil.X, "node", False
                )
                plaxis_ys = self.g_o.getresults(
                    cut_volume, self.g_o.ResultTypes.Soil.Y, "node", False
                )
                plaxis_zs = self.g_o.getresults(
                    cut_volume, self.g_o.ResultTypes.Soil.Z, "node", False
                )
                # Map PlxValues to List[float] (this is time consuming)
                xs = list(map(float, plaxis_xs))
                ys = list(map(float, plaxis_ys))
                zs = list(map(float, plaxis_zs))
                # Make a set of the coordinates
                coordinates_set = set()
                for x, y, z in zip(xs, ys, zs):
                    coordinates_set.add((x, y, z))
                # Store the coordinates as points
                nodes_per_cut_volume[cut_volume.Name.value] = [
                    Point3D(x=c[0], y=c[1], z=c[2]) for c in list(coordinates_set)
                ]

        return nodes_per_cut_volume
