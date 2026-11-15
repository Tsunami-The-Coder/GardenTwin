from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SimulationRequest(BaseModel):
    location_name: str = "My Garden"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    crop_name: str = "Tomato"

    planting_date: date
    start_date: date
    end_date: date

    crop_coefficient: float = Field(default=1.0, gt=0, le=2)

    # Soil source:
    # auto = try SSURGO, then fall back to manual values
    # ssurgo = require a successful SSURGO lookup
    # manual = use the values below without making an online lookup
    soil_mode: Literal["auto", "ssurgo", "manual"] = "auto"

    # Manual fallback values; also used when soil_mode="manual".
    wilting_point: float = Field(default=0.12, ge=0)
    field_capacity: float = Field(default=0.30, gt=0)
    saturation: float = Field(default=0.45, gt=0)

    saturated_hydraulic_conductivity_mm_day: float = Field(
        default=10.0,
        ge=0,
    )

    root_depth_cm: float = Field(default=30.0, gt=0)
    initial_water_content: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_dates_and_soil(self):
        if self.planting_date > self.start_date:
            raise ValueError("Planting date cannot follow simulation start.")

        if self.start_date > self.end_date:
            raise ValueError("Start date cannot follow simulation end.")

        if (self.end_date - self.start_date).days > 365:
            raise ValueError("Simulation cannot exceed 366 days.")

        if not (
            0 <= self.wilting_point
            < self.field_capacity
            < self.saturation
        ):
            raise ValueError(
                "Soil values must satisfy wilting point < "
                "field capacity < saturation."
            )

        if (
            self.initial_water_content is not None
            and self.initial_water_content > self.saturation
        ):
            raise ValueError(
                "Initial water content cannot exceed soil saturation."
            )

        return self
