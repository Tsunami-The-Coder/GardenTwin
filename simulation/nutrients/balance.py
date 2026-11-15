from dataclasses import dataclass
from math import isfinite

from simulation.contracts import NutrientState


@dataclass
class NutrientFluxes:
    """Daily nutrient inputs and demands, all in kg/ha."""

    fertilizer_n_kg_ha: float = 0.0
    fertilizer_p_kg_ha: float = 0.0
    fertilizer_k_kg_ha: float = 0.0

    mineralization_n_kg_ha: float = 0.0
    mineralization_p_kg_ha: float = 0.0
    mineralization_k_kg_ha: float = 0.0

    crop_demand_n_kg_ha: float = 0.0
    crop_demand_p_kg_ha: float = 0.0
    crop_demand_k_kg_ha: float = 0.0

    losses_n_kg_ha: float = 0.0
    losses_p_kg_ha: float = 0.0
    losses_k_kg_ha: float = 0.0

    def __post_init__(self):
        for name, value in vars(self).items():
            if not isfinite(value) or value < 0:
                raise ValueError(
                    f"{name} must be finite and nonnegative."
                )


@dataclass
class NutrientBalanceResult:
    state: NutrientState

    actual_uptake_n_kg_ha: float | None
    actual_uptake_p_kg_ha: float | None
    actual_uptake_k_kg_ha: float | None

    unmet_demand_n_kg_ha: float | None
    unmet_demand_p_kg_ha: float | None
    unmet_demand_k_kg_ha: float | None



def _calculate_one_nutrient(
    available,
    fertilizer,
    mineralization,
    demand,
    losses,
):
    if available is None:
        return None, None, None

    pool = available + fertilizer + mineralization

    # Apply losses before crop uptake.
    actual_losses = min(pool, losses)
    remaining_after_losses = pool - actual_losses

    # Crop uptake cannot exceed what remains.
    actual_uptake = min(remaining_after_losses, demand)
    unmet_demand = demand - actual_uptake

    remaining = remaining_after_losses - actual_uptake

    return remaining, actual_uptake, unmet_demand



def simulate_nutrient_balance(
    nutrients: NutrientState,
    fluxes: NutrientFluxes,
) -> NutrientBalanceResult:
    """Advance the available N, P, and K pools by one day."""

    n = _calculate_one_nutrient(
        nutrients.nitrogen_available_kg_ha,
        fluxes.fertilizer_n_kg_ha,
        fluxes.mineralization_n_kg_ha,
        fluxes.crop_demand_n_kg_ha,
        fluxes.losses_n_kg_ha,
    )

    p = _calculate_one_nutrient(
        nutrients.phosphorus_available_kg_ha,
        fluxes.fertilizer_p_kg_ha,
        fluxes.mineralization_p_kg_ha,
        fluxes.crop_demand_p_kg_ha,
        fluxes.losses_p_kg_ha,
    )

    k = _calculate_one_nutrient(
        nutrients.potassium_available_kg_ha,
        fluxes.fertilizer_k_kg_ha,
        fluxes.mineralization_k_kg_ha,
        fluxes.crop_demand_k_kg_ha,
        fluxes.losses_k_kg_ha,
    )

    # A stress index of 0 means all modeled demand was met.
    # A stress index of 1 means all modeled demand was unmet.
    # If any demanded nutrient has unknown availability,
    # overall nutrient stress cannot be calculated reliably.

    demands = [
        (
            fluxes.crop_demand_n_kg_ha,
            n[2],
        ),
        (
            fluxes.crop_demand_p_kg_ha,
            p[2],
        ),
        (
            fluxes.crop_demand_k_kg_ha,
            k[2],
        ),
    ]

    demanded = [
        (demand, unmet)
        for demand, unmet in demands
        if demand > 0
    ]

    if not demanded:
        stress_index = None
    elif any(unmet is None for _, unmet in demanded):
        stress_index = None
    else:
        stress_index = sum(
            unmet / demand
            for demand, unmet in demanded
        ) / len(demanded)

    updated_state = NutrientState(
        nitrogen_available_kg_ha=n[0],
        phosphorus_available_kg_ha=p[0],
        potassium_available_kg_ha=k[0],
        nutrient_stress_index=stress_index,
        soil_test_available=nutrients.soil_test_available,
    )

    return NutrientBalanceResult(
        state=updated_state,

        actual_uptake_n_kg_ha=n[1],
        actual_uptake_p_kg_ha=p[1],
        actual_uptake_k_kg_ha=k[1],

        unmet_demand_n_kg_ha=n[2],
        unmet_demand_p_kg_ha=p[2],
        unmet_demand_k_kg_ha=k[2],
    )
