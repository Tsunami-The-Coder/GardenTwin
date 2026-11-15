import unittest

from simulation.water.soil_properties import SoilHydraulicProperties


class TestSoilHydraulicProperties(unittest.TestCase):

    def setUp(self):
        self.soil = SoilHydraulicProperties(
            wilting_point=0.12,
            field_capacity=0.30,
            saturation=0.45,
            saturated_hydraulic_conductivity_mm_day=10.0,
            root_depth_cm=30.0,
        )

    def test_converts_water_contents_to_mm(self):
        self.assertAlmostEqual(self.soil.wilting_point_mm, 36.0)
        self.assertAlmostEqual(self.soil.field_capacity_mm, 90.0)
        self.assertAlmostEqual(self.soil.saturation_mm, 135.0)

    def test_converts_arbitrary_water_content(self):
        self.assertAlmostEqual(
            self.soil.water_content_to_mm(0.20), 60.0
        )

    def test_rejects_invalid_water_content(self):
        with self.assertRaises(ValueError):
            self.soil.water_content_to_mm(0.50)

    def test_rejects_invalid_field_capacity(self):
        with self.assertRaises(ValueError):
            SoilHydraulicProperties(
                wilting_point=0.30,
                field_capacity=0.20,
                saturation=0.45,
                saturated_hydraulic_conductivity_mm_day=10.0,
                root_depth_cm=30.0,
            )

    def test_rejects_negative_conductivity(self):
        with self.assertRaises(ValueError):
            SoilHydraulicProperties(
                wilting_point=0.12,
                field_capacity=0.30,
                saturation=0.45,
                saturated_hydraulic_conductivity_mm_day=-1.0,
                root_depth_cm=30.0,
            )


if __name__ == "__main__":
    unittest.main()
