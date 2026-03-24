from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class SinglePointTimeHistoryResult2D:
    """Class representing a point time history result in a 2D PLAXIS model for a single point, phase and result type."""

    result_type: str
    value: list[float]


@dataclass
class SinglePhaseSinglePointTimeHistoryResult2D:
    """Class representing a point time history result in a 2D PLAXIS model.
    for a single point, phase and result type."""

    phase_name: str
    phase_identification: str
    point_name: str
    point_type: str
    point_x: float
    point_y: float
    step: list[int]
    time: list[float]
    results: list[SinglePointTimeHistoryResult2D] = field(default_factory=list)

    def add_result(self, result: SinglePointTimeHistoryResult2D) -> None:
        """Add a result."""
        # Check if the result already exists for the same result type
        for existing_result in self.results:
            if existing_result.result_type == result.result_type:
                raise ValueError(
                    f"Result with type '{result.result_type}' already exists for point '{self.point_name}' and phase '{self.phase_name}'."
                )
        self.results.append(result)


@dataclass
class SinglePhaseMultiPointTimeHistoryResult2D:
    """Class representing a point time history result in a 2D PLAXIS model for a single point and result type, but multiple phases."""

    phase_name: str
    phase_identification: str
    point_results: list[SinglePhaseSinglePointTimeHistoryResult2D] = field(default_factory=list)

    def add_point_result(
        self, point_result: SinglePhaseSinglePointTimeHistoryResult2D
    ) -> None:
        """Add a point result."""
        # Check if the phase result already exists for the same phase name
        for existing_phase_result in self.point_results:
            if existing_phase_result.phase_name == point_result.phase_name:
                raise ValueError(
                    f"Phase result with name '{point_result.phase_name}' already exists for point '{point_result.point_name}'."
                )
        self.point_results.append(point_result)

    def get_point_result(
        self, point_name: str
    ) -> SinglePhaseSinglePointTimeHistoryResult2D:
        """Get a point result by point name."""
        for point_result in self.point_results:
            if point_result.point_name == point_name:
                return point_result
        raise ValueError(
            f"Point result with name '{point_name}' not found for phase '{self.phase_name}'."
        )


@dataclass
class MultiPhaseMultiPointTimeHistoryResult2D:
    """Class representing a point time history result in a 2D PLAXIS model for multiple points, phases and result types."""

    phases_results: list[SinglePhaseMultiPointTimeHistoryResult2D] = field(default_factory=list)

    @property
    def point_names(self) -> list[str]:
        """Get the unique point names from the multi-phase result."""
        point_names = set()
        for phase_result in self.phases_results:
            for point_result in phase_result.point_results:
                point_names.add(point_result.point_name)
        return list(point_names)

    def add_phase_result(
        self, phase_result: SinglePhaseMultiPointTimeHistoryResult2D
    ) -> None:
        """Add a phase result to the multi-phase result."""
        # Check if the phase result already exists for the same phase name
        for existing_phase_result in self.phases_results:
            if existing_phase_result.phase_name == phase_result.phase_name:
                raise ValueError(
                    f"Phase result with name '{phase_result.phase_name}' already exists."
                )
        self.phases_results.append(phase_result)

    def to_dataframe(self) -> pd.DataFrame:
        # Generate records
        records = []
        for point_name in self.point_names:
            for phase_result in self.phases_results:
                point_result = phase_result.get_point_result(point_name)
                for i in range(len(point_result.step)):
                    record = {
                        "point_name": point_result.point_name,
                        "point_type": point_result.point_type,
                        "x": point_result.point_x,
                        "y": point_result.point_y,
                        "phase_name": phase_result.phase_name,
                        "phase_identification": phase_result.phase_identification,
                        "step": point_result.step[i],
                        "time": point_result.time[i],
                    }
                    for result in point_result.results:
                        record[result.result_type] = result.value[i]
                    records.append(record)

        # Create DataFrame
        return pd.DataFrame.from_records(records)
