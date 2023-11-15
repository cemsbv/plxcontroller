import pytest

from plxcontroller.geometry_3d.convex_hull_3d import ConvexHull3D
from plxcontroller.geometry_3d.point_3d import Point3D


def test_convex_hull_3d() -> None:
    """
    Tests the methods of the class ConvexHull3D.
    """

    # Assert invalid input
    with pytest.raises(TypeError, match="Expected list"):
        ConvexHull3D(points="invalid input")

    with pytest.raises(TypeError, match="Expected Point3D or tuple"):
        ConvexHull3D(points=["invalid input"])

    with pytest.raises(ValueError, match="Expected tuple length = 3"):
        ConvexHull3D(points=[(1.0, 2.0)])

    with pytest.raises(TypeError, match="Expected float"):
        ConvexHull3D(points=[(1.0, 2.0, "invalid input")])

    with pytest.raises(ValueError, match="Expected length >= 4"):
        ConvexHull3D(points=[])

    with pytest.raises(
        ValueError, match="Cannot create ConvexHull3D from given points"
    ):
        ConvexHull3D(
            points=[
                Point3D(-5.0, -5.0, -5.0),
                Point3D(5.0, -5.0, -5.0),
                Point3D(5.0, 5.0, -5.0),
                Point3D(-5.0, 5.0, -5.0),
            ]
        )

    # Assert instance is correctly created with valid input
    points = [
        Point3D(-5.0, -5.0, -5.0),
        Point3D(5.0, -5.0, -5.0),
        Point3D(5.0, 5.0, -5.0),
        Point3D(-5.0, 5.0, -5.0),
        Point3D(-5.0, -5.0, 5.0),
        Point3D(5.0, -5.0, 5.0),
        Point3D(5.0, 5.0, 5.0),
        Point3D(-5.0, 5.0, 5.0),
        Point3D(0.0, 0.0, 0.0),
    ]

    convex_hull = ConvexHull3D(points=points)

    assert convex_hull.points == points
    assert convex_hull.vertex_indices == list(range(0, 8))
    assert convex_hull.vertices == points[:-1]
