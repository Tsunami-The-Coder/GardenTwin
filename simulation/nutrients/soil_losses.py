
from dataclasses import dataclass
import math

from simulation.contracts import NutrientState
from simulation.water.drainage import (
    DrainageResult,
    calculate_drainage,
)
from simulation.nutrients.leaching import (
    NutrientLeachingResult,
    calculate_nutrient_leaching,
)


@dataclass(frozen=True)
class SoilLossResult:
    drainage: DrainageResult
    nutrient_losses: NutrientLeachingResult


def _leaching_fraction(
    drainage_mm: float,
    sensitivity_per_mm: float,
) -> float:
    if not math.isfinite(sensitivity_per_mm):
        raise ValueError("Leaching sensitivity must be finite.")

    if sensitivity_per_mm < 0:
        raise ValueError("Leaching sensitivity cannot be negative.")

    return 1.0 - math.exp(-sensitivity_per_mm * drainage_mm)


def calculate_soil_losses(
    soil_water_mm: float,
    field_capacity_mm: float,
    saturated_water_content_mm: float,
    drainage_fraction: float,
    nutrients: NutrientState,
    nitrogen_sensitivity_per_mm: float,
    phosphorus_sensitivity_per_mm: float,
    potassium_sensitivity_per_mm: float,
) -> SoilLossResult:
    """Calculate drainage and drainage-dependent nutrient losses."""

    drainage = calculate_drainage(
        soil_water_mm=soil_water_mm,
        field_capacity_mm=field_capacity_mm,
        saturated_water_content_mm=saturated_water_content_mm,
        drainage_fraction=drainage_fraction,
    )

    nitrogen_fraction = _leaching_fraction(
        drainage.drainage_mm, nitrogen_sensitivity_per_mm
    )
    phosphorus_fraction = _leaching_fraction(
        drainage.drainage_mm, phosphorus_sensitivity_per_mm
    )
    potassium_fraction = _leaching_fraction(
        drainage.drainage_mm, potassium_sensitivity_per_mm
    )

    nutrient_losses = calculate_nutrient_leaching(
        nutrients=nutrients,
        nitrogen_fraction=nitrogen_fraction,
        phosphorus_fraction=phosphorus_fraction,
        potassium_fraction=potassium_fraction,
    )

    return SoilLossResult(
        drainage=drainage,
        nutrient_losses=nutrient_losses,
    )
