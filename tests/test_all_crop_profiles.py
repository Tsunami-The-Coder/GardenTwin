import pytest

from simulation.crops.profiles import (
    CROP_PROFILES,
    get_crop_profile,
    determine_growth_stage,
    GrowthStage,
)


EXPECTED_CROPS = {
    "tomato",
    "pepper",
    "cucumber",
    "lettuce",
    "carrot",
    "bean",
    "strawberry",
}


def test_all_seven_crops_are_registered():
    assert set(CROP_PROFILES) == EXPECTED_CROPS


@pytest.mark.parametrize("crop_name", sorted(EXPECTED_CROPS))
def test_each_crop_has_valid_growth_parameters(crop_name):
    profile = get_crop_profile(crop_name)

    assert profile.crop_id == crop_name
    assert profile.base_temperature_c < profile.upper_temperature_c
    assert profile.max_height_cm > 0
    assert profile.mature_biomass_kg_ha > 0
    assert len(profile.stage_thresholds) == 6


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("tomatoes", "tomato"),
        ("bell peppers", "pepper"),
        ("peppers", "pepper"),
        ("cucumbers", "cucumber"),
        ("lettuces", "lettuce"),
        ("carrots", "carrot"),
        ("beans", "bean"),
        ("green beans", "bean"),
        ("strawberries", "strawberry"),
    ],
)
def test_crop_aliases(alias, expected):
    assert get_crop_profile(alias).crop_id == expected


@pytest.mark.parametrize("crop_name", sorted(EXPECTED_CROPS))
def test_each_crop_reaches_maturity(crop_name):
    profile = get_crop_profile(crop_name)
    maturity_gdd = profile.stage_thresholds[-1].accumulated_gdd

    assert (
        determine_growth_stage(maturity_gdd, profile)
        == GrowthStage.MATURITY
    )


def test_unsupported_crop_is_rejected():
    with pytest.raises(ValueError, match="Unsupported crop"):
        get_crop_profile("pineapple")
