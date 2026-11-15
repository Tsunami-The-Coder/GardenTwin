"""GardenTwin's four data-driven AI output pipelines.

These are transparent analytical fallbacks, not pretrained model inference.
Each pipeline returns structured results that can later be replaced by a
real Aurora, Prithvi, AgriFM-E, or Earth-2 inference adapter.
"""

from statistics import mean
from datetime import date

from ai.artifacts import (
    load_aurora_result,
    load_prithvi_result,
)
from ai.artifacts import (
    load_aurora_result,
    load_prithvi_result,
    load_earth2_result,
)

def _values(records, getter):
    return [
        value
        for record in records
        if (value := getter(record)) is not None
    ]


def _average(values):
    return round(mean(values), 3) if values else None


def _score(value):
    return round(max(0.0, min(1.0, value)), 3)


def _risk_label(score):
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "moderate"
    return "low"


def _weather(record, field):
    return getattr(record.weather, field, None)


def _crop(record, field):
    return getattr(record.crop, field, None)


def _water(record, field):
    return getattr(record.soil_water, field, None)


def _nutrient(record, field):
    return getattr(record.nutrients, field, None)


def _aurora_analysis(run):
    records = run.records
    temperatures = _values(
        records, lambda r: _weather(r, "temperature_mean_c")
    )
    rainfall = _values(
        records, lambda r: _weather(r, "precipitation_mm")
    )
    humidity = _values(
        records, lambda r: _weather(r, "relative_humidity_pct")
    )

    heat_days = sum(
        1 for r in records
        if (_weather(r, "temperature_max_c") or -999) >= 32
    )
    heavy_rain_days = sum(
        1 for r in records
        if (_weather(r, "precipitation_mm") or 0) >= 20
    )
    dry_air_days = sum(
        1 for r in records
        if (
            _weather(r, "relative_humidity_pct") is not None
            and _weather(r, "relative_humidity_pct") < 35
        )
    )

    stress_values = _values(
        records, lambda r: _water(r, "water_stress_index")
    )
    stress = _average(stress_values) or 0.0

    weather_risk = _score(
        min(1.0, heat_days / max(1, len(records)) * 2)
        + min(0.3, heavy_rain_days / max(1, len(records)))
        + stress * 0.4
    )

    return {
        "system": "aurora",
        "model": "Microsoft Aurora",
        "status": "fallback_analysis",
        "method": "historical_weather_statistical_analysis",
        "input_source": "NASA POWER observations in simulation",
        "output": {
            "mean_temperature_c": _average(temperatures),
            "total_precipitation_mm": round(sum(rainfall), 2),
            "mean_relative_humidity_pct": _average(humidity),
            "heat_days": heat_days,
            "heavy_rain_days": heavy_rain_days,
            "low_humidity_days": dry_air_days,
            "weather_risk_score": weather_risk,
            "weather_risk": _risk_label(weather_risk),
            "interpretation": (
                "Historical weather conditions indicate "
                f"{_risk_label(weather_risk)} growing-weather risk."
            ),
        },
    }


def _prithvi_analysis(run):
    records = run.records
    water_ratios = []

    for record in records:
        water = _water(record, "root_zone_water_mm")
        capacity = _water(record, "field_capacity_mm")
        if water is not None and capacity and capacity > 0:
            water_ratios.append(max(0.0, min(1.5, water / capacity)))

    health = _values(records, lambda r: _crop(r, "health_index"))
    biomass = _values(records, lambda r: _crop(r, "biomass_kg_ha"))
    height = _values(records, lambda r: _crop(r, "height_cm"))

    average_water_ratio = _average(water_ratios)
    average_health = _average(health)

    condition_score = _score(
        (average_health if average_health is not None else 0.5)
        * 0.7
        + (
            min(1.0, average_water_ratio)
            if average_water_ratio is not None else 0.5
        ) * 0.3
    )

    return {
        "system": "prithvi",
        "model": "NASA/IBM Prithvi-EO-2.0",
        "status": "proxy_analysis",
        "method": "soil_water_and_crop_state_proxy",
        "input_source": "Simulation soil-water and crop-state records",
        "satellite_observations_available": False,
        "output": {
            "estimated_land_surface_condition_score": condition_score,
            "condition": _risk_label(1.0 - condition_score),
            "mean_root_zone_water_to_field_capacity_ratio": (
                average_water_ratio
            ),
            "mean_crop_health_index": average_health,
            "final_biomass_kg_ha": biomass[-1] if biomass else None,
            "final_height_cm": height[-1] if height else None,
            "interpretation": (
                "This is a ground-model proxy, not satellite imagery "
                "analysis. NASA HLS imagery and Prithvi inference "
                "are not yet integrated."
            ),
        },
    }


