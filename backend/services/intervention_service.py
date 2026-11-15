from simulation.contracts import (
    CropState,
    NutrientState,
    SoilWaterState,
)
from simulation.season import simulate_season
from simulation.water.soil_properties import SoilHydraulicProperties


def _summarize(run, irrigation_total_mm=0.0):
    records = run.records

    water_stress = [
        record.soil_water.water_stress_index
        for record in records
        if record.soil_water.water_stress_index is not None
    ]

    health = [
        record.crop.health_index
        for record in records
        if record.crop.health_index is not None
    ]

    biomass = [
        record.crop.biomass_kg_ha
        for record in records
        if record.crop.biomass_kg_ha is not None
    ]

    return {
        "days_simulated": len(records),
        "total_irrigation_mm": round(irrigation_total_mm, 2),
        "mean_water_stress": (
            round(sum(water_stress) / len(water_stress), 4)
            if water_stress else None
        ),
        "maximum_water_stress": (
            round(max(water_stress), 4)
            if water_stress else None
        ),
        "days_with_water_stress": sum(
            value > 0 for value in water_stress
        ),
        "final_crop_health_index": (
            round(health[-1], 4) if health else None
        ),
        "final_biomass_kg_ha": (
            round(biomass[-1], 2) if biomass else None
        ),
    }


def compare_irrigation_intervention(run):
    """Compare rain-fed conditions with recommended irrigation."""

    if not run.records:
        raise ValueError("Cannot compare a simulation with no records.")

    parameters = run.simulation_parameters
    soil_data = run.soil_properties

    required_parameters = ("crop_coefficient",)
    if any(key not in parameters for key in required_parameters):
        raise ValueError(
            "This simulation does not contain the original "
            "settings needed for intervention comparison. "
            "Create a new simulation and try again."
        )

    required_soil = (
        "wilting_point",
        "field_capacity",
        "saturation",
        "saturated_hydraulic_conductivity_mm_day",
        "root_depth_cm",
        "initial_water_content_used",
    )
    if any(key not in soil_data for key in required_soil):
        raise ValueError(
            "The original soil settings are incomplete. "
            "Create a new simulation and try again."
        )

    soil = SoilHydraulicProperties(
        wilting_point=soil_data["wilting_point"],
        field_capacity=soil_data["field_capacity"],
        saturation=soil_data["saturation"],
        saturated_hydraulic_conductivity_mm_day=(
            soil_data["saturated_hydraulic_conductivity_mm_day"]
        ),
        root_depth_cm=soil_data["root_depth_cm"],
    )

    root_depth = soil.root_depth_cm
    conversion = root_depth * 10
    initial_water = soil_data["initial_water_content_used"]

    initial_soil = SoilWaterState(
        root_zone_water_mm=initial_water * conversion,
        field_capacity_mm=soil.field_capacity * conversion,
        wilting_point_mm=soil.wilting_point * conversion,
        root_depth_cm=root_depth,
    )

    initial_nutrients = NutrientState(
        soil_test_available=False,
    )

    initial_crop = CropState(
        crop_name=run.crop_name,
        growth_stage="planted",
        days_after_planting=0,
    )

    observations = [record.weather for record in run.records]

    common = {
        "observations": observations,
        "initial_soil": initial_soil,
        "initial_nutrients": initial_nutrients,
        "initial_crop": initial_crop,
        "site": run.site,
        "planting_date": run.planting_date,
        "crop_coefficient": parameters["crop_coefficient"],
        "elevation_m": parameters.get("elevation_m", 0.0),
        "irrigation_efficiency": parameters.get(
            "irrigation_efficiency", 0.90
        ),
        "depletion_fraction": parameters.get(
            "depletion_fraction", 0.50
        ),
        "soil_properties": soil,
    }

    baseline = simulate_season(
        run_id=f"{run.run_id}-baseline",
        **common,
    )

    # Apply each baseline day's recommended amount on that same day.
    irrigation_schedule = {
        record.date: record.irrigation.amount_mm
        for record in baseline.records
        if (
            record.irrigation.amount_mm is not None
            and record.irrigation.amount_mm > 0
        )
    }

    intervention = simulate_season(
        run_id=f"{run.run_id}-irrigated",
        actual_irrigation_by_date=irrigation_schedule,
        **common,
    )

    baseline_summary = _summarize(baseline)
    intervention_total = sum(irrigation_schedule.values())
    intervention_summary = _summarize(
        intervention,
        irrigation_total_mm=intervention_total,
    )

    baseline_stress = baseline_summary["mean_water_stress"]
    intervention_stress = intervention_summary["mean_water_stress"]

    stress_reduction = None
    if baseline_stress is not None and intervention_stress is not None:
        stress_reduction = round(
            baseline_stress - intervention_stress,
            4,
        )

    baseline_biomass = baseline_summary["final_biomass_kg_ha"]
    intervention_biomass = intervention_summary["final_biomass_kg_ha"]

    biomass_difference = None
    if baseline_biomass is not None and intervention_biomass is not None:
        biomass_difference = round(
            intervention_biomass - baseline_biomass,
            2,
        )

    return {
        "run_id": run.run_id,
        "intervention": "apply_daily_model_recommended_irrigation",
        "method": (
            "Both scenarios use the same historical weather, "
            "soil profile, crop settings, and initial conditions. "
            "The intervention applies each baseline irrigation "
            "recommendation on its corresponding day."
        ),
        "baseline": baseline_summary,
        "intervention": intervention_summary,
        "difference": {
            "mean_water_stress_reduction": stress_reduction,
            "final_biomass_change_kg_ha": biomass_difference,
        },
        "limitations": [
            "This is a modeled scenario, not a measured field outcome.",
            "Daily recommendations are applied on the same day "
            "they are calculated.",
            "The comparison does not model irrigation cost, "
            "equipment constraints, or water availability.",
            "Nutrient availability remains unknown without a soil test.",
        ],
    }
