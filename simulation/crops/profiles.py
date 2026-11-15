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