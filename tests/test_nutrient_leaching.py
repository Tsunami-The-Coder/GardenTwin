import unittest

from simulation.contracts import NutrientState
from simulation.nutrients.leaching import calculate_nutrient_leaching


class TestNutrientLeaching(unittest.TestCase):

    def setUp(self):
        self.nutrients = NutrientState(
            nitrogen_available_kg_ha=100.0,
            phosphorus_available_kg_ha=40.0,
            potassium_available_kg_ha=80.0,
            nutrient_stress_index=0.0,
            soil_test_available=True,
        )

    def test_calculates_losses(self):
        result = calculate_nutrient_leaching(
            self.nutrients,
            nitrogen_fraction=0.10,
            phosphorus_fraction=0.02,
            potassium_fraction=0.05,
        )

        self.assertAlmostEqual(result.nitrogen_loss_kg_ha, 10.0)
        self.assertAlmostEqual(result.phosphorus_loss_kg_ha, 0.8)
        self.assertAlmostEqual(result.potassium_loss_kg_ha, 4.0)

    def test_zero_leaching(self):
        result = calculate_nutrient_leaching(
            self.nutrients, 0.0, 0.0, 0.0
        )

        self.assertEqual(result.nitrogen_loss_kg_ha, 0.0)
        self.assertEqual(result.phosphorus_loss_kg_ha, 0.0)
        self.assertEqual(result.potassium_loss_kg_ha, 0.0)

    def test_unknown_nutrient_stays_unknown(self):
        nutrients = NutrientState(
            nitrogen_available_kg_ha=None,
            phosphorus_available_kg_ha=40.0,
            potassium_available_kg_ha=None,
            soil_test_available=False,
        )

        result = calculate_nutrient_leaching(
            nutrients, 0.1, 0.1, 0.1
        )

        self.assertIsNone(result.nitrogen_loss_kg_ha)
        self.assertAlmostEqual(result.phosphorus_loss_kg_ha, 4.0)
        self.assertIsNone(result.potassium_loss_kg_ha)

    def test_rejects_invalid_fraction(self):
        with self.assertRaises(ValueError):
            calculate_nutrient_leaching(
                self.nutrients, 1.5, 0.0, 0.0
            )


if __name__ == "__main__":
    unittest.main()
