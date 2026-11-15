from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DrainageResult:
    water_above_field_capacity_mm: float
    drainage_mm: float
    water_remaining_mm: float


def calculate_drainage(
    soil_water_mm: float,
    field_capacity_mm: float,
    saturated_water_content_mm: float,
    drainage_fraction: float,
) -> DrainageResult:
    """
    Estimate daily drainage from water stored above field capacity.

    drainage_fraction is a simplified daily drainage coefficient.
    It must eventually be calibrated using soil hydraulic properties.
    """

    values = (
        soil_water_mm,
        field_capacity_mm,
        saturated_water_content_mm,
        drainage_fraction,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("All inputs must be finite.")

    if field_capacity_mm < 0:
        raise ValueError("Field capacity cannot be negative.")

    if saturated_water_content_mm < field_capacity_mm:
        raise ValueError(
            "Saturated water content must be at least field capacity."
        )

    if not field_capacity_mm <= soil_water_mm <= saturated_water_content_mm:
        raise ValueError(
            "Soil water must be between field capacity and saturation."
        )

    if not 0.0 <= drainage_fraction <= 1.0:
        raise ValueError("Drainage fraction must be between 0 and 1.")

    excess = soil_water_mm - field_capacity_mm
    drainage = excess * drainage_fraction
    remaining = soil_water_mm - drainage

    return DrainageResult(
        water_above_field_capacity_mm=excess,
        drainage_mm=drainage,
        water_remaining_mm=remaining,
    )
