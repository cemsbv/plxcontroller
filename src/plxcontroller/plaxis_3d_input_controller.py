from __future__ import annotations

from typing import Dict, List

from plxscripting.easy import new_server
from plxscripting.plxproxy import PlxProxyGlobalObject, PlxProxyObject
from plxscripting.server import Server

from plxcontroller.geometry_3d.bounding_box_3d import BoundingBox3D
from plxcontroller.geometry_3d.convex_hull_3d import ConvexHull3D
from plxcontroller.geometry_3d.operations_3d import (
    project_vertically_point_onto_polygon_3d,
)
from plxcontroller.geometry_3d.point_3d import Point3D
from plxcontroller.geometry_3d.polygon_3d import Polygon3D
from plxcontroller.globals import ABS_TOL
from plxcontroller.plaxis_3d_output_controller import Plaxis3DOutputController


class Plaxis3DInputController:
    def __init__(self, server: Server):
        """Creates a new PlaxisInputController instance based on a server connection with the Plaxis program.

        Args:
            server (Server): the server connection with the Plaxis program.
        """
        self.server = server
        self._plaxis_volumes_bounding_boxes: Dict[PlxProxyObject, BoundingBox3D] = {}
        self._convex_hull_per_cut_volume: Dict[PlxProxyObject, ConvexHull3D] = {}

    @property
    def s_i(self) -> Server:
        """Returns the server object. This is a typical alias for the server object."""
        return self.server

    @property
    def g_i(self) -> PlxProxyGlobalObject:
        """Returns the global project object. This is a typical alias for the global project object."""
        return self.server.plx_global

    @property
    def plaxis_volumes_bounding_boxes(self) -> Dict[PlxProxyObject, BoundingBox3D]:
        """Returns the mapping between the plaxis volumes and their corresponding bounding boxes."""
        return self._plaxis_volumes_bounding_boxes

    @property
    def convex_hull_per_cut_volume(self) -> Dict[PlxProxyObject, ConvexHull3D]:
        """Returns the convex hull per cut volume object."""
        return self._convex_hull_per_cut_volume

    def go_to_mode(self, mode_number: int) -> None:
        """Go to the plaxis mode specified by mode_number.

        Available options are:

            Mode                    mode_number
            ----------------        -----------
            Soil                        0
            Structures                  1
            Mesh                        2
            Flow Conditions             3
            Staged Construction         4

        Parameters
        ----------
        mode_number : int
            the mode number to go to.

        Raises
        ------
            TypeError
                if mode_number is not of type int.
            ValueError
                if mode_number is not 0 <= mode_number <= 4.
        """

        # Validate input
        if not isinstance(mode_number, int):
            raise TypeError(
                f"Unexpected typ for mode_number. Expected int, but got {type(mode_number)}."
            )
        if not 0 <= mode_number <= 4:
            raise ValueError("mode_number is not not 0 <= mode_number <= 4.")

        mode_functions = [
            self.g_i.gotosoil,
            self.g_i.gotostructures,
            self.g_i.gotomesh,
            self.g_i.gotoflow,
            self.g_i.gotostages,
        ]

        mode_functions[mode_number]()

    def filter_cut_volumes_above_polygons(
        self,
        polygons: List[Polygon3D],
        cut_volumes: List[PlxProxyObject] | None = None,
        tol: float | None = None,
    ) -> List[PlxProxyObject]:
        """Filters the given cut volumes if all its vertices are located above any polygon
        in the given list of polygons.

        Note that if any vertex of the cut volume falls outside the projection
        of a polygon in the xy plane, then the cut volume is not considered to be above
        the polygon.

        A cut volume is defined as any Volume or SoilVolume in Mesh, FlowConditions
        and StagedConstruction tabs of the plaxis model.

        Parameters
        ----------
        polygons : List[Polygon3D]
            the list of polygons.
        cut_volumes : List[PlxProxyObject] | None, optional
            the list of plaxis volumes to filter from.
            If None is given then all the cut volumes in the model are used.
            Defaults to None.
        tol: float | None, optional
            the allowed tolerance to compared the coordinates of the cut_volumes
            and the polygons.
            If None given, then the globals.ABS_TOL will be used.
            Defaults to None.

        Returns
        -------
        List[PlxProxyObject]
            the filtered cut volumes.

        Raises
        ------
        TypeError
            if parameters are not of the expected type.
        ValueError
            - if this method is not called in modes Mesh, FlowConditions and StagedConstruction.
            - if any item of cut_volumes is not present in the Volumes nor SoilVolumes of the plaxis model.
            - if tol is not >= 0.
        """

        # Method should be only called in Mesh, FlowConditions and StagedConstruction.
        if not 2 <= self.g_i.Project.Mode.value <= 4:
            raise ValueError(
                "Method filter_cut_volumes_above_polygons can only be called in Mesh, "
                + "FlowConditions and StagedConstruction."
            )

        # Validate input
        if not isinstance(polygons, list):
            raise TypeError(
                f"Unexpected type for polygons. Expected list, but got {type(polygons)}."
            )
        for i, polygon in enumerate(polygons):
            if not isinstance(polygon, Polygon3D):
                raise TypeError(
                    f"Unexpected type for item {i} of polygons. Expected Polygon3D, but got {type(polygon)}."
                )

        if cut_volumes is not None:
            if not isinstance(cut_volumes, list):
                raise TypeError(
                    f"Unexpected type for cut_volumes. Expected list, but got {type(cut_volumes)}."
                )
            for i, cut_volume in enumerate(cut_volumes):
                if not isinstance(cut_volume, PlxProxyObject):
                    raise TypeError(
                        f"Unexpected type for item {i} of cut_volumes. Expected PlxProxyObject, but got {type(cut_volume)}."
                    )
                if cut_volume not in list(
                    set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes))
                ):
                    raise ValueError(
                        f"Item {i} of cut_volumes is not present in the volumes of the plaxis model."
                    )

        if tol is not None:
            if not isinstance(tol, (float, int)):
                raise TypeError(
                    f"Unexpected type for tol. Expected float, but got {type(tol)}."
                )
            if not tol >= 0:
                raise ValueError(f"tol must be >= 0, but got {tol}.")

        # Initialize plaxis_volume list as all the volumes in the Plaxis model.
        if cut_volumes is None:
            cut_volumes = list(set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes)))

        # Initialize tol
        if tol is None:
            tol = ABS_TOL

        # Map convex hulls per cut volume (if any cut volume is not present in self.convex_hull_per_cut_volume)
        if any(a not in self.convex_hull_per_cut_volume for a in cut_volumes):
            self.map_convex_hull_per_cut_volume()

        # Filter the volumes if it is above any of the polygons
        filtered_cut_volumes = []
        for cut_volume in cut_volumes:
            # Get the convex hull corresponding to the cut volume
            convex_hull = self.convex_hull_per_cut_volume[cut_volume]

            # Check that all vertices of the convex hull are above
            # any of the polygon. If this is the case add it to the
            # filtered_cut_volumes list.
            for polygon in polygons:
                checks = []
                for vertex in convex_hull.vertices:
                    projected_point = project_vertically_point_onto_polygon_3d(
                        point=vertex, polygon=polygon, tol=tol
                    )
                    checks.append(
                        isinstance(projected_point, Point3D)
                        and vertex.z + tol >= projected_point.z
                    )
                    if checks[-1] is False:
                        break
                if all(checks):
                    filtered_cut_volumes.append(cut_volume)
                    break

        return filtered_cut_volumes

    def map_convex_hull_per_cut_volume(self) -> None:
        """Maps the convex hull for each cut volume of the Plaxis model
        and stores it in the dictionary `self.convex_hull_per_cut_volume`.

        A cut volume is defined as any Volume or SoilVolume in Mesh, FlowConditions
        and StagedConstruction tabs.

        Note that the convex hulls are mapped based on the mesh nodes of the model,
        which means:
            - This method requires that the mesh is already generated, otherwise
            an error is raised.
            - The mesh must be up-to-date with the input geometry to get
            correct results (but this is not checked by this method).
            - The Plaxis output program is opened (but closing should be done manually).

        Raises
        ------
            ValueError: if the mesh is not yet generated for the Plaxis model.
        """
        # Get initial mode to return later in this method.
        initial_mode = self.g_i.Project.Mode.value

        # Initialize a Plaxis3DOutput controller to get the information
        # about nodes per cut volume
        if initial_mode != 2:
            self.g_i.gotomesh()
        try:
            port = self.g_i.viewmesh()
        except Exception as e:
            raise ValueError(
                "Cannot map the convex hull per cut volume, the following error occurred "
                + f"when requesting to view the mesh: {e}"
            )

        server, _ = new_server(
            self.server.connection.host, port, password=self.server.connection._password
        )
        co = Plaxis3DOutputController(server)

        # Get nodes per cut volume
        nodes_per_cut_volume = co.get_nodes_per_cut_volume()
        # Close the output project (Plaxis 3D program keeps open)
        co.s_o.close()

        # Return to the initial mode
        if initial_mode != 2:
            self.go_to_mode(initial_mode)

        # Get convex hull per cut volume
        self._convex_hull_per_cut_volume = {}
        for cut_volume in list(
            set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes))
        ):
            self._convex_hull_per_cut_volume[cut_volume] = ConvexHull3D(
                points=nodes_per_cut_volume[cut_volume.Name.value]
            )
