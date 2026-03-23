from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PrecalculationPoint2D:
    """Class representing a precalculation point in a 2D PLAXIS model."""

    x: float
    y: float
    point_type: Literal["node", "stresspoint"] = "node"
    name: str | None = None

    def __post_init__(self) -> None:
        # Validate point type
        if self.point_type not in ["node", "stresspoint"]:
            raise ValueError(
                f"Unexpected point type: {self.point_type}. Expected 'node' or 'stresspoint'."
            )
