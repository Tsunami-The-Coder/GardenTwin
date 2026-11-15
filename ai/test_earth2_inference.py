import time
import torch

from earth2studio.data import GFS
from earth2studio.io import ZarrBackend
from earth2studio.models.px import FCN
from earth2studio.run import deterministic

torch.set_num_threads(4)

print("Loading FourCastNet...")
start = time.time()

package = FCN.load_default_package()
model = FCN.load_model(package)
model = model.to("cpu").eval()

print("Model loaded in", round(time.time() - start, 2), "seconds")

print("\nInitializing GFS weather data source...")
data = GFS()
io = ZarrBackend()

print("\nRunning one genuine Earth-2 forecast step...")
start = time.time()

with torch.no_grad():
    io = deterministic(
        ["2026-11-15"],
        1,
        model,
        data,
        io,
        device=torch.device("cpu"),
    )

print("\nEARTH-2 INFERENCE SUCCESS")
print("Forecast output:")
print(io.root.tree())
print("Inference time:", round(time.time() - start, 2), "seconds")

import json
import numpy as np
from pathlib import Path

# GardenTwin pilot location
GARDEN_LAT = 39.4273
GARDEN_LON = -75.2341

# Earth2Studio global grid coordinates
latitudes = np.asarray(io["lat"][:])
longitudes = np.asarray(io["lon"][:])

# Earth2Studio longitude uses 0–360, not -180–180
garden_lon_360 = GARDEN_LON % 360

lat_idx = int(np.abs(latitudes - GARDEN_LAT).argmin())
lon_idx = int(np.abs(longitudes - garden_lon_360).argmin())

# Index 0 is the initial GFS state; index 1 is the predicted step
forecast_idx = 1

def get_value(variable):
    return float(
        io[variable][0, forecast_idx, lat_idx, lon_idx]
    )

temperature_k = get_value("t2m")
wind_u = get_value("u10m")
wind_v = get_value("v10m")
pressure_pa = get_value("msl")
total_column_water = get_value("tcwv")

wind_speed = (wind_u**2 + wind_v**2) ** 0.5

lead_times = np.asarray(io["lead_time"][:])
lead_hours = int(
    lead_times[forecast_idx] / np.timedelta64(1, "h")
)

initialization_time = str(io["time"][0])
valid_time = str(
    np.datetime64(io["time"][0]) +
    np.timedelta64(lead_hours, "h")
)

result = {
    "model": "NVIDIA FourCastNet1 via Earth2Studio",
    "source": "GFS",
    "location": {
        "latitude": GARDEN_LAT,
        "longitude": GARDEN_LON,
        "grid_latitude": float(latitudes[lat_idx]),
        "grid_longitude": float(longitudes[lon_idx]),
    },
    "initialization_time": initialization_time,
    "forecast_valid_time": valid_time,
    "forecast_lead_hours": lead_hours,
    "weather": {
        "temperature_c": temperature_k - 273.15,
        "wind_u_10m_m_s": wind_u,
        "wind_v_10m_m_s": wind_v,
        "wind_speed_10m_m_s": wind_speed,
        "mean_sea_level_pressure_hpa": pressure_pa / 100,
        "total_column_water_kg_m2": total_column_water,
    },
}

output_path = Path("data/earth2_garden_forecast.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w") as f:
    json.dump(result, f, indent=2)

print("\nGARDEN-LEVEL EARTH-2 FORECAST")
print(json.dumps(result, indent=2))
print("\nSaved:", output_path)

for name in [
    "t2m",
    "tcwv",
    "u10m",
    "v10m",
    "msl",
    "lat",
    "lon",
    "lead_time",
]:
    try:
        arr = io[name]
        print(
            name,
            "| type:", type(arr),
            "| shape:", getattr(arr, "shape", None),
            "| sample:", arr[0] if getattr(arr, "shape", None) else arr,
        )
    except Exception as exc:
        print(name, "| ERROR:", repr(exc))