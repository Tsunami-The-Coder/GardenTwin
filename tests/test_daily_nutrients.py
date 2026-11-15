import math
import unittest

from simulation.contracts import NutrientState
from simulation.nutrients.balance import NutrientFluxes
from simulation.nutrients.daily import simulate_daily_nutrients
from simulation.water.soil_properties import SoilHydraulicProperties


class TestDailyNutrients(unittest.TestCase):

    def setUp(self):
        self.nutrients = NutrientState(
            nitrogen_available_kg_ha=100.0,
            phosphorus_available_kg_ha=40.0,
            potassium_available_kg_ha=80.0,
            nutrient_stress_index=0.0,
            soil_test_available=True,
        )

        self.soil_properties = SoilHydraulicProperties(
            wilting_point=0.12,
            field_capacity=0.30,
            saturation=0.45,
            saturated_hydraulic_conductivity_mm_day=10.0,
            root_depth_cm=30.0,
        )

    def test_daily_losses_affect_updated_nutrient_state(self):
        fluxes = NutrientFluxes(
            fertilizer_n_kg_ha=10.0,
            mineralization_n_kg_ha=5.0,
            crop_demand_n_kg_ha=30.0,
        )

        result = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=fluxes,
            drainage_mm=15.0,
            nitrogen_sensitivity_per_mm=0.01,
            phosphorus_sensitivity_per_mm=0.002,
            potassium_sensitivity_per_mm=0.005,
        )

        expected_leaching = 115.0 * (
            1.0 - math.exp(-0.01 * 15.0)
        )
        expected_remaining = 115.0 - expected_leaching - 30.0

        self.assertAlmostEqual(
            result.nutrient_losses.nitrogen_loss_kg_ha,
            expected_leaching,
        )
        self.assertAlmostEqual(
            result.balance.state.nitrogen_available_kg_ha,
            expected_remaining,
        )
        self.assertAlmostEqual(
            result.balance.actual_uptake_n_kg_ha,
            30.0,
        )

    def test_no_drainage_means_no_leaching(self):
        fluxes = NutrientFluxes(
            crop_demand_n_kg_ha=20.0,
        )

        result = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=fluxes,
            drainage_mm=0.0,
            nitrogen_sensitivity_per_mm=0.01,
            phosphorus_sensitivity_per_mm=0.002,
            potassium_sensitivity_per_mm=0.005,
        )

        self.assertEqual(
            result.nutrient_losses.nitrogen_loss_kg_ha,
            0.0,
        )
        self.assertAlmostEqual(
            result.balance.state.nitrogen_available_kg_ha,
            80.0,
        )

    def test_negative_drainage_is_rejected(self):
        with self.assertRaises(ValueError):
            simulate_daily_nutrients(
                nutrients=self.nutrients,
                fluxes=NutrientFluxes(),
                drainage_mm=-1.0,
            )

    def test_hydraulic_leaching_uses_nutrient_mobility(self):
        result = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=NutrientFluxes(),
            drainage_mm=20.0,
            soil_properties=self.soil_properties,
            root_zone_water_mm=1000.0,
        )

        nitrogen_loss = result.nutrient_losses.nitrogen_loss_kg_ha
        phosphorus_loss = result.nutrient_losses.phosphorus_loss_kg_ha
        potassium_loss = result.nutrient_losses.potassium_loss_kg_ha

        self.assertGreater(nitrogen_loss, potassium_loss)
        self.assertGreater(potassium_loss, phosphorus_loss)
        self.assertGreater(phosphorus_loss, 0.0)

    def test_more_drainage_causes_more_nutrient_leaching(self):
        low_drainage = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=NutrientFluxes(),
            drainage_mm=5.0,
            soil_properties=self.soil_properties,
            root_zone_water_mm=1000.0,
        )

        high_drainage = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=NutrientFluxes(),
            drainage_mm=30.0,
            soil_properties=self.soil_properties,
            root_zone_water_mm=1000.0,
        )

        self.assertGreater(
            high_drainage.nutrient_losses.nitrogen_loss_kg_ha,
            low_drainage.nutrient_losses.nitrogen_loss_kg_ha,
        )

    def test_hydraulic_mode_has_no_losses_without_drainage(self):
        result = simulate_daily_nutrients(
            nutrients=self.nutrients,
            fluxes=NutrientFluxes(),
            drainage_mm=0.0,
            soil_properties=self.soil_properties,
            root_zone_water_mm=1000.0,
        )

        self.assertEqual(
            result.nutrient_losses.nitrogen_loss_kg_ha,
            0.0,
        )
        self.assertEqual(
            result.nutrient_losses.phosphorus_loss_kg_ha,
            0.0,
        )
        self.assertEqual(
            result.nutrient_losses.potassium_loss_kg_ha,
            0.0,
        )

    def test_hydraulic_mode_requires_root_zone_water(self):
        with self.assertRaises(ValueError):
            simulate_daily_nutrients(
                nutrients=self.nutrients,
                fluxes=NutrientFluxes(),
                drainage_mm=10.0,
                soil_properties=self.soil_properties,
            )


if __name__ == "__main__":
    unittest.main()
