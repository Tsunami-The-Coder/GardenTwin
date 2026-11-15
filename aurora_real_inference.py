
from datetime import datetime

import numpy as np
import torch
import xarray as xr

from aurora import AuroraSmallPretrained, Batch, Metadata

# Garden location
LAT = 39.4273
LON = -75.2341

# ERA5 longitude uses 0-360 degrees
LON_360 = LON % 360

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

URL = (
    "gs://weatherbench2/datasets/era5/"
    "1959-2023_01_10-wb13-6h-1440x721_with_derived_variables.zarr"
)

TIMES = [
    np.datetime64("2022-06-15T00:00:00"),
    np.datetime64("2022-06-15T06:00:00"),
]

print("Opening ERA5...")
ds = xr.open_zarr(
    URL,
    storage_options={"token": "anon"},
    chunks=None,
)

# Select a 17 x 32 grid around the garden.
lat_idx = int(abs(ds.latitude.values - LAT).argmin())
lon_idx = int(abs(ds.longitude.values - LON_360).argmin())

lat_start = lat_idx - 8
lat_end = lat_idx + 9
lon_start = lon_idx - 16
lon_end = lon_idx + 16

region = ds.isel(
    latitude=slice(lat_start, lat_end),
    longitude=slice(lon_start, lon_end),
).sel(time=TIMES)

region = region.load()

latitudes = region.latitude.values
longitudes = region.longitude.values
levels = tuple(int(x) for x in region.level.values)

print("Region:", len(latitudes), "x", len(longitudes))
print("Pressure levels:", levels)
print("Times:", region.time.values)

def tensor(data):
    array = np.asarray(data, dtype=np.float32)
    if not np.isfinite(array).all():
        raise ValueError("ERA5 data contains non-finite values")
    return torch.from_numpy(array.copy())

# Surface variables: [batch, time, latitude, longitude]
surf_vars = {
    "2t": tensor(region["2m_temperature"].values)[None],
    "10u": tensor(region["10m_u_component_of_wind"].values)[None],
    "10v": tensor(region["10m_v_component_of_wind"].values)[None],
    "msl": tensor(region["mean_sea_level_pressure"].values)[None],
}

# Atmospheric variables:
# [batch, time, pressure_level, latitude, longitude]
atmos_vars = {
    "z": tensor(region["geopotential"].values)[None],
    "u": tensor(region["u_component_of_wind"].values)[None],
    "v": tensor(region["v_component_of_wind"].values)[None],
    "t": tensor(region["temperature"].values)[None],
    "q": tensor(region["specific_humidity"].values)[None],
}

# Static geographic variables: [latitude, longitude]
static_vars = {
    "lsm": tensor(
        region["land_sea_mask"].isel(time=0).values
        if "time" in region["land_sea_mask"].dims
        else region["land_sea_mask"].values
    ),
    "z": tensor(
        region["geopotential_at_surface"].isel(time=0).values
        if "time" in region["geopotential_at_surface"].dims
        else region["geopotential_at_surface"].values
    ),
    "slt": tensor(
        region["soil_type"].isel(time=0).values
        if "time" in region["soil_type"].dims
        else region["soil_type"].values
    ),
}

batch = Batch(
    surf_vars=surf_vars,
    static_vars=static_vars,
    atmos_vars=atmos_vars,
    metadata=Metadata(
        lat=torch.tensor(latitudes, dtype=torch.float32),
        lon=torch.tensor(longitudes, dtype=torch.float32),
        time=(datetime(2022, 6, 15, 6),),
        atmos_levels=levels,
    ),
)

print("\nInput verification:")
for name, value in surf_vars.items():
    print("Surface", name, tuple(value.shape))

for name, value in atmos_vars.items():
    print("Atmosphere", name, tuple(value.shape))

print("Static:", {
    name: tuple(value.shape)
    for name, value in static_vars.items()
})

print("\nLoading Aurora...")
model = AuroraSmallPretrained()
model.load_checkpoint()
model.eval().to(DEVICE)

print("Running actual ERA5 inference...")

with torch.inference_mode():
    prediction = model.forward(batch)

output = prediction.surf_vars["2t"]

print("\nAURORA REAL INFERENCE SUCCESS")
print("Output shape:", tuple(output.shape))
print("Finite:", bool(torch.isfinite(output).all()))
print("Predicted temperature mean (K):", output.float().mean().item())

# Convert Kelvin to Celsius for reporting.
print(
    "Predicted temperature mean (C):",
    output.float().mean().item() - 273.15
)

torch.save(
    {
        "prediction": prediction.to("cpu"),
        "latitude": latitudes,
        "longitude": longitudes,
        "initialization": "2022-06-15T06:00:00",
        "source": "ERA5",
    },
    "data/aurora_real_prediction.pt",
)

print("Saved: data/aurora_real_prediction.pt")
