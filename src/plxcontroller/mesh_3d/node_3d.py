from __future__ import annotations

from plxcontroller.geometry_3d.point_3d import Point3D


class Node3D:
    """
    A class with information about a node in a 3D mesh.
    """

    def __init__(self, node_id: int, point: Point3D) -> None:
        """Initializes a Node3D instance.

        Parameters
        ----------
        node_id : int
            the id of the node in the mesh.
        point: Point3D
            the point where the node is located in the 3D space.

        Raises
        ------
        TypeError
            if any parameter is not of the expected type.
        """
        # Validate types
        if not isinstance(node_id, int):
            raise TypeError(
                f"Unexpected type found for node_id. Expected int, but got {type(node_id)}."
            )
        if not isinstance(point, Point3D):
            raise TypeError(
                f"Unexpected type found for point. Expected Point3D, but got {type(point)}."
            )

        self._node_id = node_id
        self._point = point

    @property
    def node_id(self) -> int:
        """Returns the id of the node in the mesh."""
        return self._node_id

    @property
    def point(self) -> Point3D:
        """Returns the point where the node is located in the 3D space."""
        return self._point
