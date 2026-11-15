
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SoilHydraulicProperties:
    """
    Hydraulic properties for a simplified, uniform soil layer.

    Water contents are volumetric fractions (m3/m3).
    Hydraulic conductivity is expressed in mm/day.

    Nutrient mobility coefficients are simplified demo parameters,
    not calibrated soil-specific measurements.
    """

    wilting_point: float
    field_capacity: float
    saturation: float
    saturated_hydraulic_conductivity_mm_day: float
    root_depth_cm: float

    nitrogen_mobility: float = 1.0
    phosphorus_mobility: float = 0.05
    potassium_mobility: float = 0.30

    def __post_init__(self):
        values = (
            self.wilting_point,
            self.field_capacity,
            self.saturation,
            self.saturated_hydraulic_conductivity_mm_day,
            self.root_depth_cm,
            self.nitrogen_mobility,
            self.phosphorus_mobility,
            self.potassium_mobility,
        )

        if not all(math.isfinite(value) for value in values):
            raise ValueError("All soil properties must be finite.")

        if not 0 <= self.wilting_point < self.field_capacity:
            raise ValueError(
                "Wilting point must be nonnegative and below field capacity."
            )

        if self.field_capacity >= self.saturation:
            raise ValueError("Field capacity must be below saturation.")

        if self.saturated_hydraulic_conductivity_mm_day < 0:
            raise ValueError("Hydraulic conductivity cannot be negative.")

        if self.root_depth_cm <= 0:
            raise ValueError("Root depth must be positive.")

        if any(
            value < 0
            for value in (
                self.nitrogen_mobility,
                self.phosphorus_mobility,
                self.potassium_mobility,
            )
        ):
            raise ValueError("Nutrient mobility coefficients cannot be negative.")

    def water_content_to_mm(self, water_content: float) -> float:
        """Convert volumetric water content into water depth in mm."""

        if not math.isfinite(water_content):
            raise ValueError("Water content must be finite.")

        if not 0 <= water_content <= self.saturation:
            raise ValueError(
                "Water content must be between zero and saturation."
            )

        return water_content * self.root_depth_cm * 10

    @property
    def wilting_point_mm(self) -> float:
        return self.water_content_to_mm(self.wilting_point)

    @property
    def field_capacity_mm(self) -> float:
        return self.water_content_to_mm(self.field_capacity)

    @property
    def saturation_mm(self) -> float:
        return self.water_content_to_mm(self.saturation)

    def calculate_drainage(
        self,
        water_above_field_capacity_mm: float,
        water_content_mm: float,
    ) -> float:
        """
        Estimate daily drainage using saturated hydraulic conductivity.

        A simplified cubic relative-saturation relationship reduces
        conductivity as the soil becomes less saturated.

        Drainage cannot exceed either the excess water or the
        estimated daily hydraulic conductivity.
        """

        if (
            not math.isfinite(water_above_field_capacity_mm)
            or water_above_field_capacity_mm < 0
        ):
            raise ValueError("Excess water must be finite and nonnegative.")

        if (
            not math.isfinite(water_content_mm)
            or not self.wilting_point_mm <= water_content_mm <= self.saturation_mm
        ):
            raise ValueError("Water content is outside the soil's valid range.")

        available_pore_space = (
            self.saturation_mm - self.field_capacity_mm
        )

        if available_pore_space <= 0 or water_above_field_capacity_mm == 0:
            return 0.0

        relative_saturation = (
            water_content_mm - self.field_capacity_mm
        ) / available_pore_space

        relative_saturation = max(0.0, min(1.0, relative_saturation))

        effective_conductivity = (
            self.saturated_hydraulic_conductivity_mm_day
            * relative_saturation ** 3
        )

        return min(
            water_above_field_capacity_mm,
            effective_conductivity,
        )

    def calculate_leaching_fraction(
        self,
        drainage_mm: float,
        root_zone_water_mm: float,
        nutrient_mobility: float,
    ) -> float:
        """
        Estimate a nutrient-specific leaching fraction.

        This is a simplified drainage-coupled approximation.
        Mobility coefficients require future calibration.
        """

        values = (
            drainage_mm,
            root_zone_water_mm,
            nutrient_mobility,
        )

        if not all(math.isfinite(value) for value in values):
            raise ValueError("Leaching inputs must be finite.")

        if drainage_mm < 0 or root_zone_water_mm < 0:
            raise ValueError("Water quantities cannot be negative.")

        if nutrient_mobility < 0:
            raise ValueError("Nutrient mobility cannot be negative.")

        if drainage_mm == 0 or root_zone_water_mm == 0:
            return 0.0

        fraction = 1.0 - math.exp(
            -nutrient_mobility * drainage_mm / root_zone_water_mm
        )

        return max(0.0, min(1.0, fraction))
