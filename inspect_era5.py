
import xarray as xr

URL = (
    "gs://weatherbench2/datasets/era5/"
    "1959-2023_01_10-wb13-6h-1440x721_with_derived_variables.zarr"
)

print("Opening public ERA5 dataset...")

ds = xr.open_zarr(
    URL,
    storage_options={"token": "anon"},
    chunks=None,
)

print("\nDATASET VARIABLES")
print(list(ds.data_vars))

print("\nCOORDINATES")
for name, coord in ds.coords.items():
    print(name, coord.shape, coord.values[:5])

print("\nDIMENSIONS")
print(dict(ds.sizes))

print("\nAVAILABLE TIME RANGE")
print(ds.time.values[0], "to", ds.time.values[-1])

print("\nDATASET INSPECTION COMPLETE")
