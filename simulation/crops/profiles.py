from dataclasses import dataclass
from enum import Enum
import math


class GrowthStage(str, Enum):
    PLANTED = "planted"
    EMERGENCE = "emergence"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUIT_DEVELOPMENT = "fruit_development"
    MATURITY = "maturity"


@dataclass(frozen=True)
class GrowthStageThreshold:
    stage: GrowthStage
    accumulated_gdd: float

    def __post_init__(self):
        if not math.isfinite(self.accumulated_gdd):
            raise ValueError("GDD threshold must be finite.")

        if self.accumulated_gdd < 0:
            raise ValueError("GDD threshold cannot be negative.")


@dataclass(frozen=True)
class CropProfile:
    crop_id: str
    common_name: str
    scientific_name: str

    base_temperature_c: float
    upper_temperature_c: float

    stage_thresholds: tuple[GrowthStageThreshold, ...]
    max_height_cm: float = 180.0
    mature_biomass_kg_ha: float = 12000.0
    height_growth_exponent: float = 0.75
    biomass_growth_exponent: float = 1.5

    def __post_init__(self):
        if not self.crop_id.strip():
            raise ValueError("Crop ID cannot be empty.")

        if not self.common_name.strip():
            raise ValueError("Common name cannot be empty.")

        if not self.scientific_name.strip():
            raise ValueError("Scientific name cannot be empty.")

        if not math.isfinite(self.base_temperature_c):
            raise ValueError("Base temperature must be finite.")

        if not math.isfinite(self.upper_temperature_c):
            raise ValueError("Upper temperature must be finite.")

        if self.upper_temperature_c <= self.base_temperature_c:
            raise ValueError(
                "Upper temperature must exceed base temperature."
            )

        if not self.stage_thresholds:
            raise ValueError("At least one stage threshold is required.")

        if self.stage_thresholds[0].stage != GrowthStage.PLANTED:
            raise ValueError("The first growth stage must be PLANTED.")

        if self.stage_thresholds[0].accumulated_gdd != 0:
            raise ValueError("PLANTED must begin at 0 GDD.")

        previous_threshold = -1.0
        seen_stages = set()

        for threshold in self.stage_thresholds:
            if threshold.accumulated_gdd <= previous_threshold:
                raise ValueError(
                    "Growth-stage thresholds must be strictly increasing."
                )

            if threshold.stage in seen_stages:
                raise ValueError("Growth stages cannot be repeated.")

            previous_threshold = threshold.accumulated_gdd
            seen_stages.add(threshold.stage)

        if len(self.stage_thresholds) < 2:
            raise ValueError(
                "At least two growth-stage thresholds are required."
            )

        growth_parameters = (
            self.max_height_cm,
            self.mature_biomass_kg_ha,
            self.height_growth_exponent,
            self.biomass_growth_exponent,
        )

        if not all(math.isfinite(value) for value in growth_parameters):
            raise ValueError("Growth parameters must be finite.")

        if any(value <= 0 for value in growth_parameters):
            raise ValueError("Growth parameters must be positive.")


def determine_growth_stage(
    accumulated_gdd: float,
    profile: CropProfile,
) -> GrowthStage:
    """Return the latest growth stage reached at the given GDD."""

    if not math.isfinite(accumulated_gdd) or accumulated_gdd < 0:
        raise ValueError(
            "Accumulated GDD must be finite and nonnegative."
        )

    current_stage = GrowthStage.PLANTED

    for threshold in profile.stage_thresholds:
        if accumulated_gdd >= threshold.accumulated_gdd:
            current_stage = threshold.stage
        else:
            break

    return current_stage

TOMATO_PROFILE = CropProfile(
    crop_id="tomato",
    common_name="Tomato",
    scientific_name="Solanum lycopersicum",
    base_temperature_c=10.0,
    upper_temperature_c=30.0,
    stage_thresholds=(
        GrowthStageThreshold(GrowthStage.PLANTED, 0),
        GrowthStageThreshold(GrowthStage.EMERGENCE, 50),
        GrowthStageThreshold(GrowthStage.VEGETATIVE, 200),
        GrowthStageThreshold(GrowthStage.FLOWERING, 500),
        GrowthStageThreshold(GrowthStage.FRUIT_DEVELOPMENT, 800),
        GrowthStageThreshold(GrowthStage.MATURITY, 1200),
    ),
)

