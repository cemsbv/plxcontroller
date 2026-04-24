from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class SingleStepSafetyResult2D:
    """Class representing a safety result in a 2D PLAXIS model for a single step, phase and result type."""

    step: int
    time: float
    safety_factor: float


@dataclass
class SinglePhaseSafetyResult2D:
    """Class representing a safety result in a 2D PLAXIS model.
    for a single phase."""

    phase_name: str
    phase_identification: str
    results: list[SingleStepSafetyResult2D] = field(default_factory=list)

    def add_result(self, result: SingleStepSafetyResult2D) -> None:
        """Add a result."""
        self.results.append(result)


@dataclass
class MultiPhaseSafetyResult2D:
    """Class representing a safety result in a 2D PLAXIS model for multiple phases."""

    phases_results: list[SinglePhaseSafetyResult2D] = field(default_factory=list)

    def add_phase_result(self, phase_result: SinglePhaseSafetyResult2D) -> None:
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
        for phase_result in self.phases_results:
            for step_result in phase_result.results:
                record = {
                    "phase_name": phase_result.phase_name,
                    "phase_identification": phase_result.phase_identification,
                    "step": step_result.step,
                    "time": step_result.time,
                    "safety_factor": step_result.safety_factor,
                }
                records.append(record)

        # Create DataFrame
        return pd.DataFrame.from_records(records)
