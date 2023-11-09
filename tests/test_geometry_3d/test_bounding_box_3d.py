import pytest

from plxcontroller.geometry_3d.bounding_box_3d import BoundingBox3D
from plxcontroller.geometry_3d.point_3d import Point3D


def test_bounding_box_3d() -> None:
    """
    Tests the methods of the class BoudingBox3D.
    """

    # Assert invalid input (types)
    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min="invalid input", y_min=2.0, z_min=3.0, x_max=2.0, y_max=3.0, z_max=4.0
        )

    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min=1.0, y_min="invalid input", z_min=3.0, x_max=2.0, y_max=3.0, z_max=4.0
        )

    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min=1.0, y_min=2.0, z_min="invalid input", x_max=2.0, y_max=3.0, z_max=4.0
        )

    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min=1.0, y_min=2.0, z_min=3.0, x_max="invalid input", y_max=3.0, z_max=4.0
        )

    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min=1.0, y_min=2.0, z_min=3.0, x_max=2.0, y_max="invalid input", z_max=4.0
        )

    with pytest.raises(TypeError, match="Expected float"):
        BoundingBox3D(
            x_min=1.0, y_min=2.0, z_min=3.0, x_max=2.0, y_max=3.0, z_max="invalid input"
        )

    # Assert invalid input (values)
    with pytest.raises(ValueError, match="x_max must be > x_min"):
        BoundingBox3D(x_min=3.0, y_min=2.0, z_min=3.0, x_max=2.0, y_max=3.0, z_max=4.0)

    with pytest.raises(ValueError, match="y_max must be > y_min"):
        BoundingBox3D(x_min=1.0, y_min=4.0, z_min=3.0, x_max=2.0, y_max=3.0, z_max=4.0)

    with pytest.raises(ValueError, match="z_max must be > z_min"):
        BoundingBox3D(x_min=1.0, y_min=2.0, z_min=5.0, x_max=2.0, y_max=3.0, z_max=4.0)

    # Assert correct instance with valid input
    bbox = BoundingBox3D(
        x_min=1.0, y_min=2.0, z_min=3.0, x_max=2.0, y_max=3.0, z_max=4.0
    )
    assert bbox.x_min == 1.0
    assert bbox.y_min == 2.0
    assert bbox.z_min == 3.0
    assert bbox.x_max == 2.0
    assert bbox.y_max == 3.0
    assert bbox.z_max == 4.0
    # centroid
    assert bbox.centroid.x == 1.5
    assert bbox.centroid.y == 2.5
    assert bbox.centroid.z == 3.5
