import pytest

from plxcontroller.geometry_3d.polygon_3d import Polygon3D


def test_polygon_3d() -> None:
    """
    Tests the methods of the class Polygon3D.
    """

    # Assert invalid input
    with pytest.raises(TypeError, match="Expected list"):
        Polygon3D(coordinates="invalid input")

    with pytest.raises(TypeError, match="Expected tuple"):
        Polygon3D(coordinates=["invalid input"])

    with pytest.raises(ValueError, match="Expected tuple length = 3"):
        Polygon3D(coordinates=[(1.0, 2.0)])

    with pytest.raises(TypeError, match="Expected float"):
        Polygon3D(coordinates=[(1.0, 2.0, "invalid input")])

    with pytest.raises(ValueError, match="Expected length >= 3"):
        Polygon3D(coordinates=[(1.0, 2.0, 3.0), (2.0, 3.0, 4.0)])

    with pytest.raises(ValueError, match="coordinates are not coplanar"):
        Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)])

    # Assert instance is correctly created with valid input
    poly = Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)])

    assert poly.coordinates == [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)]

    for i, point in enumerate(poly.points):
        assert point.coordinates == poly.coordinates[i]

    for i, coord in enumerate(poly.scikit_spatial_points):
        assert tuple(coord) == poly.coordinates[i]
