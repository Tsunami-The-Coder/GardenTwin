from datetime import date, timedelta

from simulation.contracts import (
    CropState,
    NutrientState,
    SimulationRun,
    SimulationSite,
    SoilWaterState,
    WeatherObservation,
)
from simulation.engine import advance_one_day
from simulation.nutrients.balance import NutrientFluxes
from simulation.water.soil_properties import SoilHydraulicProperties


def simulate_season(
    run_id: str,
    observations: list[WeatherObservation],
    initial_soil: SoilWaterState,
    initial_nutrients: NutrientState,
    initial_crop: CropState,
    site: SimulationSite,
    planting_date: date,
    crop_coefficient: float,
    elevation_m: float = 0.0,
    actual_irrigation_by_date: dict | None = None,
    irrigation_efficiency: float = 0.90,
    depletion_fraction: float = 0.50,
    nutrient_fluxes_by_date: dict | None = None,
    nitrogen_sensitivity_per_mm: float = 0.0,
    phosphorus_sensitivity_per_mm: float = 0.0,
    potassium_sensitivity_per_mm: float = 0.0,
    soil_properties: SoilHydraulicProperties | None = None,
) -> SimulationRun:
    """Simulate a continuous sequence of daily weather observations."""

    if not observations:
        raise ValueError("At least one weather observation is required.")

    ordered = sorted(observations, key=lambda item: item.date)
    dates = [item.date for item in ordered]

    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate weather observation dates.")

    for previous, current in zip(dates, dates[1:]):
        if current != previous + timedelta(days=1):
            raise ValueError(
                f"Missing daily weather observation between "
                f"{previous} and {current}."
            )

    if dates[0] < planting_date:
        raise ValueError("Weather observations cannot precede planting.")

    irrigation_schedule = actual_irrigation_by_date or {}
    nutrient_schedule = nutrient_fluxes_by_date or {}

    previous_soil = initial_soil
    current_nutrients = initial_nutrients
    current_crop = initial_crop
    records = []

    for observation in ordered:
        actual_irrigation = irrigation_schedule.get(
            observation.date, 0.0
        )

        daily_fluxes = nutrient_schedule.get(
            observation.date, NutrientFluxes()
        )

        result = advance_one_day(
            observation=observation,
            previous_soil=previous_soil,
            nutrients=current_nutrients,
            crop=current_crop,
            site=site,
            planting_date=planting_date,
            crop_coefficient=crop_coefficient,
            elevation_m=elevation_m,
            irrigation_mm=actual_irrigation,
            irrigation_efficiency=irrigation_efficiency,
            depletion_fraction=depletion_fraction,
            nutrient_fluxes=daily_fluxes,
            nitrogen_sensitivity_per_mm=nitrogen_sensitivity_per_mm,
            phosphorus_sensitivity_per_mm=phosphorus_sensitivity_per_mm,
            potassium_sensitivity_per_mm=potassium_sensitivity_per_mm,
            soil_properties=soil_properties,
        )

        records.append(result.record)

        previous_soil = result.record.soil_water
        current_nutrients = result.record.nutrients
        current_crop = result.record.crop

    return SimulationRun(
        run_id=run_id,
        site=site,
        crop_name=initial_crop.crop_name,
        planting_date=planting_date,
        start_date=dates[0],
        end_date=dates[-1],
        records=records,
    )
