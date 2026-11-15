import unittest

from simulation.water.soil_properties import SoilHydraulicProperties
from simulation.contracts import SoilWaterState
from simulation.water.bucket import (
    calculate_water_stress,
    simulate_water_balance,
)


class WaterBalanceTests(unittest.TestCase):

    def setUp(self):
        self.soil = SoilWaterState(
            root_zone_water_mm=120.0,
            field_capacity_mm=150.0,
            wilting_point_mm=50.0,
            root_depth_cm=30.0,
            water_stress_index=0.0,
        )

    def test_rain_increases_soil_water(self):
        result = simulate_water_balance(
            self.soil,
            precipitation_mm=10.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
        )

        self.assertAlmostEqual(
            result.soil_water.root_zone_water_mm,
            130.0,
        )

    def test_excess_water_drains(self):
        result = simulate_water_balance(
            self.soil,
            precipitation_mm=50.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
        )

        self.assertAlmostEqual(
            result.soil_water.root_zone_water_mm,
            150.0,
        )

        self.assertAlmostEqual(result.drainage_mm, 20.0)

    def test_evapotranspiration_reduces_water(self):
        result = simulate_water_balance(
            self.soil,
            precipitation_mm=0.0,
            reference_et_mm=5.0,
            crop_coefficient=1.0,
        )

        self.assertLess(
            result.soil_water.root_zone_water_mm,
            self.soil.root_zone_water_mm,
        )

    def test_water_stress_increases_with_depletion(self):
        low_stress = calculate_water_stress(
            depletion_mm=20.0,
            total_available_water_mm=100.0,
            depletion_fraction=0.5,
        )

        high_stress = calculate_water_stress(
            depletion_mm=80.0,
            total_available_water_mm=100.0,
            depletion_fraction=0.5,
        )

        self.assertGreater(low_stress, high_stress)

    def test_irrigation_recommended_when_too_dry(self):
        dry_soil = SoilWaterState(
            root_zone_water_mm=80.0,
            field_capacity_mm=150.0,
            wilting_point_mm=50.0,
            root_depth_cm=30.0,
            water_stress_index=0.0,
        )

        result = simulate_water_balance(
            dry_soil,
            precipitation_mm=0.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
        )

        self.assertGreater(
            result.irrigation_recommendation_mm,
            0.0,
        )

    def test_no_irrigation_when_water_is_sufficient(self):
        result = simulate_water_balance(
            self.soil,
            precipitation_mm=0.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
        )

        self.assertEqual(
            result.irrigation_recommendation_mm,
            0.0,
        )

    def test_hydraulic_drainage_is_limited_by_conductivity(self):
        properties = SoilHydraulicProperties(
            wilting_point=1 / 6,
            field_capacity=0.5,
            saturation=0.75,
            saturated_hydraulic_conductivity_mm_day=5.0,
            root_depth_cm=30.0,
        )

        result = simulate_water_balance(
            self.soil,
            precipitation_mm=80.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
            soil_properties=properties,
        )

        self.assertGreater(result.drainage_mm, 0.0)
        self.assertLess(result.drainage_mm, 50.0)

        self.assertGreater(
            result.soil_water.root_zone_water_mm,
            150.0,
        )

    def test_hydraulic_water_balance_conserves_water(self):
        properties = SoilHydraulicProperties(
            wilting_point=1 / 6,
            field_capacity=0.5,
            saturation=0.75,
            saturated_hydraulic_conductivity_mm_day=5.0,
            root_depth_cm=30.0,
        )

        result = simulate_water_balance(
            self.soil,
            precipitation_mm=150.0,
            reference_et_mm=0.0,
            crop_coefficient=1.0,
            soil_properties=properties,
        )

        initial_plus_rain = 120.0 + 150.0
        final_water_and_drainage = (
            result.soil_water.root_zone_water_mm
            + result.drainage_mm
        )

        self.assertAlmostEqual(
            initial_plus_rain,
            final_water_and_drainage,
        )

        self.assertLessEqual(
            result.soil_water.root_zone_water_mm,
            properties.saturation_mm,
        )

if __name__ == "__main__":
    unittest.main()
