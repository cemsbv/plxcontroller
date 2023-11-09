import pytest

from plxcontroller.geometry_3d.point_3d import Point3D


def test_point_3d() -> None:
    """
    Tests the methods of the class Point3D.
    """

    # Assert invalid input
    with pytest.raises(TypeError, match="Expected float"):
        Point3D(x="invalid input", y=2.0, z=3.0)

    with pytest.raises(TypeError, match="Expected float"):
        Point3D(x=1.0, y="invalid input", z=3.0)

    with pytest.raises(TypeError, match="Expected float"):
        Point3D(x=1.0, y=2.0, z="invalid input")

    # Assert instance is correct with valid input
    point = Point3D(x=1.0, y=2.0, z=3.0)
    assert point.x == 1.0
    assert point.y == 2.0
    assert point.z == 3.0
