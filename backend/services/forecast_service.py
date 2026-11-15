
from dataclasses import asdict
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from simulation.contracts import WeatherObservation
from simulation.engine import advance_one_day
from simulation.water.soil_properties import SoilHydraulicProperties


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_seven_day_forecast(latitude: float, longitude: float):
    """Fetch seven days of daily forecast weather from Open-Meteo."""

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join([
            "temperature_2m_min",
            "temperature_2m_max",
            "precipitation_sum",
            "precipitation_probability_max",
            "relative_humidity_2m_mean",
            "shortwave_radiation_sum",
            "wind_speed_10m_mean",
        ]),
        "forecast_days": 7,
        "timezone": "auto",
        "wind_speed_unit": "ms",
    }

    url = f"{OPEN_METEO_URL}?{urlencode(params)}"
    request = Request(
        url,
        headers={"User-Agent": "GardenTwin/1.0"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve the seven-day weather forecast: {exc}"
        ) from exc

    try:
        daily = payload["daily"]
        dates = daily["time"]
        required = [
            "temperature_2m_min",
            "temperature_2m_max",
            "precipitation_sum",
            "relative_humidity_2m_mean",
            "shortwave_radiation_sum",
            "wind_speed_10m_mean",
        ]

        for key in required:
            if key not in daily or len(daily[key]) != len(dates):
                raise ValueError(f"Missing or incomplete forecast field: {key}")

        observations = []

        for i, day in enumerate(dates):
            values = {key: daily[key][i] for key in required}

            if any(value is None for value in values.values()):
                continue

            t_min = float(values["temperature_2m_min"])
            t_max = float(values["temperature_2m_max"])

            observations.append(
                WeatherObservation(
                    date=date.fromisoformat(day),
                    source="Open-Meteo forecast",
                    temperature_min_c=t_min,
                    temperature_max_c=t_max,
                    temperature_mean_c=(t_min + t_max) / 2,
                    precipitation_mm=float(values["precipitation_sum"]),
                    relative_humidity_pct=float(
                        values["relative_humidity_2m_mean"]
                    ),
                    solar_radiation_mj_m2_day=float(
                        values["shortwave_radiation_sum"]
                    ),
                    wind_speed_2m_m_s=float(
                        values["wind_speed_10m_mean"]
                    ),
                )
            )

        if not observations:
            raise ValueError("The weather provider returned no usable days.")

        probabilities = daily.get("precipitation_probability_max", [])

        return observations, {
            observation.date.isoformat(): (
                probabilities[i] if i < len(probabilities) else None
            )
            for i, observation in enumerate(observations)
        }

    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Open-Meteo returned invalid forecast data: {exc}"
        ) from exc


def build_seven_day_forecast(run):
    """Return forecast weather and, when dates align, simulated guidance."""

    if not run.records:
        raise ValueError("The simulation has no daily records.")

    observations, precipitation_probabilities = fetch_seven_day_forecast(
        run.site.latitude,
        run.site.longitude,
    )

    latest_record = run.records[-1]

    # Only continue the model when the first forecast day directly
    # follows the final simulated day.
    expected_next_day = latest_record.date + timedelta(days=1)
    continuation_available = observations[0].date == expected_next_day

    forecast_records = []

    if continuation_available:
        properties = run.soil_properties
        parameters = run.simulation_parameters

        required_soil = (
            "wilting_point",
            "field_capacity",
            "saturation",
            "saturated_hydraulic_conductivity_mm_day",
            "root_depth_cm",
        )

        if not all(key in properties for key in required_soil):
            raise ValueError(
                "The simulation is missing soil hydraulic properties."
            )

        soil_properties = SoilHydraulicProperties(
            wilting_point=properties["wilting_point"],
            field_capacity=properties["field_capacity"],
            saturation=properties["saturation"],
            saturated_hydraulic_conductivity_mm_day=(
                properties["saturated_hydraulic_conductivity_mm_day"]
            ),
            root_depth_cm=properties["root_depth_cm"],
        )

        previous_soil = latest_record.soil_water
        nutrients = latest_record.nutrients
        crop = latest_record.crop

        for observation in observations:
            result = advance_one_day(
                observation=observation,
                previous_soil=previous_soil,
                nutrients=nutrients,
                crop=crop,
                site=run.site,
                planting_date=run.planting_date,
                crop_coefficient=parameters.get("crop_coefficient", 1.0),
                elevation_m=parameters.get("elevation_m", 0.0),
                irrigation_efficiency=parameters.get(
                    "irrigation_efficiency", 0.90
                ),
                depletion_fraction=parameters.get(
                    "depletion_fraction", 0.50
                ),
                soil_properties=soil_properties,
            )

            forecast_records.append(result.record)

            previous_soil = result.record.soil_water
            nutrients = result.record.nutrients
            crop = result.record.crop

    return {
        "run_id": run.run_id,
        "provider": "Open-Meteo",
        "forecast_days": len(observations),
        "simulation_continuation_available": continuation_available,
        "continuation_note": (
            "Forecast-driven soil and crop simulation is available."
            if continuation_available
            else (
                "Weather forecast is available, but the historical "
                "simulation does not end immediately before the forecast. "
                "Current soil and crop conditions are therefore unknown; "
                "no future irrigation recommendation was calculated."
            )
        ),
        "weather": [
            {
                **asdict(observation),
                "precipitation_probability_max_pct": (
                    precipitation_probabilities.get(
                        observation.date.isoformat()
                    )
                ),
            }
            for observation in observations
        ],
        "simulation_records": [
            asdict(record) for record in forecast_records
        ],
    }
