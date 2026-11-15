import unittest
from datetime import date

from simulation.water.evapotranspiration import (
    calculate_reference_et,
)


class EvapotranspirationTests(unittest.TestCase):

    def calculate(self, **overrides):
        parameters = {
            "observation_date": date(2022, 6, 7),
            "temperature_min_c": 16.0,
            "temperature_max_c": 28.0,
            "relative_humidity_percent": 65.0,
            "solar_radiation_mj_m2_day": 20.0,
            "wind_speed_2m_m_s": 2.0,
            "latitude_degrees": 40.0,
            "elevation_m": 30.0,
        }
        parameters.update(overrides)

        return calculate_reference_et(**parameters)

    def test_returns_nonnegative_eto(self):
        result = self.calculate()
        self.assertGreaterEqual(result, 0.0)

    def test_returns_finite_value(self):
        result = self.calculate()
        self.assertTrue(float("-inf") < result < float("inf"))

    def test_more_solar_radiation_increases_eto(self):
        cloudy = self.calculate(
            solar_radiation_mj_m2_day=10.0
        )
        sunny = self.calculate(
            solar_radiation_mj_m2_day=25.0
        )

        self.assertGreater(sunny, cloudy)

    def test_invalid_temperature_range_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(
                temperature_min_c=30.0,
                temperature_max_c=20.0,
            )

    def test_invalid_humidity_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(
                relative_humidity_percent=120.0
            )

    def test_negative_wind_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(wind_speed_2m_m_s=-1.0)


if __name__ == "__main__":
    unittest.main()
