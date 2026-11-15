from datetime import date
from math import (
    acos,
    cos,
    exp,
    isfinite,
    pi,
    sin,
    sqrt,
    tan,
)


def saturation_vapor_pressure(temperature_c: float) -> float:
    """Saturation vapor pressure in kPa."""
    return 0.6108 * exp(
        (17.27 * temperature_c) / (temperature_c + 237.3)
    )


def calculate_reference_et(
    observation_date: date,
    temperature_min_c: float,
    temperature_max_c: float,
    relative_humidity_percent: float,
    solar_radiation_mj_m2_day: float,
    wind_speed_2m_m_s: float,
    latitude_degrees: float,
    elevation_m: float = 0.0,
) -> float:
    """
    Calculate daily reference evapotranspiration (ETo)
    using the FAO-56 Penman-Monteith equation.

    Returns:
        ETo in millimeters per day.

    Assumes:
        - Relative humidity is daily mean RH.
        - Wind speed is measured or adjusted to 2 meters.
        - Solar radiation is daily incoming solar radiation.
        - Daily soil heat flux is approximately zero.
    """

    values = {
        "minimum temperature": temperature_min_c,
        "maximum temperature": temperature_max_c,
        "relative humidity": relative_humidity_percent,
        "solar radiation": solar_radiation_mj_m2_day,
        "wind speed": wind_speed_2m_m_s,
        "latitude": latitude_degrees,
        "elevation": elevation_m,
    }

    for name, value in values.items():
        if not isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if temperature_min_c > temperature_max_c:
        raise ValueError("Minimum temperature exceeds maximum.")

    if not 0 <= relative_humidity_percent <= 100:
        raise ValueError("Relative humidity must be between 0 and 100.")

    if solar_radiation_mj_m2_day < 0:
        raise ValueError("Solar radiation cannot be negative.")

    if wind_speed_2m_m_s < 0:
        raise ValueError("Wind speed cannot be negative.")

    if not -90 <= latitude_degrees <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if elevation_m < -500 or elevation_m > 9000:
        raise ValueError("Elevation is outside the supported range.")

    # Convert latitude to radians.
    latitude = latitude_degrees * pi / 180

    # Day of year.
    day_number = observation_date.timetuple().tm_yday

    # Mean temperature.
    temperature_mean = (
        temperature_min_c + temperature_max_c
    ) / 2

    # Saturation vapor pressure.
    es_min = saturation_vapor_pressure(temperature_min_c)
    es_max = saturation_vapor_pressure(temperature_max_c)
    es = (es_min + es_max) / 2

    # Actual vapor pressure, estimated from daily mean RH.
    ea = es * relative_humidity_percent / 100

    # Slope of saturation vapor pressure curve.
    delta = (
        4098 * saturation_vapor_pressure(temperature_mean)
        / (temperature_mean + 237.3) ** 2
    )

    # Atmospheric pressure and psychrometric constant.
    pressure = (
        101.3
        * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
    )
    gamma = 0.000665 * pressure

    # Extraterrestrial radiation.
    inverse_distance = (
        1 + 0.033 * cos(2 * pi * day_number / 365)
    )

    solar_declination = (
        0.409 * sin(2 * pi * day_number / 365 - 1.39)
    )

    sunset_argument = -tan(latitude) * tan(solar_declination)
    sunset_argument = max(-1.0, min(1.0, sunset_argument))
    sunset_hour_angle = acos(sunset_argument)

    extraterrestrial_radiation = (
        (24 * 60 / pi)
        * 0.0820
        * inverse_distance
        * (
            sunset_hour_angle
            * sin(latitude)
            * sin(solar_declination)
            + cos(latitude)
            * cos(solar_declination)
            * sin(sunset_hour_angle)
        )
    )

    # Clear-sky solar radiation.
    clear_sky_radiation = (
        0.75 + 2e-5 * elevation_m
    ) * extraterrestrial_radiation

    # Net shortwave radiation.
    net_shortwave = (
        (1 - 0.23) * solar_radiation_mj_m2_day
    )

    # Net longwave radiation.
    if clear_sky_radiation > 0:
        radiation_ratio = (
            solar_radiation_mj_m2_day
            / clear_sky_radiation
        )
        radiation_ratio = max(
            0.3, min(1.0, radiation_ratio)
        )
    else:
        radiation_ratio = 0.3

    sigma = 4.903e-9

    longwave_factor = (
        0.34 - 0.14 * sqrt(max(ea, 0.0))
    ) * (1.35 * radiation_ratio - 0.35)

    net_longwave = (
        sigma
        * (
            ((temperature_max_c + 273.16) ** 4
             + (temperature_min_c + 273.16) ** 4)
            / 2
        )
        * longwave_factor
    )

    net_radiation = net_shortwave - net_longwave

    # Daily soil heat flux is assumed to be zero.
    soil_heat_flux = 0.0

    # FAO-56 Penman-Monteith equation.
    numerator = (
        0.408 * delta * (net_radiation - soil_heat_flux)
        + gamma
        * (900 / (temperature_mean + 273))
        * wind_speed_2m_m_s
        * (es - ea)
    )

    denominator = (
        delta
        + gamma * (1 + 0.34 * wind_speed_2m_m_s)
    )

    eto = numerator / denominator

    # Negative daily reference ET is not physically meaningful.
    return max(0.0, eto)
