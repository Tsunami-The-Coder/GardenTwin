from uuid import uuid4

from simulation.contracts import (
    CropState,
    NutrientState,
    SimulationSite,
    SoilWaterState,
)
from simulation.season import simulate_season
from simulation.water.soil_properties import SoilHydraulicProperties
from simulation.weather.nasa_power import fetch_nasa_power_weather

from backend.schemas.simulation import SimulationRequest
from backend.services.ssurgo_service import fetch_ssurgo_soil


def run_garden_simulation(request: SimulationRequest):
    """Build and execute a GardenTwin simulation."""

    site = SimulationSite(
        site_id=str(uuid4()),
        latitude=request.latitude,
        longitude=request.longitude,
        location_name=request.location_name,
    )

    observations = fetch_nasa_power_weather(
        site=site,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if not observations:
        raise ValueError(
            "No historical weather observations were returned."
        )

    # Start with the manual values. These are the fallback when
    # SSURGO is unavailable or the user selects manual mode.
    soil_properties = SoilHydraulicProperties(
        wilting_point=request.wilting_point,
        field_capacity=request.field_capacity,
        saturation=request.saturation,
        saturated_hydraulic_conductivity_mm_day=(
            request.saturated_hydraulic_conductivity_mm_day
        ),
        root_depth_cm=request.root_depth_cm,
    )

    soil_data_source = "Manual user inputs"
    soil_map_unit_key = None
    soil_map_unit_name = None
    soil_component_name = None
    soil_lookup_note = None

    if request.soil_mode in ("auto", "ssurgo"):
        try:
            ssurgo_result = fetch_ssurgo_soil(
                site=site,
                root_depth_cm=request.root_depth_cm,
            )
        except RuntimeError as exc:
            if request.soil_mode == "ssurgo":
                raise

            ssurgo_result = None
            soil_lookup_note = (
                "SSURGO lookup failed. Manual soil assumptions "
                f"were used instead. Details: {exc}"
            )

        if ssurgo_result is not None:
            soil_properties = ssurgo_result.properties
            soil_data_source = ssurgo_result.source
            soil_map_unit_key = ssurgo_result.map_unit_key
            soil_map_unit_name = ssurgo_result.map_unit_name
            soil_component_name = ssurgo_result.dominant_component

        elif request.soil_mode == "ssurgo":
            raise RuntimeError(
                "SSURGO returned no usable hydraulic properties "
                "for this location. Try auto or manual soil mode."
            )

        elif soil_lookup_note is None:
            soil_lookup_note = (
                "No usable SSURGO soil profile was found. "
                "Manual soil assumptions were used instead."
            )

    # Use the selected soil profile consistently for both the
    # initial water state and the daily water-balance simulation.
    root_depth_cm = soil_properties.root_depth_cm
    conversion = root_depth_cm * 10

    # Use field capacity when the user does not specify initial moisture.
    # Preserve explicitly supplied moisture, capped at soil saturation.
    requested_water_content = (
        soil_properties.field_capacity
        if request.initial_water_content is None
        else request.initial_water_content
    )

    initial_water_content = min(
        requested_water_content,
        soil_properties.saturation,
    )

    initial_soil = SoilWaterState(
        root_zone_water_mm=initial_water_content * conversion,
        field_capacity_mm=soil_properties.field_capacity * conversion,
        wilting_point_mm=soil_properties.wilting_point * conversion,
        root_depth_cm=root_depth_cm,
    )

    # No soil test was supplied, so nutrient availability remains unknown.
    initial_nutrients = NutrientState(
        soil_test_available=False,
    )

    initial_crop = CropState(
        crop_name=request.crop_name,
        growth_stage="planted",
        days_after_planting=0,
    )

    run = simulate_season(
        run_id=str(uuid4()),
        observations=observations,
        initial_soil=initial_soil,
        initial_nutrients=initial_nutrients,
        initial_crop=initial_crop,
        site=site,
        planting_date=request.planting_date,
        crop_coefficient=request.crop_coefficient,
        soil_properties=soil_properties,
    )

    # Attach provenance and the exact hydraulic values used.
    run.soil_data_source = soil_data_source
    run.soil_map_unit_key = soil_map_unit_key
    run.soil_map_unit_name = soil_map_unit_name
    run.soil_component_name = soil_component_name
    run.soil_lookup_note = soil_lookup_note
    run.soil_properties = {
        "wilting_point": soil_properties.wilting_point,
        "field_capacity": soil_properties.field_capacity,
        "saturation": soil_properties.saturation,
        "saturated_hydraulic_conductivity_mm_day": (
            soil_properties.saturated_hydraulic_conductivity_mm_day
        ),
        "root_depth_cm": soil_properties.root_depth_cm,
        "initial_water_content_used": initial_water_content,
    }

    run.simulation_parameters = {
        "crop_coefficient": request.crop_coefficient,
        "elevation_m": 0.0,
        "irrigation_efficiency": 0.90,
        "depletion_fraction": 0.50,
    }

    return run
