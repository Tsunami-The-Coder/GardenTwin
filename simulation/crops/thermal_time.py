import math


def calculate_daily_gdd(
    temperature_min_c: float,
    temperature_max_c: float,
    base_temperature_c: float,
    upper_temperature_c: float | None = None,
) -> float:
    """
    Calculate daily growing degree days using the modified
    average-temperature method.

    Temperatures are in degrees Celsius.
    """

    values = [
        temperature_min_c,
        temperature_max_c,
        base_temperature_c,
    ]

    if upper_temperature_c is not None:
        values.append(upper_temperature_c)

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Temperatures must be finite.")

    if temperature_min_c > temperature_max_c:
        raise ValueError("Minimum temperature cannot exceed maximum.")

    if (
        upper_temperature_c is not None
        and upper_temperature_c <= base_temperature_c
    ):
        raise ValueError("Upper temperature must exceed base temperature.")

    effective_min = max(temperature_min_c, base_temperature_c)
    effective_max = max(temperature_max_c, base_temperature_c)

    if upper_temperature_c is not None:
        effective_min = min(effective_min, upper_temperature_c)
        effective_max = min(effective_max, upper_temperature_c)

    average_temperature = (effective_min + effective_max) / 2.0

    return max(0.0, average_temperature - base_temperature_c)


def accumulate_gdd(
    accumulated_gdd: float,
    daily_gdd: float,
) -> float:
    """Add today's GDD to the accumulated seasonal total."""

    if not math.isfinite(accumulated_gdd) or accumulated_gdd < 0:
        raise ValueError("Accumulated GDD must be finite and nonnegative.")

    if not math.isfinite(daily_gdd) or daily_gdd < 0:
        raise ValueError("Daily GDD must be finite and nonnegative.")

    return accumulated_gdd + daily_gdd
