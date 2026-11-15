import unittest

from simulation.crops.profiles import (
    CropProfile,
    GrowthStage,
    GrowthStageThreshold,
    determine_growth_stage,
)


class TestCropProfiles(unittest.TestCase):

    def setUp(self):
        self.profile = CropProfile(
            crop_id="test_crop",
            common_name="Test Crop",
            scientific_name="Testus plantus",
            base_temperature_c=10.0,
            upper_temperature_c=30.0,
            stage_thresholds=(
                GrowthStageThreshold(GrowthStage.PLANTED, 0.0),
                GrowthStageThreshold(GrowthStage.EMERGENCE, 50.0),
                GrowthStageThreshold(GrowthStage.VEGETATIVE, 150.0),
                GrowthStageThreshold(GrowthStage.FLOWERING, 300.0),
                GrowthStageThreshold(GrowthStage.FRUIT_DEVELOPMENT, 450.0),
                GrowthStageThreshold(GrowthStage.MATURITY, 700.0),
            ),
        )

    def test_initial_stage(self):
        self.assertEqual(
            determine_growth_stage(0.0, self.profile),
            GrowthStage.PLANTED,
        )

    def test_emergence_stage(self):
        self.assertEqual(
            determine_growth_stage(50.0, self.profile),
            GrowthStage.EMERGENCE,
        )

    def test_intermediate_gdd(self):
        self.assertEqual(
            determine_growth_stage(200.0, self.profile),
            GrowthStage.VEGETATIVE,
        )

    def test_maturity_stage(self):
        self.assertEqual(
            determine_growth_stage(700.0, self.profile),
            GrowthStage.MATURITY,
        )

    def test_stage_does_not_advance_before_threshold(self):
        self.assertEqual(
            determine_growth_stage(49.9, self.profile),
            GrowthStage.PLANTED,
        )

    def test_negative_gdd_rejected(self):
        with self.assertRaises(ValueError):
            determine_growth_stage(-1.0, self.profile)

    def test_invalid_temperature_range_rejected(self):
        with self.assertRaises(ValueError):
            CropProfile(
                crop_id="invalid",
                common_name="Invalid Crop",
                scientific_name="Invalidus",
                base_temperature_c=30.0,
                upper_temperature_c=20.0,
                stage_thresholds=(
                    GrowthStageThreshold(GrowthStage.PLANTED, 0.0),
                ),
            )

    def test_non_increasing_thresholds_rejected(self):
        with self.assertRaises(ValueError):
            CropProfile(
                crop_id="invalid",
                common_name="Invalid Crop",
                scientific_name="Invalidus",
                base_temperature_c=10.0,
                upper_temperature_c=30.0,
                stage_thresholds=(
                    GrowthStageThreshold(GrowthStage.PLANTED, 0.0),
                    GrowthStageThreshold(GrowthStage.EMERGENCE, 100.0),
                    GrowthStageThreshold(GrowthStage.VEGETATIVE, 90.0),
                ),
            )


if __name__ == "__main__":
    unittest.main()
