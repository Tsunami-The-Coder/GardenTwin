"""Shared data contracts for GardenTwin.

All simulation components use these structures so the backend and
eventual web frontend receive consistent, date-aligned information.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class RecommendationStatus(str, Enum):
    APPLY = "apply"
    NONE = "none"
    UNKNOWN = "unknown"


@dataclass
class WeatherObservation:
    date: date
    source: str

    temperature_mean_c: Optional[float] = None
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    precipitation_mm: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    solar_radiation_mj_m2_day: Optional[float] = None
    wind_speed_2m_m_s: Optional[float] = None

    def __post_init__(self):
        if self.precipitation_mm is not None and self.precipitation_mm < 0:
            raise ValueError("Precipitation cannot be negative.")

        if self.relative_humidity_pct is not None:
            if not 0 <= self.relative_humidity_pct <= 100:
                raise ValueError("Relative humidity must be between 0 and 100.")

        if (
            self.temperature_min_c is not None
            and self.temperature_max_c is not None
            and self.temperature_min_c > self.temperature_max_c
        ):
            raise ValueError("Minimum temperature exceeds maximum temperature.")


@dataclass
class SoilWaterState:
    root_zone_water_mm: Optional[float] = None
    field_capacity_mm: Optional[float] = None
    wilting_point_mm: Optional[float] = None
    root_depth_cm: Optional[float] = None

    # 0 = no water stress; 1 = maximum modeled water stress.
    water_stress_index: Optional[float] = None


@dataclass
class NutrientState:
    # Available nutrient estimates, expressed as kg per hectare.
    nitrogen_available_kg_ha: Optional[float] = None
    phosphorus_available_kg_ha: Optional[float] = None
    potassium_available_kg_ha: Optional[float] = None

    # 0 = no modeled nutrient stress; 1 = maximum modeled stress.
    nutrient_stress_index: Optional[float] = None

    soil_test_available: bool = False


@dataclass
class CropState:
    crop_name: str
    growth_stage: str
    days_after_planting: int

    accumulated_gdd: float = 0.0

    height_cm: Optional[float] = None
    biomass_kg_ha: Optional[float] = None
    estimated_yield_kg_ha: Optional[float] = None

    # 0 = poor modeled condition; 1 = optimal modeled condition.
    health_index: Optional[float] = None


@dataclass
class IrrigationRecommendation:
    status: RecommendationStatus

    # Irrigation depth over the growing area.
    amount_mm: Optional[float] = None

    # Optional conversion for a plant with known growing-area allocation.
    liters_per_plant: Optional[float] = None

    reason: str = ""
    confidence: Optional[float] = None


@dataclass
class FertilizerRecommendation:
    status: RecommendationStatus

    # Recommended nutrient quantities, not fertilizer product weights.
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None

    # Estimated daily crop uptake, NOT fertilizer application rates.
    estimated_daily_n_demand_kg_ha: Optional[float] = None
    estimated_daily_p_demand_kg_ha: Optional[float] = None
    estimated_daily_k_demand_kg_ha: Optional[float] = None

    product_name: Optional[str] = None
    product_amount_g_per_plant: Optional[float] = None
    reason: str = ""
    confidence: Optional[float] = None


@dataclass
class DailySimulationRecord:
    date: date
    weather: WeatherObservation
    soil_water: SoilWaterState
    nutrients: NutrientState
    crop: CropState
    irrigation: IrrigationRecommendation
    fertilizer: FertilizerRecommendation

    alerts: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.weather.date != self.date:
            raise ValueError("Weather and simulation dates must match.")

        for index in (
            self.soil_water.water_stress_index,
            self.nutrients.nutrient_stress_index,
            self.crop.health_index,
            self.irrigation.confidence,
            self.fertilizer.confidence,
        ):
            if index is not None and not 0 <= index <= 1:
                raise ValueError("Indices and confidence values must be 0–1.")

        if self.crop.days_after_planting < 0:
            raise ValueError("Days after planting cannot be negative.")


@dataclass
class SimulationSite:
    site_id: str
    latitude: float
    longitude: float
    location_name: str = ""

    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Invalid latitude.")

        if not -180 <= self.longitude <= 180:
            raise ValueError("Invalid longitude.")



@dataclass
class SimulationRun:
    run_id: str
    site: SimulationSite
    crop_name: str
    planting_date: date
    start_date: date
    end_date: date
    records: list[DailySimulationRecord] = field(default_factory=list)

    # Soil data provenance for the API/frontend.
    soil_data_source: str = "Manual user inputs"
    soil_map_unit_key: str | None = None
    soil_map_unit_name: str | None = None
    soil_component_name: str | None = None
    soil_lookup_note: str | None = None
    soil_properties: dict[str, float] = field(default_factory=dict)
    simulation_parameters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("Simulation start date must precede end date.")

        if self.planting_date > self.start_date:
            raise ValueError("Planting date cannot follow simulation start.")

        dates = [record.date for record in self.records]

        if len(dates) != len(set(dates)):
            raise ValueError("Simulation contains duplicate daily records.")

        if dates != sorted(dates):
            raise ValueError("Simulation records must be chronological.")

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("Simulation start date must precede end date.")

        if self.planting_date > self.start_date:
            raise ValueError("Planting date cannot follow simulation start.")

        dates = [record.date for record in self.records]

        if len(dates) != len(set(dates)):
            raise ValueError("Simulation contains duplicate daily records.")

        if dates != sorted(dates):
            raise ValueError("Simulation records must be chronological.")
