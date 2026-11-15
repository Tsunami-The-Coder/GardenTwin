import os
from pathlib import Path
from datetime import date

import rasterio
from rasterio.windows import Window
from pyproj import Transformer
from pystac_client import Client
import planetary_computer

LAT = float(os.environ["GARDENTWIN_LATITUDE"])
LON = float(os.environ["GARDENTWIN_LONGITUDE"])

TARGET_DATES = [
    date(2025, 6, 2),
    date(2025, 6, 25),
    date(2025, 7, 25),
    date(2025, 8, 29),
]

BANDS = ["B02", "B03", "B04", "B05", "B06", "B07"]
OUTPUT_DIR = Path("data/prithvi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

search = catalog.search(
    collections=["hls2-s30"],
    bbox=[LON - 0.02, LAT - 0.02, LON + 0.02, LAT + 0.02],
    datetime="2025-06-01/2025-08-31",
    query={"eo:cloud_cover": {"lt": 40}},
)

items = list(search.items())
print(f"Found {len(items)} scenes")

# Convert geographic coordinates into the raster's projected CRS.
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32618",
    always_xy=True,
)
x, y = transformer.transform(LON, LAT)
print(f"Garden projected coordinates: {x:.2f}, {y:.2f}")

for target in TARGET_DATES:
    candidates = [
        item for item in items
        if item.datetime.date() == target
        and all(band in item.assets for band in BANDS)
    ]

    if not candidates:
        raise RuntimeError(f"No scene found for {target}")

    item = min(
        candidates,
        key=lambda obj: obj.properties.get("eo:cloud_cover", 100),
    )

    print(f"\nProcessing {item.id}")

    with rasterio.open(item.assets["B02"].href) as src:
        # Convert the garden's projected coordinates to pixel coordinates.
        row, col = src.index(x, y)

        print("Raster bounds:", src.bounds)
        print("Garden pixel:", row, col)

        window = Window(col - 112, row - 112, 224, 224)
        transform = src.window_transform(window)

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=224,
            width=224,
            count=6,
            transform=transform,
            compress="deflate",
        )

    output_path = OUTPUT_DIR / f"{target.isoformat()}.tif"

    with rasterio.open(output_path, "w", **profile) as dst:
        for band_index, band in enumerate(BANDS, start=1):
            with rasterio.open(item.assets[band].href) as src:
                data = src.read(
                    1,
                    window=window,
                    boundless=True,
                    fill_value=src.nodata if src.nodata is not None else 0,
                )
                dst.write(data, band_index)

    with rasterio.open(output_path) as check:
        data = check.read()
        nodata = check.nodata

        valid = data != nodata if nodata is not None else data != -9999

        print("Saved:", output_path)
        print("Shape:", data.shape)
        print("Valid pixels:", int(valid.sum()), "/", data.size)
        print("Data range:", data.min(), "to", data.max())

        if not valid.any():
            raise RuntimeError(
                f"{target}: image still contains only NoData pixels"
            )

print("\nAll four observations downloaded and checked.")
