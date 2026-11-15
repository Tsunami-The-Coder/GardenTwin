import unittest

from simulation.contracts import NutrientState
from simulation.nutrients.balance import (
    NutrientFluxes,
    simulate_nutrient_balance,
)


class TestNutrientBalance(unittest.TestCase):

    def setUp(self):
        self.initial = NutrientState(
            nitrogen_available_kg_ha=100.0,
            phosphorus_available_kg_ha=50.0,
            potassium_available_kg_ha=80.0,
            nutrient_stress_index=None,
            soil_test_available=True,
        )

    def test_basic_nutrient_balance(self):
        fluxes = NutrientFluxes(
            fertilizer_n_kg_ha=10.0,
            mineralization_n_kg_ha=5.0,
            crop_demand_n_kg_ha=20.0,
            losses_n_kg_ha=5.0,
        )

        result = simulate_nutrient_balance(
            self.initial, fluxes
        )

        self.assertAlmostEqual(
            result.state.nitrogen_available_kg_ha, 90.0
        )

    def test_fertilizer_increases_availability(self):
        fluxes = NutrientFluxes(
            fertilizer_n_kg_ha=20.0
        )

        result = simulate_nutrient_balance(
            self.initial, fluxes
        )

        self.assertEqual(
            result.state.nitrogen_available_kg_ha, 120.0
        )

    def test_uptake_cannot_exceed_available_pool(self):
        fluxes = NutrientFluxes(
            crop_demand_n_kg_ha=150.0
        )

        result = simulate_nutrient_balance(
            self.initial, fluxes
        )

        self.assertEqual(
            result.state.nitrogen_available_kg_ha, 0.0
        )
        self.assertEqual(
            result.actual_uptake_n_kg_ha, 100.0
        )
        self.assertEqual(
            result.unmet_demand_n_kg_ha, 50.0
        )

    def test_unknown_nutrient_stays_unknown(self):
        initial = NutrientState(
            nitrogen_available_kg_ha=None,
            phosphorus_available_kg_ha=50.0,
            potassium_available_kg_ha=80.0,
            nutrient_stress_index=None,
            soil_test_available=False,
        )

        result = simulate_nutrient_balance(
            initial,
            NutrientFluxes(fertilizer_n_kg_ha=20.0),
        )

        self.assertIsNone(
            result.state.nitrogen_available_kg_ha
        )

    def test_no_demand_means_unknown_stress(self):
        result = simulate_nutrient_balance(
            self.initial,
            NutrientFluxes(),
        )

        self.assertIsNone(
            result.state.nutrient_stress_index
        )

    def test_all_demand_met_means_zero_stress(self):
        result = simulate_nutrient_balance(
            self.initial,
            NutrientFluxes(
                crop_demand_n_kg_ha=10.0,
                crop_demand_p_kg_ha=10.0,
                crop_demand_k_kg_ha=10.0,
            ),
        )

        self.assertAlmostEqual(
            result.state.nutrient_stress_index, 0.0
        )

    def test_unmet_demand_increases_stress(self):
        result = simulate_nutrient_balance(
            self.initial,
            NutrientFluxes(
                crop_demand_n_kg_ha=200.0,
            ),
        )

        self.assertAlmostEqual(
            result.state.nutrient_stress_index, 0.5
        )

    def test_negative_flux_is_rejected(self):
        with self.assertRaises(ValueError):
            NutrientFluxes(
                fertilizer_n_kg_ha=-5.0
            )

    def test_losses_are_subtracted_before_crop_uptake(self):
        nutrients = NutrientState(
            nitrogen_available_kg_ha=100.0,
            phosphorus_available_kg_ha=40.0,
            potassium_available_kg_ha=80.0,
            soil_test_available=True,
        )

        fluxes = NutrientFluxes(
            fertilizer_n_kg_ha=0.0,
            fertilizer_p_kg_ha=0.0,
            fertilizer_k_kg_ha=0.0,
            mineralization_n_kg_ha=0.0,
            mineralization_p_kg_ha=0.0,
            mineralization_k_kg_ha=0.0,
            crop_demand_n_kg_ha=30.0,
            crop_demand_p_kg_ha=0.0,
            crop_demand_k_kg_ha=0.0,
            losses_n_kg_ha=20.0,
            losses_p_kg_ha=0.0,
            losses_k_kg_ha=0.0,
        )

        result = simulate_nutrient_balance(nutrients, fluxes)

        self.assertAlmostEqual(
            result.state.nitrogen_available_kg_ha, 50.0
        )
        self.assertAlmostEqual(result.actual_uptake_n_kg_ha, 30.0)



if __name__ == "__main__":
    unittest.main()
