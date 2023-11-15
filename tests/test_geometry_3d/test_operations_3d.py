import pytest

from plxcontroller.geometry_3d.operations_3d import (
    project_vertically_point_onto_polygon_3d,
)
from plxcontroller.geometry_3d.point_3d import Point3D
from plxcontroller.geometry_3d.polygon_3d import Polygon3D


def test_project_vertically_point_onto_polygon_3d() -> None:
    """
    Tests the method project_vertically_point_onto_polygon_3d.
    """

    # Assert invalid input (types)
    with pytest.raises(TypeError, match="Expected Point3D"):
        project_vertically_point_onto_polygon_3d(
            point="invalid input",
            polygon=Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
        )

    with pytest.raises(TypeError, match="Expected Polygon3D"):
        project_vertically_point_onto_polygon_3d(
            point=Point3D(x=0.5, y=0.5, z=5.0),
            polygon="invalid input",
        )

    # Assert it returns None if projection falls out the boundaries of the polygon
    assert (
        project_vertically_point_onto_polygon_3d(
            point=Point3D(x=-0.5, y=-0.5, z=5.0),
            polygon=Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
        )
        is None
    )

    # Assert it returns the expected point (polygon3d parallel to xy plane)
    assert project_vertically_point_onto_polygon_3d(
        point=Point3D(x=0.5, y=0.5, z=5.0),
        polygon=Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
    ).coordinates == (0.5, 0.5, 0)

    # Assert it returns the expected point (inclined polygon3d)
    assert project_vertically_point_onto_polygon_3d(
        point=Point3D(x=0.5, y=0.5, z=5.0),
        polygon=Polygon3D(coordinates=[(0, 0, 0), (1, 0, 1), (1, 1, 1), (0, 1, 0)]),
    ).coordinates == (0.5, 0.5, 0.5)

    # Assert it returns the expected point when enough tolerance is provided.
    assert project_vertically_point_onto_polygon_3d(
        point=Point3D(x=-0.5, y=-0.5, z=5.0),
        polygon=Polygon3D(coordinates=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]),
        tol=0.8,
    ).coordinates == (-0.5, -0.5, 0)
