import os
from pystac_client import Client
import planetary_computer

LAT = float(os.environ["GARDENTWIN_LATITUDE"])
LON = float(os.environ["GARDENTWIN_LONGITUDE"])

START_DATE = "2025-06-01"
END_DATE = "2025-08-31"

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

collections = ["hls2-s30", "hls2-l30"]

for collection in collections:
    print(f"\nSearching {collection}...")

    search = catalog.search(
        collections=[collection],
        bbox=[
            LON - 0.02,
            LAT - 0.02,
            LON + 0.02,
            LAT + 0.02,
        ],
        datetime=f"{START_DATE}/{END_DATE}",
        query={"eo:cloud_cover": {"lt": 40}},
        max_items=100,
    )

    items = sorted(
        search.items(),
        key=lambda item: item.datetime
    )

    print("Scenes found:", len(items))

    for item in items[:20]:
        print(
            item.id,
            item.datetime,
            "cloud:",
            item.properties.get("eo:cloud_cover"),
        )

        print("Bands:", [
            key for key in item.assets
            if key in ["B02", "B03", "B04", "B05", "B06", "B07"]
        ])
