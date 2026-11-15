
import math
import unittest

from simulation.contracts import NutrientState
from simulation.nutrients.soil_losses import calculate_soil_losses


class TestSoilLosses(unittest.TestCase):

    def setUp(self):
        self.nutrients = NutrientState(
            nitrogen_available_kg_ha=100.0,
            phosphorus_available_kg_ha=40.0,
            potassium_available_kg_ha=80.0,
            nutrient_stress_index=0.0,
            soil_test_available=True,
        )

    def calculate(self, soil_water_mm):
        return calculate_soil_losses(
            soil_water_mm=soil_water_mm,
            field_capacity_mm=70.0,
            saturated_water_content_mm=120.0,
            drainage_fraction=0.5,
            nutrients=self.nutrients,
            nitrogen_sensitivity_per_mm=0.01,
            phosphorus_sensitivity_per_mm=0.002,
            potassium_sensitivity_per_mm=0.005,
        )

    def test_calculates_drainage_dependent_losses(self):
        result = self.calculate(100.0)

        self.assertAlmostEqual(result.drainage.drainage_mm, 15.0)

        expected_n = 100.0 * (1.0 - math.exp(-0.01 * 15.0))
        expected_p = 40.0 * (1.0 - math.exp(-0.002 * 15.0))
        expected_k = 80.0 * (1.0 - math.exp(-0.005 * 15.0))

        self.assertAlmostEqual(
            result.nutrient_losses.nitrogen_loss_kg_ha,
            expected_n,
        )
        self.assertAlmostEqual(
            result.nutrient_losses.phosphorus_loss_kg_ha,
            expected_p,
        )
        self.assertAlmostEqual(
            result.nutrient_losses.potassium_loss_kg_ha,
            expected_k,
        )

    def test_no_drainage_means_no_leaching(self):
        result = self.calculate(70.0)

        self.assertEqual(result.drainage.drainage_mm, 0.0)
        self.assertEqual(
            result.nutrient_losses.nitrogen_loss_kg_ha, 0.0
        )
        self.assertEqual(
            result.nutrient_losses.phosphorus_loss_kg_ha, 0.0
        )
        self.assertEqual(
            result.nutrient_losses.potassium_loss_kg_ha, 0.0
        )

    def test_more_drainage_causes_more_leaching(self):
        low = self.calculate(80.0)
        high = self.calculate(110.0)

        self.assertGreater(
            high.nutrient_losses.nitrogen_loss_kg_ha,
            low.nutrient_losses.nitrogen_loss_kg_ha,
        )

    def test_rejects_negative_sensitivity(self):
        with self.assertRaises(ValueError):
            calculate_soil_losses(
                100.0, 70.0, 120.0, 0.5,
                self.nutrients,
                -0.01, 0.002, 0.005,
            )


if __name__ == "__main__":
    unittest.main()
