from simulation.crops.profiles import (
    TOMATO_PROFILE,
    GrowthStage,
    determine_growth_stage,
)
from simulation.crops.thermal_time import (
    calculate_daily_gdd,
    accumulate_gdd,
)


def test_daily_gdd_calculation():
    result = calculate_daily_gdd(
        temperature_min_c=15,
        temperature_max_c=25,
        base_temperature_c=10,
        upper_temperature_c=30,
    )

    assert result == 10


def test_daily_gdd_respects_base_temperature():
    result = calculate_daily_gdd(
        temperature_min_c=5,
        temperature_max_c=9,
        base_temperature_c=10,
        upper_temperature_c=30,
    )

    assert result == 0


def test_daily_gdd_respects_upper_temperature():
    result = calculate_daily_gdd(
        temperature_min_c=30,
        temperature_max_c=40,
        base_temperature_c=10,
        upper_temperature_c=30,
    )

    assert result == 20


def test_gdd_accumulation():
    result = accumulate_gdd(100, 25)

    assert result == 125


def test_tomato_starts_in_planted_stage():
    stage = determine_growth_stage(0, TOMATO_PROFILE)

    assert stage == GrowthStage.PLANTED


def test_tomato_reaches_emergence():
    stage = determine_growth_stage(50, TOMATO_PROFILE)

    assert stage == GrowthStage.EMERGENCE


def test_tomato_reaches_vegetative_stage():
    stage = determine_growth_stage(200, TOMATO_PROFILE)

    assert stage == GrowthStage.VEGETATIVE


def test_tomato_reaches_maturity():
    stage = determine_growth_stage(1200, TOMATO_PROFILE)

    assert stage == GrowthStage.MATURITY
