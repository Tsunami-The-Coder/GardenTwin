
from datetime import datetime

import torch
from aurora import AuroraSmallPretrained, Batch, Metadata

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading Aurora Small...")
model = AuroraSmallPretrained()
model.load_checkpoint()
model.eval()
model = model.to(device)

print("Building test input...")

# Synthetic test data only; not observed weather.
batch = Batch(
    surf_vars={
        key: torch.randn(1, 2, 17, 32)
        for key in ("2t", "10u", "10v", "msl")
    },
    static_vars={
        key: torch.randn(17, 32)
        for key in ("lsm", "z", "slt")
    },
    atmos_vars={
        key: torch.randn(1, 2, 4, 17, 32)
        for key in ("z", "u", "v", "t", "q")
    },
    metadata=Metadata(
        lat=torch.linspace(90, -90, 17),
        lon=torch.linspace(0, 360, 33)[:-1],
        time=(datetime(2025, 6, 2, 12),),
        atmos_levels=(100, 250, 500, 850),
    ),
)

print("Running pretrained inference...")

with torch.inference_mode():
    prediction = model.forward(batch)

temperature = prediction.surf_vars["2t"]

print("INFERENCE SUCCESS")
print("Temperature output shape:", tuple(temperature.shape))
print("Finite values:", bool(torch.isfinite(temperature).all()))
print("Output mean:", temperature.float().mean().item())

torch.save(
    prediction.to("cpu"),
    "data/aurora_smoke_test.pt",
)

print("Saved: data/aurora_smoke_test.pt")
