from dataclasses import dataclass
from functools import cached_property

import pandas as pd

from plxcontroller.precalculation_point_2d import PrecalculationPoint2D


@dataclass(frozen=True)
class PointTimeHistoryResult2D:
    """Class representing a point time history result in a 2D PLAXIS model.
    for a single point, phase and result type."""

    point: PrecalculationPoint2D
    phase_name: str
    phase_identification: str
    step: list[int]
    time: list[float]
    value: list[float]
    result_type: str

    @cached_property
    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "point_name": self.point.name,
                "point_type": self.point.point_type,
                "phase_name": self.phase_name,
                "phase_identification": self.phase_identification,
                "point_x": self.point.x,
                "point_y": self.point.y,
                "step": self.step,
                "time": self.time,
                "value": self.value,
                "result_type": self.result_type,
            }
        )
