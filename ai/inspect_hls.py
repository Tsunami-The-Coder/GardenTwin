from pathlib import Path
import rasterio
import numpy as np

path = Path("data/prithvi/2025-06-02.tif")

with rasterio.open(path) as src:
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Transform:", src.transform)
    print("NoData:", src.nodata)
    print("Dimensions:", src.width, src.height)

    data = src.read()
    print("Unique values:", np.unique(data)[:20])
    print("Valid pixels per band:")

    for i in range(src.count):
        band = data[i]
        valid = band != src.nodata if src.nodata is not None else np.isfinite(band)
        print(i + 1, int(valid.sum()), "/", valid.size)