def _agrifm_analysis(run):
    records = run.records
    water_stress = _values(
        records, lambda r: _water(r, "water_stress_index")
    )
    nutrient_stress = _values(
        records, lambda r: _nutrient(r, "nutrient_stress_index")
    )
    health = _values(records, lambda r: _crop(r, "health_index"))

    mean_water_stress = _average(water_stress)
    mean_nutrient_stress = _average(nutrient_stress)
    mean_health = _average(health)

    # Unknown nutrient data is not silently treated as zero stress.
    combined_components = [
        value for value in (mean_water_stress, mean_nutrient_stress)
        if value is not None
    ]
    combined_stress = (
        _score(mean(combined_components))
        if combined_components else None
    )

    return {
        "system": "agrifm_e",
        "model": "AgriFM-E",
        "status": "fallback_analysis",
        "method": "agricultural_feature_risk_assessment",
        "input_source": (
            "Simulation crop, water, nutrient, and weather records"
        ),
        "output": {
            "mean_water_stress": mean_water_stress,
            "mean_nutrient_stress": mean_nutrient_stress,
            "mean_crop_health": mean_health,
            "combined_stress_score": combined_stress,
            "risk": (
                _risk_label(combined_stress)
                if combined_stress is not None else "unknown"
            ),
            "nutrient_data_available": bool(nutrient_stress),
            "interpretation": (
                "Nutrient stress remains unknown because no soil test "
                "was supplied."
                if not nutrient_stress else
                "Agricultural stress indicators were assessed from "
                "the simulation records."
            ),
        },
    }


def _earth2_analysis(run):
    records = run.records
    risk_days = []

    for record in records:
        risks = []
        maximum = _weather(record, "temperature_max_c")
        rainfall = _weather(record, "precipitation_mm")
        wind = _weather(record, "wind_speed_2m_m_s")

        if maximum is not None and maximum >= 32:
            risks.append("heat")
        if rainfall is not None and rainfall >= 20:
            risks.append("heavy_rain")
        if wind is not None and wind >= 8:
            risks.append("high_wind")

        if risks:
            risk_days.append({
                "date": record.date.isoformat(),
                "risks": risks,
            })

    risk_frequency = len(risk_days) / max(1, len(records))
    risk_score = _score(risk_frequency)

    return {
        "system": "earth2",
        "model": "NVIDIA Earth-2",
        "status": "fallback_analysis",
        "method": "historical_weather_hazard_window_analysis",
        "input_source": "NASA POWER historical daily weather",
        "output": {
            "days_with_weather_hazards": len(risk_days),
            "hazard_day_fraction": round(risk_frequency, 3),
            "historical_weather_risk": _risk_label(risk_score),
            "hazard_windows": risk_days[:20],
            "interpretation": (
                "These are detected historical hazard days, "
                "not Earth-2 forecasts."
            ),
        },
    }



def _artifact_date(value):
    """Extract an ISO calendar date from an artifact timestamp."""
    if not value:
        return None

    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _date_overlap(artifact_dates, run):
    """Describe how saved artifact dates overlap a simulation."""
    dates = [
        parsed
        for value in artifact_dates
        if (parsed := _artifact_date(value)) is not None
    ]

    if not dates:
        return {
            "status": "unknown",
            "overlapping_dates": [],
            "explanation": "Artifact dates are unavailable.",
        }

    overlapping = sorted({
        item for item in dates
        if run.start_date <= item <= run.end_date
    })

    if len(overlapping) == len(set(dates)):
        status = "full"
    elif overlapping:
        status = "partial"
    else:
        status = "none"

    return {
        "status": status,
        "overlapping_dates": [
            item.isoformat() for item in overlapping
        ],
        "artifact_dates": [
            item.isoformat() for item in sorted(set(dates))
        ],
    }


