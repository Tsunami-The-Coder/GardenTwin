from dataclasses import dataclass
import math

from simulation.contracts import NutrientState


@dataclass(frozen=True)
class NutrientLeachingResult:
    nitrogen_loss_kg_ha: float | None
    phosphorus_loss_kg_ha: float | None
    potassium_loss_kg_ha: float | None


def _calculate_loss(
    available_kg_ha: float | None,
    leaching_fraction: float,
) -> float | None:
    if not math.isfinite(leaching_fraction):
        raise ValueError("Leaching fraction must be finite.")

    if not 0.0 <= leaching_fraction <= 1.0:
        raise ValueError("Leaching fraction must be between 0 and 1.")

    if available_kg_ha is None:
        return None

    return available_kg_ha * leaching_fraction


def calculate_nutrient_leaching(
    nutrients: NutrientState,
    nitrogen_fraction: float,
    phosphorus_fraction: float,
    potassium_fraction: float,
) -> NutrientLeachingResult:
    """Calculate nutrient losses using fractions supplied by a soil model."""

    return NutrientLeachingResult(
        nitrogen_loss_kg_ha=_calculate_loss(
            nutrients.nitrogen_available_kg_ha,
            nitrogen_fraction,
        ),
        phosphorus_loss_kg_ha=_calculate_loss(
            nutrients.phosphorus_available_kg_ha,
            phosphorus_fraction,
        ),
        potassium_loss_kg_ha=_calculate_loss(
            nutrients.potassium_available_kg_ha,
            potassium_fraction,
        ),
    )
