from pathlib import Path
import numpy as np
import rasterio
import torch
from terratorch.registry import BACKBONE_REGISTRY

FILES = [
    Path("data/prithvi/2025-06-02.tif"),
    Path("data/prithvi/2025-06-25.tif"),
    Path("data/prithvi/2025-07-25.tif"),
    Path("data/prithvi/2025-08-29.tif"),
]

# HLS reflectance normalization reference values.
# These are published in the Prithvi HLS burn-scar task config;
# they are not claimed to be the original pretraining statistics.
MEANS = np.array([
    0.0333497067, 0.0570118552, 0.0588974813,
    0.2323245113, 0.1972854854, 0.1194491423
], dtype=np.float32)

STDS = np.array([
    0.0226913557, 0.0268075602, 0.0400410984,
    0.0779173242, 0.0870873884, 0.0724197948
], dtype=np.float32)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

frames = []

for path in FILES:
    if not path.exists():
        raise FileNotFoundError(path)

    with rasterio.open(path) as src:
        image = src.read().astype(np.float32)
        nodata = src.nodata

    if image.shape != (6, 224, 224):
        raise ValueError(f"Unexpected shape in {path}: {image.shape}")

    # Convert HLS scaled integer values into reflectance units.
    image /= 10000.0

    # Replace missing pixels with the per-band mean.
    # After normalization, these pixels become zero.
    valid = np.isfinite(image)
    if nodata is not None:
        valid &= (image * 10000.0 != nodata)

    for band in range(6):
        band_valid = valid[band]

        if not band_valid.any():
            raise ValueError(f"No valid pixels in {path}, band {band}")

        image[band, ~band_valid] = MEANS[band]

    image = (image - MEANS[:, None, None]) / STDS[:, None, None]

    frames.append(image)

    print(
        f"{path.name}: "
        f"valid pixels={int(valid.sum())}/{valid.size}, "
        f"normalized range={image.min():.2f} to {image.max():.2f}"
    )

# Shape: [batch, channels, time, height, width]
array = np.stack(frames, axis=1)
tensor = torch.from_numpy(array).unsqueeze(0).to(device)

print("Input tensor:", tuple(tensor.shape))

print("\nLoading pretrained Prithvi-EO-2.0 300M...")

model = BACKBONE_REGISTRY.build(
    "prithvi_eo_v2_300",
    pretrained=True,
    num_frames=4,
)

model = model.eval().to(device=device, dtype=torch.float16)

print("Model loaded.")
print("Parameters:", sum(p.numel() for p in model.parameters()))

print("\nRunning actual pretrained inference...")

with torch.inference_mode():
    with torch.autocast(
        device_type="cuda" if device.type == "cuda" else "cpu",
        dtype=torch.float16,
        enabled=(device.type == "cuda"),
    ):
        output = model(tensor)

def describe(value, depth=0):
    prefix = "  " * depth

    if isinstance(value, torch.Tensor):
        print(
            f"{prefix}Tensor shape={tuple(value.shape)}, "
            f"dtype={value.dtype}, "
            f"finite={bool(torch.isfinite(value).all())}"
        )
        return

    if isinstance(value, (list, tuple)):
        print(f"{prefix}{type(value).__name__}, length={len(value)}")
        for item in value:
            describe(item, depth + 1)
        return

    if isinstance(value, dict):
        print(f"{prefix}Dictionary keys={list(value.keys())}")
        for key, item in value.items():
            print(f"{prefix}{key}:")
            describe(item, depth + 1)
        return

    print(f"{prefix}{type(value).__name__}: {value}")

print("\nMODEL OUTPUT:")
describe(output)

output_dir = Path("data/prithvi")
output_dir.mkdir(exist_ok=True)

# Store the actual model features for downstream use.
torch.save(
    {
        "model": "Prithvi-EO-2.0-300M",
        "dates": [p.stem for p in FILES],
        "features": output,
    },
    output_dir / "prithvi_features.pt",
)

print("\nSaved actual pretrained features:")
print("data/prithvi/prithvi_features.pt")