def analyze_simulation_with_ai(run):
    """Return pretrained inference with explicit applicability metadata."""

    if not run.records:
        raise ValueError(
            "Cannot analyze a simulation with no daily records."
        )

    systems = {}
    artifact_errors = {}

    try:
        systems["aurora"] = load_aurora_result()
    except Exception as exc:
        systems["aurora"] = _aurora_analysis(run)
        artifact_errors["aurora"] = str(exc)

    try:
        systems["prithvi"] = load_prithvi_result()
    except Exception as exc:
        systems["prithvi"] = _prithvi_analysis(run)
        artifact_errors["prithvi"] = str(exc)

    systems["agrifm_e"] = _agrifm_analysis(run)

    try:
        systems["earth2"] = load_earth2_result()
    except Exception as exc:
        systems["earth2"] = _earth2_analysis(run)
        artifact_errors["earth2"] = str(exc)

    # Aurora: its saved initialization must overlap the simulation.
    aurora = systems["aurora"]
    if aurora.get("status") == "pretrained_inference_artifact":
        overlap = _date_overlap(
            [aurora.get("initialization_time")],
            run,
        )
        aurora["artifact_relevance"] = {
            **overlap,
            "spatial_match": "unverified",
            "usable_as_simulation_period_prediction": (
                bool(overlap["overlapping_dates"])
            ),
            "explanation": (
                "The saved Aurora initialization does not overlap "
                "this simulation period."
                if not overlap["overlapping_dates"]
                else "Temporal overlap exists, but the artifact is "
                     "not calibrated to this garden."
            ),
        }

    # Prithvi: distinguish overlapping satellite observations from
    # observations outside the simulated period.
    prithvi = systems["prithvi"]
    if prithvi.get("status") == "pretrained_inference_artifact":
        overlap = _date_overlap(
            prithvi.get("observation_dates", prithvi.get("dates", [])),
            run,
        )
        prithvi["artifact_relevance"] = {
            **overlap,
            "spatial_match": "pilot-site artifact; verify metadata",
            "usable_as_simulation_period_feature": (
                bool(overlap["overlapping_dates"])
            ),
            "explanation": (
                "These are pretrained satellite features, not a "
                "crop-health classification."
            ),
        }

    # Earth-2: check both location and forecast freshness.
    earth2 = systems["earth2"]
    if earth2.get("status") == "pretrained_inference_artifact":
        location = earth2.get("location") or {}
        spatial_match = "unverified"

        if isinstance(location, dict):
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is not None and longitude is not None:
                matches = (
                    abs(float(latitude) - run.site.latitude) <= 0.5
                    and abs(float(longitude) - run.site.longitude) <= 0.5
                )
                spatial_match = "matched" if matches else "mismatch"

        forecast_status = earth2.get("forecast_status", "unknown")

        earth2["artifact_relevance"] = {
            "forecast_status": forecast_status,
            "spatial_match": spatial_match,
            "usable_as_upcoming_forecast": (
                forecast_status == "upcoming"
                and spatial_match == "matched"
            ),
            "explanation": (
                "The saved forecast is stale."
                if forecast_status == "stale"
                else "The forecast is not verified as both current "
                     "and spatially matched to this garden."
            ),
        }

    return {
        "run_id": run.run_id,
        "location": run.site.location_name,
        "crop": run.crop_name,
        "analysis_type": "mixed_pretrained_inference_and_fallbacks",
        "systems": systems,
        "artifact_errors": artifact_errors,
        "limitations": [
            "Aurora uses saved historical ERA5 inference, not "
            "live inference for each simulation.",
            "Prithvi produces learned satellite features, not "
            "a trained crop-health classification.",
            "AgriFM-E uses an analytical fallback because an "
            "official public inference checkpoint has not been verified.",
            "Earth-2 uses saved FourCastNet1 inference; stale "
            "forecasts must not be treated as upcoming predictions.",
            "Nutrient assessments remain limited without soil-test data.",
        ],
    }
