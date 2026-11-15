
import math

from simulation.crops.profiles import CropProfile


def estimate_crop_growth(
    accumulated_gdd: float,
    profile: CropProfile,
) -> tuple[float, float]:
    """
    Estimate potential crop height and biomass from accumulated GDD.

    This is an illustrative growth curve, not a calibrated crop model.
    """

    if not math.isfinite(accumulated_gdd) or accumulated_gdd < 0:
        raise ValueError(
            "Accumulated GDD must be finite and nonnegative."
        )

    maturity_gdd = profile.stage_thresholds[-1].accumulated_gdd
    progress = min(accumulated_gdd / maturity_gdd, 1.0)

    height_cm = (
        profile.max_height_cm
        * progress ** profile.height_growth_exponent
    )

    biomass_kg_ha = (
        profile.mature_biomass_kg_ha
        * progress ** profile.biomass_growth_exponent
    )

    return height_cm, biomass_kg_ha


def estimate_stress_adjusted_growth(
    previous_gdd: float,
    current_gdd: float,
    previous_height_cm: float,
    previous_biomass_kg_ha: float,
    profile: CropProfile,
    water_stress_index: float,
    nutrient_stress_index: float | None,
) -> tuple[float, float, float | None]:
    """
    Estimate today's growth using known water and nutrient stress.

    Unknown nutrient stress is excluded from the growth multiplier,
    meaning the estimate uses known water effects only. Health remains
    unknown until nutrient stress can also be calculated.
    """

    values = (
        previous_gdd,
        current_gdd,
        previous_height_cm,
        previous_biomass_kg_ha,
        water_stress_index,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Growth inputs must be finite.")

    if previous_gdd < 0 or current_gdd < previous_gdd:
        raise ValueError("GDD values must be nonnegative and increasing.")

    if previous_height_cm < 0 or previous_biomass_kg_ha < 0:
        raise ValueError("Previous growth values cannot be negative.")

    if not 0 <= water_stress_index <= 1:
        raise ValueError("Water stress must be between 0 and 1.")

    if nutrient_stress_index is not None:
        if (
            not math.isfinite(nutrient_stress_index)
            or not 0 <= nutrient_stress_index <= 1
        ):
            raise ValueError(
                "Nutrient stress must be between 0 and 1."
            )

    previous_potential = estimate_crop_growth(
        previous_gdd,
        profile,
    )

    current_potential = estimate_crop_growth(
        current_gdd,
        profile,
    )

    water_growth_factor = 1.0 - water_stress_index

    if nutrient_stress_index is None:
        combined_growth_factor = water_growth_factor
        health_index = None
    else:
        nutrient_growth_factor = 1.0 - nutrient_stress_index

        combined_growth_factor = (
            water_growth_factor * nutrient_growth_factor
        )

        health_index = combined_growth_factor

    daily_height_growth = (
        current_potential[0] - previous_potential[0]
    ) * combined_growth_factor

    daily_biomass_growth = (
        current_potential[1] - previous_potential[1]
    ) * combined_growth_factor

    height_cm = previous_height_cm + max(0.0, daily_height_growth)
    biomass_kg_ha = (
        previous_biomass_kg_ha
        + max(0.0, daily_biomass_growth)
    )

    return height_cm, biomass_kg_ha, health_index
