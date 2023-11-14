from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
from scipy import spatial

from plxcontroller.geometry_3d.bounding_box_3d import BoundingBox3D
from plxcontroller.geometry_3d.point_3d import Point3D


class ConvexHull3D:
    """
    A class with information about a convex hull in the 3D space.
    """

    def __init__(self, points: Sequence[Point3D | Tuple[float, float, float]]):
        """Initializes a ConvexHull3D instance.

        Parameters
        ----------
        points : List[Point3D | Tuple[float, float, float]]
            a list of the points from which the convex hull will be created.

        Raises
        ------
        TypeError
            if points of its (sub)items are not of the expected type.
        ValueError
            - if length of points is not >= 4.
            - if item of points is tuple but its length of any tuple is not exactly 3.
            - if a convex hull cannot be computed from the given points.
        """
        # Validate input
        # points
        if not isinstance(points, list):
            raise TypeError(
                f"Unexpected type for points. Expected list, but got: {type(points)}"
            )
        # point items and subtimes
        for i, point in enumerate(points):
            if not isinstance(point, (Point3D, tuple)):
                raise TypeError(
                    f"Unexpected type for item of points at index {i}. Expected Point3D or tuple, but got: {type(point)}"
                )
            if isinstance(point, tuple):
                if not len(point) == 3:
                    raise ValueError(
                        f"Unexpected tuple length for item of points at index {i}. Expected tuple length = 3, but got: {len(point)}"
                    )
                if not all(isinstance(a, (float, int)) for a in point):
                    raise TypeError(
                        f"Unexpected type for tuple items of point at index {i}. Expected float, but got: {tuple(isinstance(a, float) for a in point)}"
                    )

        # Validate length of list
        if not len(points) >= 4:
            raise ValueError(
                f"Unexpected length of points. Expected length >= 4, but got: {len(points)}"
            )

        # Cast tuples to points
        casted_points: List[Point3D] = []
        for point in points:
            if isinstance(point, Point3D):
                casted_points.append(point)
            else:
                casted_points.append(Point3D(x=point[0], y=point[1], z=point[2]))

        # Compute the convex hull of all the points
        try:
            convex_hull = spatial.ConvexHull(
                points=np.vstack([point.coordinates for point in casted_points])
            )
        except spatial.QhullError as e:
            raise ValueError(
                "Cannot create ConvexHull3D from given points, the followin error "
                + f"was raised when computing the convex hull: {e}"
            )

        # Store the points and the indices of a
        self._points = casted_points
        self._vertex_indices = list(convex_hull.vertices)

    @property
    def points(self) -> List[Point3D]:
        """Returns all the points of the convex hull."""
        return self._points

    @property
    def vertex_indices(self) -> List[int]:
        """Returns the indices of the vertices of the convex hull."""
        return self._vertex_indices

    @property
    def vertices(self) -> List[Point3D]:
        """Returns the vertices of the convex hull as points."""
        return [self._points[i] for i in self._vertex_indices]

    @property
    def bounding_box(self) -> BoundingBox3D:
        """Returns the bounding box of the convex hull."""
        return BoundingBox3D(
            x_min=min([vertex.x for vertex in self.vertices]),
            y_min=min([vertex.y for vertex in self.vertices]),
            z_min=min([vertex.z for vertex in self.vertices]),
            x_max=max([vertex.x for vertex in self.vertices]),
            y_max=max([vertex.y for vertex in self.vertices]),
            z_max=max([vertex.z for vertex in self.vertices]),
        )
