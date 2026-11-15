import unittest
from datetime import date

from simulation.contracts import (
    CropState,
    NutrientState,
    RecommendationStatus,
    SimulationSite,
    SoilWaterState,
    WeatherObservation,
)
from simulation.engine import advance_one_day


class DailyEngineTests(unittest.TestCase):

    def setUp(self):
        self.planting_date = date(2022, 5, 1)

        self.site = SimulationSite(
            site_id="test-site",
            latitude=39.45,
            longitude=-75.23,
            location_name="New Jersey test site",
        )

        self.weather = WeatherObservation(
            date=date(2022, 6, 7),
            source="test",
            temperature_mean_c=22.0,
            temperature_min_c=15.0,
            temperature_max_c=29.0,
            precipitation_mm=0.0,
            relative_humidity_pct=60.0,
            solar_radiation_mj_m2_day=20.0,
            wind_speed_2m_m_s=2.0,
        )

        self.soil = SoilWaterState(
            root_zone_water_mm=120.0,
            field_capacity_mm=150.0,
            wilting_point_mm=50.0,
            root_depth_cm=30.0,
            water_stress_index=0.0,
        )

        self.nutrients = NutrientState(
            soil_test_available=False,
        )

        self.crop = CropState(
            crop_name="tomato",
            growth_stage="vegetative",
            days_after_planting=0,
        )

    def test_daily_engine_returns_record(self):
        result = advance_one_day(
            observation=self.weather,
            previous_soil=self.soil,
            nutrients=self.nutrients,
            crop=self.crop,
            site=self.site,
            planting_date=self.planting_date,
            crop_coefficient=1.0,
        )

        self.assertEqual(
            result.record.date,
            self.weather.date,
        )

        self.assertEqual(
            result.record.weather.date,
            self.weather.date,
        )

    def test_reference_et_is_nonnegative(self):
        result = advance_one_day(
            self.weather,
            self.soil,
            self.nutrients,
            self.crop,
            self.site,
            self.planting_date,
            crop_coefficient=1.0,
        )

        self.assertGreaterEqual(result.reference_et_mm, 0.0)

    def test_crop_age_is_updated(self):
        result = advance_one_day(
            self.weather,
            self.soil,
            self.nutrients,
            self.crop,
            self.site,
            self.planting_date,
            crop_coefficient=1.0,
        )

        self.assertEqual(
            result.record.crop.days_after_planting,
            37,
        )

    def test_fertilizer_is_unknown_without_nutrient_model(self):
        result = advance_one_day(
            self.weather,
            self.soil,
            self.nutrients,
            self.crop,
            self.site,
            self.planting_date,
            crop_coefficient=1.0,
        )

        self.assertEqual(
            result.record.fertilizer.status,
            RecommendationStatus.UNKNOWN,
        )

    def test_missing_weather_is_rejected(self):
        incomplete_weather = WeatherObservation(
            date=self.weather.date,
            source="test",
            temperature_min_c=15.0,
            temperature_max_c=29.0,
            precipitation_mm=0.0,
        )

        with self.assertRaises(ValueError):
            advance_one_day(
                incomplete_weather,
                self.soil,
                self.nutrients,
                self.crop,
                self.site,
                self.planting_date,
                crop_coefficient=1.0,
            )

    def test_date_before_planting_is_rejected(self):
        before_planting = WeatherObservation(
            date=date(2022, 4, 30),
            source="test",
            temperature_min_c=15.0,
            temperature_max_c=29.0,
            precipitation_mm=0.0,
            relative_humidity_pct=60.0,
            solar_radiation_mj_m2_day=20.0,
            wind_speed_2m_m_s=2.0,
        )

        with self.assertRaises(ValueError):
            advance_one_day(
                before_planting,
                self.soil,
                self.nutrients,
                self.crop,
                self.site,
                self.planting_date,
                crop_coefficient=1.0,
            )


if __name__ == "__main__":
    unittest.main()
