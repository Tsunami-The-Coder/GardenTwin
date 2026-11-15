import unittest
from datetime import date, timedelta

from simulation.contracts import (
    CropState,
    NutrientState,
    RecommendationStatus,
    SimulationSite,
    SoilWaterState,
    WeatherObservation,
)
from simulation.season import simulate_season


class SeasonSimulationTests(unittest.TestCase):

    def setUp(self):
        self.planting_date = date(2022, 5, 1)

        self.site = SimulationSite(
            site_id="test-site",
            latitude=39.45,
            longitude=-75.23,
            location_name="New Jersey test site",
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

        self.start = date(2022, 6, 7)

    def make_observations(self, count):
        return [
            WeatherObservation(
                date=self.start + timedelta(days=i),
                source="test",
                temperature_mean_c=22.0,
                temperature_min_c=15.0,
                temperature_max_c=29.0,
                precipitation_mm=2.0,
                relative_humidity_pct=60.0,
                solar_radiation_mj_m2_day=20.0,
                wind_speed_2m_m_s=2.0,
            )
            for i in range(count)
        ]

    def run_season(self, observations, **kwargs):
        return simulate_season(
            run_id="test-run",
            observations=observations,
            initial_soil=self.soil,
            initial_nutrients=self.nutrients,
            initial_crop=self.crop,
            site=self.site,
            planting_date=self.planting_date,
            crop_coefficient=1.0,
            **kwargs,
        )

    def test_creates_one_record_per_day(self):
        run = self.run_season(self.make_observations(10))

        self.assertEqual(len(run.records), 10)

    def test_dates_are_chronological(self):
        run = self.run_season(self.make_observations(5))

        dates = [record.date for record in run.records]

        self.assertEqual(dates, sorted(dates))

    def test_crop_age_advances_each_day(self):
        run = self.run_season(self.make_observations(3))

        ages = [
            record.crop.days_after_planting
            for record in run.records
        ]

        self.assertEqual(ages, [37, 38, 39])

    def test_soil_state_carries_forward(self):
        run = self.run_season(self.make_observations(3))

        self.assertNotEqual(
            run.records[0].soil_water.root_zone_water_mm,
            run.records[1].soil_water.root_zone_water_mm,
        )

    def test_missing_weather_date_is_rejected(self):
        observations = self.make_observations(3)
        observations.pop(1)

        with self.assertRaises(ValueError):
            self.run_season(observations)

    def test_duplicate_weather_date_is_rejected(self):
        observations = self.make_observations(3)
        observations[1].date = observations[0].date

        with self.assertRaises(ValueError):
            self.run_season(observations)

    def test_actual_irrigation_changes_soil_water(self):
        observations = self.make_observations(2)

        without_irrigation = self.run_season(observations)

        with_irrigation = self.run_season(
            observations,
            actual_irrigation_by_date={
                self.start: 20.0
            },
        )

        self.assertGreater(
            with_irrigation.records[0].soil_water.root_zone_water_mm,
            without_irrigation.records[0].soil_water.root_zone_water_mm,
        )

    def test_recommendations_are_not_automatically_applied(self):
        observations = self.make_observations(2)

        run = self.run_season(observations)

        self.assertEqual(
            run.records[0].irrigation.status,
            RecommendationStatus.NONE,
        )

        # Rainfall is applied, but no recommended irrigation
        # is automatically added to the following day's water balance.
        self.assertEqual(
            run.records[0].irrigation.amount_mm,
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
