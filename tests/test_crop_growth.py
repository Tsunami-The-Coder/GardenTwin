import pytest

from simulation.crops.growth import estimate_stress_adjusted_growth
from simulation.crops.growth import estimate_crop_growth
from simulation.crops.profiles import TOMATO_PROFILE


def test_growth_is_zero_at_planting():
    height, biomass = estimate_crop_growth(0, TOMATO_PROFILE)

    assert height == 0
    assert biomass == 0


def test_growth_increases_with_gdd():
    early = estimate_crop_growth(200, TOMATO_PROFILE)
    later = estimate_crop_growth(800, TOMATO_PROFILE)

    assert later[0] > early[0]
    assert later[1] > early[1]


def test_growth_reaches_configured_limits_at_maturity():
    height, biomass = estimate_crop_growth(1200, TOMATO_PROFILE)

    assert height == pytest.approx(TOMATO_PROFILE.max_height_cm)
    assert biomass == pytest.approx(
        TOMATO_PROFILE.mature_biomass_kg_ha
    )


def test_growth_does_not_exceed_maturity_limits():
    height, biomass = estimate_crop_growth(2000, TOMATO_PROFILE)

    assert height == pytest.approx(TOMATO_PROFILE.max_height_cm)
    assert biomass == pytest.approx(
        TOMATO_PROFILE.mature_biomass_kg_ha
    )


@pytest.mark.parametrize("gdd", [-1, float("nan"), float("inf")])
def test_invalid_gdd_is_rejected(gdd):
    with pytest.raises(ValueError):
        estimate_crop_growth(gdd, TOMATO_PROFILE)

def test_water_stress_reduces_daily_growth():
    normal = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 0.0, 0.0,
    )

    stressed = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 0.5, 0.0,
    )

    assert stressed[0] < normal[0]
    assert stressed[1] < normal[1]


def test_nutrient_stress_reduces_daily_growth():
    normal = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 0.0, 0.0,
    )

    stressed = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 0.0, 0.5,
    )

    assert stressed[0] < normal[0]
    assert stressed[1] < normal[1]


def test_unknown_nutrient_stress_keeps_health_unknown():
    result = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 0.2, None,
    )

    assert result[0] > 20
    assert result[1] > 1000
    assert result[2] is None


def test_maximum_stress_stops_daily_growth():
    result = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 1.0, 0.0,
    )

    assert result[0] == 20
    assert result[1] == 1000
    assert result[2] == 0.0


def test_stress_only_affects_new_growth():
    result = estimate_stress_adjusted_growth(
        200, 300, 20, 1000,
        TOMATO_PROFILE, 1.0, 1.0,
    )

    assert result[0] == 20
    assert result[1] == 1000
