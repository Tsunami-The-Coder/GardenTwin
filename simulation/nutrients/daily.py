from dataclasses import dataclass, replace
import math

from simulation.contracts import NutrientState
from simulation.nutrients.balance import (
    NutrientBalanceResult,
    NutrientFluxes,
    simulate_nutrient_balance,
)
from simulation.nutrients.leaching import (
    NutrientLeachingResult,
    calculate_nutrient_leaching,
)
from simulation.water.soil_properties import SoilHydraulicProperties


@dataclass(frozen=True)
class DailyNutrientResult:
    balance: NutrientBalanceResult
    nutrient_losses: NutrientLeachingResult
    drainage_mm: float


def _legacy_leaching_fraction(
    drainage_mm: float,
    sensitivity_per_mm: float,
) -> float:
    if not math.isfinite(drainage_mm) or drainage_mm < 0:
        raise ValueError("Drainage must be finite and nonnegative.")

    if not math.isfinite(sensitivity_per_mm):
        raise ValueError("Leaching sensitivity must be finite.")

    if sensitivity_per_mm < 0:
        raise ValueError("Leaching sensitivity cannot be negative.")

    return 1.0 - math.exp(-sensitivity_per_mm * drainage_mm)


def _pool_after_additions(
    available: float | None,
    fertilizer: float,
    mineralization: float,
) -> float | None:
    if available is None:
        return None

    return available + fertilizer + mineralization


def simulate_daily_nutrients(
    nutrients: NutrientState,
    fluxes: NutrientFluxes,
    drainage_mm: float,
    nitrogen_sensitivity_per_mm: float = 0.0,
    phosphorus_sensitivity_per_mm: float = 0.0,
    potassium_sensitivity_per_mm: float = 0.0,
    soil_properties: SoilHydraulicProperties | None = None,
    root_zone_water_mm: float | None = None,
) -> DailyNutrientResult:
    """
    Apply daily nutrient additions, leaching, and crop uptake.

    Preferred mode:
        Uses soil hydraulic properties, drainage, and root-zone
        water to calculate nutrient-specific leaching fractions.

    Compatibility mode:
        Uses the older independent sensitivity parameters when
        soil_properties is not supplied. This path is temporary.
    """

    if not math.isfinite(drainage_mm) or drainage_mm < 0:
        raise ValueError("Drainage must be finite and nonnegative.")

    pool = NutrientState(
        nitrogen_available_kg_ha=_pool_after_additions(
            nutrients.nitrogen_available_kg_ha,
            fluxes.fertilizer_n_kg_ha,
            fluxes.mineralization_n_kg_ha,
        ),
        phosphorus_available_kg_ha=_pool_after_additions(
            nutrients.phosphorus_available_kg_ha,
            fluxes.fertilizer_p_kg_ha,
            fluxes.mineralization_p_kg_ha,
        ),
        potassium_available_kg_ha=_pool_after_additions(
            nutrients.potassium_available_kg_ha,
            fluxes.fertilizer_k_kg_ha,
            fluxes.mineralization_k_kg_ha,
        ),
        nutrient_stress_index=nutrients.nutrient_stress_index,
        soil_test_available=nutrients.soil_test_available,
    )

    if soil_properties is not None:
        if root_zone_water_mm is None:
            raise ValueError(
                "Root-zone water is required when soil properties are supplied."
            )

        nitrogen_fraction = soil_properties.calculate_leaching_fraction(
            drainage_mm=drainage_mm,
            root_zone_water_mm=root_zone_water_mm,
            nutrient_mobility=soil_properties.nitrogen_mobility,
        )
        phosphorus_fraction = soil_properties.calculate_leaching_fraction(
            drainage_mm=drainage_mm,
            root_zone_water_mm=root_zone_water_mm,
            nutrient_mobility=soil_properties.phosphorus_mobility,
        )
        potassium_fraction = soil_properties.calculate_leaching_fraction(
            drainage_mm=drainage_mm,
            root_zone_water_mm=root_zone_water_mm,
            nutrient_mobility=soil_properties.potassium_mobility,
        )
    else:
        nitrogen_fraction = _legacy_leaching_fraction(
            drainage_mm, nitrogen_sensitivity_per_mm
        )
        phosphorus_fraction = _legacy_leaching_fraction(
            drainage_mm, phosphorus_sensitivity_per_mm
        )
        potassium_fraction = _legacy_leaching_fraction(
            drainage_mm, potassium_sensitivity_per_mm
        )

    losses = calculate_nutrient_leaching(
        nutrients=pool,
        nitrogen_fraction=nitrogen_fraction,
        phosphorus_fraction=phosphorus_fraction,
        potassium_fraction=potassium_fraction,
    )

    daily_fluxes = replace(
        fluxes,
        losses_n_kg_ha=(
            fluxes.losses_n_kg_ha
            + (losses.nitrogen_loss_kg_ha or 0.0)
        ),
        losses_p_kg_ha=(
            fluxes.losses_p_kg_ha
            + (losses.phosphorus_loss_kg_ha or 0.0)
        ),
        losses_k_kg_ha=(
            fluxes.losses_k_kg_ha
            + (losses.potassium_loss_kg_ha or 0.0)
        ),
    )

    balance = simulate_nutrient_balance(
        nutrients=nutrients,
        fluxes=daily_fluxes,
    )

    return DailyNutrientResult(
        balance=balance,
        nutrient_losses=losses,
        drainage_mm=drainage_mm,
    )
