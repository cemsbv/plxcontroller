from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from plxscripting.plxproxy import PlxProxyObject


@dataclass(frozen=True)
class PrecalculationPoint2D:
    """Class representing a precalculation point in a 2D PLAXIS model."""

    x: float
    y: float
    point_type: Literal["node", "stresspoint"] = "node"
    identification: str | None = None

    def __post_init__(self) -> None:
        # Validate point type
        if self.point_type not in ["node", "stresspoint"]:
            raise ValueError(
                f"Unexpected point type: {self.point_type}. Expected 'node' or 'stresspoint'."
            )

    @classmethod
    def from_plaxis_node(cls, plaxis_node: PlxProxyObject) -> PrecalculationPoint2D:
        """Create a PrecalculationPoint2D instance from a PLAXIS node object."""
        return cls(
            x=plaxis_node.x.value,
            y=plaxis_node.y.value,
            point_type="node",
            identification=plaxis_node.Identification.value,
        )