def _stages(emergence, vegetative, flowering, development, maturity):
    return (
        GrowthStageThreshold(GrowthStage.PLANTED, 0),
        GrowthStageThreshold(GrowthStage.EMERGENCE, emergence),
        GrowthStageThreshold(GrowthStage.VEGETATIVE, vegetative),
        GrowthStageThreshold(GrowthStage.FLOWERING, flowering),
        GrowthStageThreshold(GrowthStage.FRUIT_DEVELOPMENT, development),
        GrowthStageThreshold(GrowthStage.MATURITY, maturity),
    )


PEPPER_PROFILE = CropProfile(
    crop_id="pepper",
    common_name="Pepper",
    scientific_name="Capsicum annuum",
    base_temperature_c=10.0,
    upper_temperature_c=30.0,
    stage_thresholds=_stages(60, 220, 650, 950, 1500),
    max_height_cm=90,
    mature_biomass_kg_ha=18000,
)

CUCUMBER_PROFILE = CropProfile(
    crop_id="cucumber",
    common_name="Cucumber",
    scientific_name="Cucumis sativus",
    base_temperature_c=12.0,
    upper_temperature_c=32.0,
    stage_thresholds=_stages(40, 160, 300, 450, 850),
    max_height_cm=60,
    mature_biomass_kg_ha=20000,
)

LETTUCE_PROFILE = CropProfile(
    crop_id="lettuce",
    common_name="Lettuce",
    scientific_name="Lactuca sativa",
    base_temperature_c=4.0,
    upper_temperature_c=24.0,
    stage_thresholds=_stages(35, 100, 250, 350, 550),
    max_height_cm=30,
    mature_biomass_kg_ha=15000,
)

CARROT_PROFILE = CropProfile(
    crop_id="carrot",
    common_name="Carrot",
    scientific_name="Daucus carota",
    base_temperature_c=4.0,
    upper_temperature_c=30.0,
    stage_thresholds=_stages(80, 220, 450, 650, 1100),
    max_height_cm=35,
    mature_biomass_kg_ha=45000,
)

BEAN_PROFILE = CropProfile(
    crop_id="bean",
    common_name="Bean",
    scientific_name="Phaseolus vulgaris",
    base_temperature_c=8.0,
    upper_temperature_c=30.0,
    stage_thresholds=_stages(50, 180, 350, 550, 950),
    max_height_cm=50,
    mature_biomass_kg_ha=8000,
)

STRAWBERRY_PROFILE = CropProfile(
    crop_id="strawberry",
    common_name="Strawberry",
    scientific_name="Fragaria × ananassa",
    base_temperature_c=5.0,
    upper_temperature_c=26.0,
    stage_thresholds=_stages(70, 220, 450, 650, 1000),
    max_height_cm=25,
    mature_biomass_kg_ha=12000,
)


CROP_PROFILES = {
    profile.crop_id: profile
    for profile in (
        TOMATO_PROFILE,
        PEPPER_PROFILE,
        CUCUMBER_PROFILE,
        LETTUCE_PROFILE,
        CARROT_PROFILE,
        BEAN_PROFILE,
        STRAWBERRY_PROFILE,
    )
}


CROP_ALIASES = {
    "tomatoes": "tomato",
    "bell pepper": "pepper",
    "bell peppers": "pepper",
    "peppers": "pepper",
    "cucumbers": "cucumber",
    "lettuces": "lettuce",
    "carrots": "carrot",
    "beans": "bean",
    "green bean": "bean",
    "green beans": "bean",
    "strawberries": "strawberry",
}


def get_crop_profile(crop_name: str) -> CropProfile:
    """Return a registered crop profile by name or alias."""

    if not isinstance(crop_name, str) or not crop_name.strip():
        raise ValueError("Crop name must be a nonempty string.")

    normalized = " ".join(
        crop_name.lower()
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )

    crop_id = CROP_ALIASES.get(normalized, normalized)

    try:
        return CROP_PROFILES[crop_id]
    except KeyError:
        supported = ", ".join(sorted(CROP_PROFILES))
        raise ValueError(
            f"Unsupported crop '{crop_name}'. "
            f"Supported crops: {supported}"
        ) from None
