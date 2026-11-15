import json
import unittest
from datetime import date
from unittest.mock import patch

from simulation.contracts import SimulationSite
from simulation.weather.nasa_power import (
    fetch_nasa_power_weather,
)


class TestNasaPower(unittest.TestCase):

    def setUp(self):
        self.site = SimulationSite(
            site_id="test_site",
            latitude=39.45,
            longitude=-75.23,
            location_name="New Jersey test site",
        )

        self.payload = {
            "properties": {
                "parameter": {
                    "T2M": {"20220607": 22.0},
                    "T2M_MAX": {"20220607": 28.0},
                    "T2M_MIN": {"20220607": 16.0},
                    "PRECTOTCORR": {"20220607": 4.0},
                    "RH2M": {"20220607": 70.0},
                    "WS2M": {"20220607": 2.5},
                    "ALLSKY_SFC_SW_DWN": {"20220607": 5.0},
                }
            }
        }

    @patch("simulation.weather.nasa_power.urlopen")
    def test_returns_weather_observation(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps(
            self.payload
        ).encode("utf-8")

        observations = fetch_nasa_power_weather(
            self.site,
            date(2022, 6, 7),
            date(2022, 6, 7),
        )

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].date, date(2022, 6, 7))
        self.assertEqual(observations[0].temperature_mean_c, 22.0)

    @patch("simulation.weather.nasa_power.urlopen")
    def test_solar_radiation_is_converted(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps(
            self.payload
        ).encode("utf-8")

        observations = fetch_nasa_power_weather(
            self.site,
            date(2022, 6, 7),
            date(2022, 6, 7),
        )

        self.assertAlmostEqual(
            observations[0].solar_radiation_mj_m2_day,
            5.0,
        )

    @patch("simulation.weather.nasa_power.urlopen")
    def test_missing_values_become_none(self, mock_urlopen):
        self.payload["properties"]["parameter"]["T2M"][
            "20220607"
        ] = -999

        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps(
            self.payload
        ).encode("utf-8")

        observations = fetch_nasa_power_weather(
            self.site,
            date(2022, 6, 7),
            date(2022, 6, 7),
        )

        self.assertIsNone(
            observations[0].temperature_mean_c
        )

    def test_rejects_invalid_date_range(self):
        with self.assertRaises(ValueError):
            fetch_nasa_power_weather(
                self.site,
                date(2022, 6, 10),
                date(2022, 6, 7),
            )

    def test_rejects_invalid_timeout(self):
        with self.assertRaises(ValueError):
            fetch_nasa_power_weather(
                self.site,
                date(2022, 6, 7),
                date(2022, 6, 7),
                timeout=0,
            )


if __name__ == "__main__":
    unittest.main()
