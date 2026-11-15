import unittest
from datetime import date, timedelta

from simulation.contracts import (
    CropState,
    DailySimulationRecord,
    FertilizerRecommendation,
    IrrigationRecommendation,
    NutrientState,
    RecommendationStatus,
    SimulationRun,
    SimulationSite,
    SoilWaterState,
    WeatherObservation,
)
from backend.services.overview_service import build_overview


def make_record(day):
    """Create test data only; these values are not scientific outputs."""

    return DailySimulationRecord(
        date=day,
        weather=WeatherObservation(
            date=day,
            source="test",
            temperature_mean_c=22.0,
            precipitation_mm=2.0,
        ),
        soil_water=SoilWaterState(
            root_zone_water_mm=100.0,
            water_stress_index=0.1,
        ),
        nutrients=NutrientState(
            nitrogen_available_kg_ha=None,
        ),
        crop=CropState(
            crop_name="tomato",
            growth_stage="vegetative",
            days_after_planting=30,
            height_cm=25.0,
            health_index=0.9,
        ),
        irrigation=IrrigationRecommendation(
            status=RecommendationStatus.NONE,
            amount_mm=0.0,
            reason="Test record.",
        ),
        fertilizer=FertilizerRecommendation(
            status=RecommendationStatus.UNKNOWN,
            reason="Nutrient data unavailable.",
        ),
    )


class GardenTwinTests(unittest.TestCase):

    def test_daily_record_requires_matching_weather_date(self):
        day = date(2022, 6, 7)

        with self.assertRaises(ValueError):
            DailySimulationRecord(
                date=day,
                weather=WeatherObservation(
                    date=day + timedelta(days=1),
                    source="test",
                ),
                soil_water=SoilWaterState(),
                nutrients=NutrientState(),
                crop=CropState("tomato", "vegetative", 10),
                irrigation=IrrigationRecommendation(
                    RecommendationStatus.UNKNOWN
                ),
                fertilizer=FertilizerRecommendation(
                    RecommendationStatus.UNKNOWN
                ),
            )

    def test_overview_contains_seven_following_days(self):
        start = date(2022, 6, 7)
        records = [
            make_record(start + timedelta(days=i))
            for i in range(8)
        ]

        run = SimulationRun(
            run_id="test_run",
            site=SimulationSite(
                site_id="test_site",
                latitude=39.4,
                longitude=-75.2,
                location_name="Test, New Jersey",
            ),
            crop_name="tomato",
            planting_date=date(2022, 5, 8),
            start_date=start,
            end_date=start + timedelta(days=7),
            records=records,
        )

        overview = build_overview(run, start)

        self.assertEqual(overview.selected_date, start)
        self.assertEqual(overview.today.date, start)
        self.assertEqual(len(overview.next_7_days), 7)
        self.assertEqual(
            overview.next_7_days[0].date,
            start + timedelta(days=1),
        )
        self.assertEqual(
            overview.next_7_days[-1].date,
            start + timedelta(days=7),
        )

    def test_overview_rejects_missing_days(self):
        start = date(2022, 6, 7)

        run = SimulationRun(
            run_id="incomplete_run",
            site=SimulationSite("test", 39.4, -75.2),
            crop_name="tomato",
            planting_date=date(2022, 5, 8),
            start_date=start,
            end_date=start + timedelta(days=2),
            records=[
                make_record(start + timedelta(days=i))
                for i in range(3)
            ],
        )

        with self.assertRaises(ValueError):
            build_overview(run, start)


if __name__ == "__main__":
    unittest.main()
