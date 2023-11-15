import pytest

from plxcontroller.geometry_3d.point_3d import Point3D
from plxcontroller.mesh_3d.node_3d import Node3D


def test_mesh_3d() -> None:
    """
    Tests the methods of the class Mesh3D.
    """

    # Assert invalid input
    with pytest.raises(TypeError, match="Expected int"):
        Node3D(node_id="invalid input", point=Point3D(x=1.0, y=2.0, z=3.0))

    with pytest.raises(TypeError, match="Expected Point3D"):
        Node3D(node_id=1, point="invalid input")

    # Assert instance is correct with valid input
    node = Node3D(node_id=1, point=Point3D(x=1.0, y=2.0, z=3.0))
    assert node.node_id == 1
    assert node.point.coordinates == (1.0, 2.0, 3.0)
