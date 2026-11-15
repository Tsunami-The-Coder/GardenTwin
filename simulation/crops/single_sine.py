import math


def calculate_single_sine_gdd(
    temperature_min_c: float,
    temperature_max_c: float,
    base_temperature_c: float,
    upper_temperature_c: float,
) -> float:
    """
    Calculate daily growing degree days using a single-sine curve
    with horizontal lower and upper cutoffs.

    Returns degree-days in Celsius units.
    """
    values = (
        temperature_min_c,
        temperature_max_c,
        base_temperature_c,
        upper_temperature_c,
    )

    if not all(math.isfinite(value) for value in values):
        raise ValueError("All temperatures must be finite.")

    if temperature_min_c > temperature_max_c:
        raise ValueError("Minimum temperature cannot exceed maximum.")

    if upper_temperature_c <= base_temperature_c:
        raise ValueError("Upper threshold must exceed base temperature.")

    mean_temp = (temperature_min_c + temperature_max_c) / 2
    amplitude = (temperature_max_c - temperature_min_c) / 2

    # A constant temperature has no daily temperature variation.
    if amplitude == 0:
        return max(
            0.0,
            min(mean_temp, upper_temperature_c) - base_temperature_c,
        )

    # Find all points where the sine curve crosses either cutoff.
    boundaries = [0.0, 2 * math.pi]

    for threshold in (base_temperature_c, upper_temperature_c):
        ratio = (threshold - mean_temp) / amplitude

        if -1.0 < ratio < 1.0:
            angle = math.asin(ratio)

            boundaries.append(angle % (2 * math.pi))
            boundaries.append((math.pi - angle) % (2 * math.pi))

    boundaries.sort()

    total_heat = 0.0

    # Integrate each section analytically.
    for start, end in zip(boundaries, boundaries[1:]):
        if end <= start:
            continue

        midpoint = (start + end) / 2
        midpoint_temp = mean_temp + amplitude * math.sin(midpoint)

        if midpoint_temp <= base_temperature_c:
            continue

        if midpoint_temp >= upper_temperature_c:
            total_heat += (
                upper_temperature_c - base_temperature_c
            ) * (end - start)
        else:
            total_heat += (
                (mean_temp - base_temperature_c) * (end - start)
                - amplitude * (math.cos(end) - math.cos(start))
            )

    return max(0.0, total_heat / (2 * math.pi))
