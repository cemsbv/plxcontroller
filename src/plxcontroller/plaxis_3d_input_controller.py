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

    def filter_volumes_above_polygons(
        self,
        polygons: List[Polygon3D],
        plaxis_volumes: List[PlxProxyObject] | None = None,
    ) -> List[PlxProxyObject]:
        """Filters the given plaxis volumes if its centroid is located above any polygon
        in the given list of polygons.

        Note that if the centroid of the plaxis volume falls outside the projection
        of a polygon is not considered to be above the polygon.

        Parameters
        ----------
        polygons : List[Polygon3D]
            the list of polygons.
        plaxis_volumes : List[PlxProxyObject] | None, optional
            the list of plaxis volumes to filter from.
            If None is given then all the plaxis volumes in the model are used.
            Defaults to None.

        Returns
        -------
        List[PlxProxyObject]
            the filtered plaxis volumes.

        Raises
        ------
        TypeError
            if parameters are not of the expected type.
        ValueError
            if any item of plaxis_volumes is not present in the Volumes nor SoilVolumes of the plaxis model.
        """

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

        if plaxis_volumes is not None:
            if not isinstance(plaxis_volumes, list):
                raise TypeError(
                    f"Unexpected type for plaxis_volumes. Expected list, but got {type(plaxis_volumes)}."
                )
            for i, plaxis_volume in enumerate(plaxis_volumes):
                if not isinstance(plaxis_volume, PlxProxyObject):
                    raise TypeError(
                        f"Unexpected type for item {i} of plaxis_volumes. Expected PlxProxyObject, but got {type(plaxis_volume)}."
                    )
                if plaxis_volume not in list(
                    set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes))
                ):
                    raise ValueError(
                        f"Item {i} of plaxis_volumes is not present in the volumes of the plaxis model."
                    )

        # Initialize plaxis_volume list as all the volumes in the Plaxis model.
        if plaxis_volumes is None:
            plaxis_volumes = list(
                set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes))
            )

        # Map plaxis volumes to bounding boxes
        for plaxis_volume in plaxis_volumes:
            if plaxis_volume not in self.plaxis_volumes_bounding_boxes.keys():
                self._plaxis_volumes_bounding_boxes[plaxis_volume] = BoundingBox3D(
                    x_min=plaxis_volume.BoundingBox.xMin.value,
                    y_min=plaxis_volume.BoundingBox.yMin.value,
                    z_min=plaxis_volume.BoundingBox.zMin.value,
                    x_max=plaxis_volume.BoundingBox.xMax.value,
                    y_max=plaxis_volume.BoundingBox.yMax.value,
                    z_max=plaxis_volume.BoundingBox.zMax.value,
                )

        # Filter the volumes if it is above any of the polygons
        filtered_plaxis_volumes = []
        for plaxis_volume in plaxis_volumes:
            bbox = self.plaxis_volumes_bounding_boxes[plaxis_volume]
            for polygon in polygons:
                projected_point = project_vertically_point_onto_polygon_3d(
                    point=bbox.centroid, polygon=polygon
                )
                if (
                    isinstance(projected_point, Point3D)
                    and bbox.centroid.z >= projected_point.z
                ):
                    filtered_plaxis_volumes.append(plaxis_volume)
                    break

        return filtered_plaxis_volumes

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

        The user should take care that the generated mesh is up-to-date with
        the inputs, otherwise
        This method assumes that the generated mesh is up-to-date with the
        geometry model in structures.


        Raises
        ------
            ValueError: if the mesh is not yet generated for the Plaxis model.
        """
        # Initialize a Plaxis3DOutput controller to get the information
        # about nodes per cut volume
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

        # Get convex hull per cut volume
        self.g_i.gotostages()
        self._convex_hull_per_cut_volume = {}
        for cut_volume in list(
            set(list(self.g_i.SoilVolumes) + list(self.g_i.Volumes))
        ):
            self._convex_hull_per_cut_volume[cut_volume] = ConvexHull3D(
                points=nodes_per_cut_volume[cut_volume.Name.value]
            )
