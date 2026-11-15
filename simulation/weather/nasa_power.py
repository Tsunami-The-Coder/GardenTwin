from datetime import date
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from simulation.contracts import SimulationSite, WeatherObservation


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)

PARAMETERS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
]

MISSING_VALUE = -999


def _clean_value(value):
    """Convert NASA POWER missing values into None."""
    if value is None or value == MISSING_VALUE:
        return None

    return float(value)


def fetch_nasa_power_weather(
    site: SimulationSite,
    start_date: date,
    end_date: date,
    timeout: int = 30,
) -> list[WeatherObservation]:
    """
    Retrieve daily historical weather observations from NASA POWER.

    Temperatures: Celsius
    Precipitation: mm/day
    Relative humidity: %
    Wind speed: m/s
    Solar radiation: MJ/m²/day
    """

    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date")

    if timeout <= 0:
        raise ValueError("timeout must be positive")

    parameters = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": site.longitude,
        "latitude": site.latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }

    url = f"{NASA_POWER_URL}?{urlencode(parameters)}"

    request = Request(
        url,
        headers={"User-Agent": "GardenTwin/1.0"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

    except Exception as exc:
        raise RuntimeError(
            f"Failed to retrieve NASA POWER weather data: {exc}"
        ) from exc

    try:
        weather_data = payload["properties"]["parameter"]
    except (KeyError, TypeError):
        raise RuntimeError(
            "NASA POWER returned an unexpected response format."
        )

    observations = []

    dates = sorted(
        set().union(
            *(weather_data.get(parameter, {}).keys()
              for parameter in PARAMETERS)
        )
    )

    for date_string in dates:
        observation_date = date.fromisoformat(
            f"{date_string[:4]}-{date_string[4:6]}-{date_string[6:8]}"
        )

        def get(parameter):
            return _clean_value(
                weather_data.get(parameter, {}).get(date_string)
            )

        solar_mj = get("ALLSKY_SFC_SW_DWN")

        observation = WeatherObservation(
            date=observation_date,
            source="NASA POWER",
            temperature_mean_c=get("T2M"),
            temperature_min_c=get("T2M_MIN"),
            temperature_max_c=get("T2M_MAX"),
            precipitation_mm=get("PRECTOTCORR"),
            relative_humidity_pct=get("RH2M"),
            solar_radiation_mj_m2_day=solar_mj,
            wind_speed_2m_m_s=get("WS2M"),
        )

        observations.append(observation)

    # Fill an isolated one-day solar-radiation gap using linear
    # interpolation between the adjacent valid observations.
    for i, observation in enumerate(observations):
        if observation.solar_radiation_mj_m2_day is not None:
            continue

        if i == 0 or i == len(observations) - 1:
            continue

        previous = observations[i - 1]
        following = observations[i + 1]

        previous_solar = previous.solar_radiation_mj_m2_day
        following_solar = following.solar_radiation_mj_m2_day

        if (
            previous_solar is not None
            and following_solar is not None
            and (following.date - previous.date).days == 2
        ):
            observation.solar_radiation_mj_m2_day = (
                previous_solar + following_solar
            ) / 2

            observation.source = (
                "NASA POWER (solar radiation interpolated)"
            )

    _fill_missing_solar_from_open_meteo(
        site,
        observations,
        timeout=timeout,
    )

    return observations


def _fill_missing_solar_from_open_meteo(site, observations, timeout=30):
    """Fill missing NASA POWER weather fields using Open-Meteo."""

    import json
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    fields = {
        "temperature_min_c": "temperature_2m_min",
        "temperature_max_c": "temperature_2m_max",
        "precipitation_mm": "precipitation_sum",
        "relative_humidity_pct": "relative_humidity_2m_mean",
        "wind_speed_2m_m_s": "wind_speed_10m_mean",
        "solar_radiation_mj_m2_day": "shortwave_radiation_sum",
    }

    missing = [
        observation
        for observation in observations
        if any(
            getattr(observation, field) is None
            for field in fields
        )
    ]

    if not missing:
        return

    params = {
        "latitude": site.latitude,
        "longitude": site.longitude,
        "daily": ",".join(fields.values()),
        "past_days": 7,
        "forecast_days": 1,
        "timezone": "auto",
        "wind_speed_unit": "ms",
    }

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urlencode(params)
    )

    try:
        request = Request(
            url,
            headers={"User-Agent": "GardenTwin/1.0"},
        )

        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

    except Exception as exc:
        raise RuntimeError(
            f"Open-Meteo weather fallback failed: {exc}"
        ) from exc

    daily = payload.get("daily", {})
    dates = daily.get("time", [])

    fallback_by_date = {}

    for index, day in enumerate(dates):
        fallback_by_date[day] = {}

        for field, api_field in fields.items():
            values = daily.get(api_field, [])

            if index < len(values):
                fallback_by_date[day][field] = values[index]

    for observation in missing:
        values = fallback_by_date.get(observation.date.isoformat())

        if values is None:
            continue

        used_fallback = False

        for field in fields:
            current = getattr(observation, field)
            replacement = values.get(field)

            if current is None and replacement is not None:
                setattr(observation, field, float(replacement))
                used_fallback = True

        # Calculate mean temperature only if the observation
        # exposes that field and it is currently missing.
        if (
            hasattr(observation, "temperature_mean_c")
            and observation.temperature_mean_c is None
            and observation.temperature_min_c is not None
            and observation.temperature_max_c is not None
        ):
            observation.temperature_mean_c = (
                observation.temperature_min_c
                + observation.temperature_max_c
            ) / 2
            used_fallback = True

        if used_fallback:
            observation.source = (
                "NASA POWER + Open-Meteo weather fallback"
            )
