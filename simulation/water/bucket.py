
from dataclasses import dataclass
from math import isfinite

from simulation.contracts import SoilWaterState
from simulation.water.soil_properties import SoilHydraulicProperties


@dataclass
class WaterBalanceResult:
    soil_water: SoilWaterState
    potential_crop_et_mm: float
    actual_crop_et_mm: float
    effective_irrigation_mm: float
    drainage_mm: float
    water_stress_index: float
    irrigation_recommendation_mm: float


def validate_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


def calculate_water_stress(
    depletion_mm: float,
    total_available_water_mm: float,
    depletion_fraction: float,
) -> float:
    """
    Calculate a simplified FAO-56 crop water stress coefficient.

    Returns:
        0.0 = maximum water stress
        1.0 = no water stress
    """

    if total_available_water_mm <= 0:
        raise ValueError("Available water capacity must be positive.")

    if not 0 < depletion_fraction < 1:
        raise ValueError("Depletion fraction must be between 0 and 1.")

    raw = depletion_fraction * total_available_water_mm

    if depletion_mm <= raw:
        return 1.0

    remaining_fraction = (
        total_available_water_mm - depletion_mm
    ) / (
        total_available_water_mm - raw
    )

    return max(0.0, min(1.0, remaining_fraction))


def simulate_water_balance(
    soil: SoilWaterState,
    precipitation_mm: float,
    reference_et_mm: float,
    crop_coefficient: float,
    irrigation_mm: float = 0.0,
    irrigation_efficiency: float = 0.90,
    depletion_fraction: float = 0.50,
    soil_properties: SoilHydraulicProperties | None = None,
) -> WaterBalanceResult:
    """
    Simulate one day's root-zone water balance.

    When soil_properties is supplied:
    - Water may temporarily remain above field capacity.
    - Water cannot exceed saturation.
    - Drainage depends on saturated hydraulic conductivity.
    - Water below wilting point cannot be extracted by the crop.

    Without soil_properties, the legacy instantaneous-drainage
    behavior is retained for compatibility with existing callers.
    """

    validate_nonnegative("Precipitation", precipitation_mm)
    validate_nonnegative("Reference ET", reference_et_mm)
    validate_nonnegative("Crop coefficient", crop_coefficient)
    validate_nonnegative("Irrigation", irrigation_mm)

    if not 0 < irrigation_efficiency <= 1:
        raise ValueError("Irrigation efficiency must be in (0, 1].")

    if not 0 < depletion_fraction < 1:
        raise ValueError("Depletion fraction must be between 0 and 1.")

    if (
        soil.root_zone_water_mm is None
        or soil.field_capacity_mm is None
        or soil.wilting_point_mm is None
    ):
        raise ValueError("Soil-water parameters are incomplete.")

    if not (
        soil.wilting_point_mm < soil.field_capacity_mm
    ):
        raise ValueError("Field capacity must exceed wilting point.")

    if soil_properties is not None:
        tolerance = 1e-6

        if (
            abs(soil_properties.field_capacity_mm - soil.field_capacity_mm)
            > tolerance
            or abs(soil_properties.wilting_point_mm - soil.wilting_point_mm)
            > tolerance
        ):
            raise ValueError(
                "Soil hydraulic properties do not match the soil-water state."
            )

        maximum_water = soil_properties.saturation_mm

        if not (
            soil.wilting_point_mm
            <= soil.root_zone_water_mm
            <= maximum_water
        ):
            raise ValueError(
                "Root-zone water must be between wilting point and saturation."
            )
    else:
        maximum_water = soil.field_capacity_mm

        if not (
            soil.wilting_point_mm
            <= soil.root_zone_water_mm
            <= soil.field_capacity_mm
        ):
            raise ValueError(
                "Root-zone water must be between wilting point "
                "and field capacity when hydraulic properties are absent."
            )

    total_available_water = (
        soil.field_capacity_mm - soil.wilting_point_mm
    )

    potential_et = reference_et_mm * crop_coefficient
    effective_irrigation = irrigation_mm * irrigation_efficiency

    incoming_water = (
        soil.root_zone_water_mm
        + precipitation_mm
        + effective_irrigation
    )

    if soil_properties is None:
        # Legacy behavior, retained until all callers pass soil properties.
        drainage = max(
            0.0,
            incoming_water - soil.field_capacity_mm,
        )
        water_before_et = min(
            incoming_water,
            soil.field_capacity_mm,
        )
    else:
        # Water exceeding saturation cannot be stored.
        overflow = max(0.0, incoming_water - maximum_water)

        water_before_drainage = min(
            incoming_water,
            maximum_water,
        )

        excess_above_field_capacity = max(
            0.0,
            water_before_drainage - soil.field_capacity_mm,
        )

        hydraulic_drainage = soil_properties.calculate_drainage(
            water_above_field_capacity_mm=excess_above_field_capacity,
            water_content_mm=water_before_drainage,
        )

        drainage = overflow + hydraulic_drainage

        water_before_et = (
            water_before_drainage - hydraulic_drainage
        )

    depletion = soil.field_capacity_mm - water_before_et

    stress_coefficient = calculate_water_stress(
        depletion,
        total_available_water,
        depletion_fraction,
    )

    actual_et = min(
        potential_et * stress_coefficient,
        max(0.0, water_before_et - soil.wilting_point_mm),
    )

    new_water = max(
        soil.wilting_point_mm,
        water_before_et - actual_et,
    )

    end_depletion = soil.field_capacity_mm - new_water

    end_stress_coefficient = calculate_water_stress(
        end_depletion,
        total_available_water,
        depletion_fraction,
    )

    stress_index = 1.0 - end_stress_coefficient

    raw = depletion_fraction * total_available_water

    if end_depletion > raw:
        net_irrigation_needed = (
            soil.field_capacity_mm - new_water
        )

        irrigation_recommendation = (
            net_irrigation_needed / irrigation_efficiency
        )
    else:
        irrigation_recommendation = 0.0

    updated_soil = SoilWaterState(
        root_zone_water_mm=new_water,
        field_capacity_mm=soil.field_capacity_mm,
        wilting_point_mm=soil.wilting_point_mm,
        root_depth_cm=soil.root_depth_cm,
        water_stress_index=stress_index,
    )

    return WaterBalanceResult(
        soil_water=updated_soil,
        potential_crop_et_mm=potential_et,
        actual_crop_et_mm=actual_et,
        effective_irrigation_mm=effective_irrigation,
        drainage_mm=drainage,
        water_stress_index=stress_index,
        irrigation_recommendation_mm=irrigation_recommendation,
    )
