import unittest

from simulation.water.drainage import calculate_drainage


class TestDrainage(unittest.TestCase):

    def test_calculates_drainage(self):
        result = calculate_drainage(
            soil_water_mm=100,
            field_capacity_mm=70,
            saturated_water_content_mm=120,
            drainage_fraction=0.5,
        )

        self.assertAlmostEqual(
            result.water_above_field_capacity_mm, 30
        )
        self.assertAlmostEqual(result.drainage_mm, 15)
        self.assertAlmostEqual(result.water_remaining_mm, 85)

    def test_no_excess_water(self):
        result = calculate_drainage(70, 70, 120, 0.5)

        self.assertEqual(result.drainage_mm, 0)
        self.assertEqual(result.water_remaining_mm, 70)

    def test_complete_drainage_of_excess(self):
        result = calculate_drainage(100, 70, 120, 1.0)

        self.assertEqual(result.drainage_mm, 30)
        self.assertEqual(result.water_remaining_mm, 70)

    def test_rejects_water_above_saturation(self):
        with self.assertRaises(ValueError):
            calculate_drainage(130, 70, 120, 0.5)

    def test_rejects_invalid_fraction(self):
        with self.assertRaises(ValueError):
            calculate_drainage(100, 70, 120, 1.5)


if __name__ == "__main__":
    unittest.main()
