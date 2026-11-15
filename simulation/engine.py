from dataclasses import dataclass, replace
from datetime import date
from simulation.crops.growth import estimate_crop_growth
from simulation.crops.growth import estimate_stress_adjusted_growth
from simulation.water.soil_properties import SoilHydraulicProperties

import math

from simulation.contracts import (
    CropState,
    DailySimulationRecord,
    FertilizerRecommendation,
    IrrigationRecommendation,
    NutrientState,
    RecommendationStatus,
    SimulationSite,
    SoilWaterState,
    WeatherObservation,
)
from simulation.nutrients.balance import NutrientFluxes
from simulation.nutrients.daily import (
    DailyNutrientResult,
    simulate_daily_nutrients,
)
from simulation.water.bucket import (
    WaterBalanceResult,
    simulate_water_balance,
)
from simulation.water.evapotranspiration import (
    calculate_reference_et,
)
from simulation.crops.profiles import (
    determine_growth_stage,
    get_crop_profile,
)
from simulation.crops.thermal_time import (
    calculate_daily_gdd,
    accumulate_gdd,
)


@dataclass
class DailyEngineOutput:
    record: DailySimulationRecord
    reference_et_mm: float
    water_balance: WaterBalanceResult
    nutrient_result: DailyNutrientResult


def advance_one_day(
    observation: WeatherObservation,
    previous_soil: SoilWaterState,
    nutrients: NutrientState,
    crop: CropState,
    site: SimulationSite,
    planting_date: date,
    crop_coefficient: float,
    elevation_m: float = 0.0,
    irrigation_mm: float = 0.0,
    irrigation_efficiency: float = 0.90,
    depletion_fraction: float = 0.50,
    nutrient_fluxes: NutrientFluxes | None = None,
    nitrogen_sensitivity_per_mm: float = 0.0,
    phosphorus_sensitivity_per_mm: float = 0.0,
    potassium_sensitivity_per_mm: float = 0.0,
    soil_properties: SoilHydraulicProperties | None = None,
) -> DailyEngineOutput:

    if observation.date < planting_date:
        raise ValueError("Observation cannot precede planting date.")

    required_weather = {
        "minimum temperature": observation.temperature_min_c,
        "maximum temperature": observation.temperature_max_c,
        "relative humidity": observation.relative_humidity_pct,
        "solar radiation": observation.solar_radiation_mj_m2_day,
        "wind speed": observation.wind_speed_2m_m_s,
        "precipitation": observation.precipitation_mm,
    }

    missing = [
        name for name, value in required_weather.items()
        if value is None
    ]

    if missing:
        raise ValueError(
            "Missing required weather fields: " + ", ".join(missing)
        )

    if (
        previous_soil.root_zone_water_mm is None
        or previous_soil.field_capacity_mm is None
        or previous_soil.wilting_point_mm is None
        or previous_soil.root_depth_cm is None
    ):
        raise ValueError("Soil-water parameters are incomplete.")

    if not math.isfinite(crop_coefficient) or crop_coefficient <= 0:
        raise ValueError("Crop coefficient must be finite and positive.")

    reference_et = calculate_reference_et(
        observation_date=observation.date,
        temperature_min_c=observation.temperature_min_c,
        temperature_max_c=observation.temperature_max_c,
        relative_humidity_percent=observation.relative_humidity_pct,
        solar_radiation_mj_m2_day=(
            observation.solar_radiation_mj_m2_day
        ),
        wind_speed_2m_m_s=observation.wind_speed_2m_m_s,
        latitude_degrees=site.latitude,
        elevation_m=elevation_m,
    )

    water_result = simulate_water_balance(
        soil=previous_soil,
        precipitation_mm=observation.precipitation_mm,
        reference_et_mm=reference_et,
        crop_coefficient=crop_coefficient,
        irrigation_mm=irrigation_mm,
        irrigation_efficiency=irrigation_efficiency,
        depletion_fraction=depletion_fraction,
        soil_properties=soil_properties,
    )

    # Advance nutrient state using the drainage calculated by the
    # water-balance model.
    if nutrient_fluxes is None:
        nutrient_fluxes = NutrientFluxes()

    nutrient_result = simulate_daily_nutrients(
        nutrients=nutrients,
        fluxes=nutrient_fluxes or NutrientFluxes(),
        drainage_mm=water_result.drainage_mm,
        nitrogen_sensitivity_per_mm=nitrogen_sensitivity_per_mm,
        phosphorus_sensitivity_per_mm=phosphorus_sensitivity_per_mm,
        potassium_sensitivity_per_mm=potassium_sensitivity_per_mm,
        soil_properties=soil_properties,
        root_zone_water_mm=water_result.soil_water.root_zone_water_mm,
    )

    days_after_planting = (
        observation.date - planting_date
    ).days

    
    crop_name = crop.crop_name.strip().lower()
    profile = get_crop_profile(crop_name)

    daily_gdd = calculate_daily_gdd(
        temperature_min_c=observation.temperature_min_c,
        temperature_max_c=observation.temperature_max_c,
        base_temperature_c=profile.base_temperature_c,
        upper_temperature_c=profile.upper_temperature_c,
    )

    accumulated_gdd = accumulate_gdd(
        crop.accumulated_gdd,
        daily_gdd,
    )

    growth_stage = determine_growth_stage(
        accumulated_gdd,
        profile,
    )

    nutrient_stress = (
        nutrient_result.balance.state.nutrient_stress_index
    )

    height_cm, biomass_kg_ha, health_index = (
        estimate_stress_adjusted_growth(
            previous_gdd=crop.accumulated_gdd,
            current_gdd=accumulated_gdd,
            previous_height_cm=crop.height_cm or 0.0,
            previous_biomass_kg_ha=crop.biomass_kg_ha or 0.0,
            profile=profile,
            water_stress_index=water_result.water_stress_index,
            nutrient_stress_index=nutrient_stress,
        )
    )

    updated_crop = replace(
        crop,
        days_after_planting=days_after_planting,
        accumulated_gdd=accumulated_gdd,
        growth_stage=growth_stage.value,
        height_cm=height_cm,
        biomass_kg_ha=biomass_kg_ha,
        health_index=health_index,
    )


    recommended_amount = water_result.irrigation_recommendation_mm

    if recommended_amount > 0:
        irrigation = IrrigationRecommendation(
            status=RecommendationStatus.APPLY,
            amount_mm=recommended_amount,
            reason=(
                "Modeled root-zone depletion exceeded "
                "the configured irrigation threshold."
            ),
            confidence=None,
        )
    else:
        irrigation = IrrigationRecommendation(
            status=RecommendationStatus.NONE,
            amount_mm=0.0,
            reason="Modeled soil moisture is within the irrigation threshold.",
            confidence=None,
        )

    
    # Estimate daily nutrient uptake from modeled daily biomass gain.
    # These are generic illustrative tissue-composition assumptions,
    # not crop-calibrated measurements or fertilizer application rates.
    previous_biomass = crop.biomass_kg_ha or 0.0
    current_biomass = updated_crop.biomass_kg_ha or 0.0

    daily_biomass_gain = max(
        0.0,
        current_biomass - previous_biomass,
    )

    estimated_n = daily_biomass_gain * 0.030
    estimated_p = daily_biomass_gain * 0.005
    estimated_k = daily_biomass_gain * 0.035


    soil_test_available = (
        nutrient_result.balance.state.soil_test_available
    )

    modeled_nutrient_stress = (
        nutrient_result.balance.state.nutrient_stress_index
    )

    if not soil_test_available:
        fertilizer_status = RecommendationStatus.UNKNOWN
        fertilizer_reason = (
            f"Estimated crop-stage nutrient uptake: "
            f"N={estimated_n:.3f}, P={estimated_p:.3f}, "
            f"K={estimated_k:.3f} kg/ha/day. "
            if estimated_n is not None
            else "Crop nutrient demand could not be estimated. "
        ) + (
            "A soil test is needed before determining whether "
            "fertilizer is required or calculating an application rate."
        )
        fertilizer_confidence = None

    elif modeled_nutrient_stress is not None and modeled_nutrient_stress >= 0.25:
        fertilizer_status = RecommendationStatus.APPLY
        fertilizer_reason = (
            "The nutrient model indicates elevated nutrient stress. "
            "Use measured soil-test results and local agricultural "
            "guidance to determine the appropriate fertilizer and rate."
        )
        fertilizer_confidence = 0.5

    elif modeled_nutrient_stress is not None:
        fertilizer_status = RecommendationStatus.NONE
        fertilizer_reason = (
            "The nutrient model does not currently indicate significant "
            "nutrient stress."
        )
        fertilizer_confidence = 0.5

    else:
        fertilizer_status = RecommendationStatus.UNKNOWN
        fertilizer_reason = (
            "Nutrient stress could not be determined from the available "
            "nutrient inputs."
        )
        fertilizer_confidence = None

    fertilizer = FertilizerRecommendation(
        status=fertilizer_status,
        estimated_daily_n_demand_kg_ha=estimated_n,
        estimated_daily_p_demand_kg_ha=estimated_p,
        estimated_daily_k_demand_kg_ha=estimated_k,
        reason=fertilizer_reason,
        confidence=fertilizer_confidence,
    )

    alerts = []

    if not nutrient_result.balance.state.soil_test_available:
        alerts.append(
            "No soil test is available; nutrient estimates "
            "may be incomplete."
        )

    if water_result.water_stress_index > 0:
        alerts.append("The water model indicates crop water stress.")

    record = DailySimulationRecord(
        date=observation.date,
        weather=observation,
        soil_water=water_result.soil_water,
        nutrients=nutrient_result.balance.state,
        crop=updated_crop,
        irrigation=irrigation,
        fertilizer=fertilizer,
        alerts=alerts,
    )

    return DailyEngineOutput(
        record=record,
        reference_et_mm=reference_et,
        water_balance=water_result,
        nutrient_result=nutrient_result,
    )
