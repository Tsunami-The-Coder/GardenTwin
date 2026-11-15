import unittest

from simulation.crops.thermal_time import (
    calculate_daily_gdd,
    accumulate_gdd,
)


class TestThermalTime(unittest.TestCase):

    def test_basic_gdd_calculation(self):
        result = calculate_daily_gdd(
            temperature_min_c=10.0,
            temperature_max_c=20.0,
            base_temperature_c=10.0,
        )
        self.assertAlmostEqual(result, 5.0)

    def test_no_growth_below_base_temperature(self):
        result = calculate_daily_gdd(
            temperature_min_c=2.0,
            temperature_max_c=8.0,
            base_temperature_c=10.0,
        )
        self.assertEqual(result, 0.0)

    def test_upper_temperature_limit(self):
        result = calculate_daily_gdd(
            temperature_min_c=20.0,
            temperature_max_c=40.0,
            base_temperature_c=10.0,
            upper_temperature_c=30.0,
        )
        self.assertAlmostEqual(result, 15.0)

    def test_accumulation(self):
        result = accumulate_gdd(100.0, 12.5)
        self.assertAlmostEqual(result, 112.5)

    def test_invalid_temperature_range(self):
        with self.assertRaises(ValueError):
            calculate_daily_gdd(temperature_min_c=20.0, temperature_max_c=10.0,
                                base_temperature_c=10.0)

    def test_invalid_upper_temperature(self):
        with self.assertRaises(ValueError):
            calculate_daily_gdd(10.0, 20.0, 10.0, 8.0)

    def test_negative_daily_gdd_rejected(self):
        with self.assertRaises(ValueError):
            accumulate_gdd(100.0, -5.0)


if __name__ == "__main__":
    unittest.main()
