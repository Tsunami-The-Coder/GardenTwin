"""Load and summarize verified pretrained-model inference artifacts."""

from pathlib import Path

import torch
import json
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]

def _find_artifact(*paths):
    for path in paths:
        if path.is_file():
            return path
    return paths[0]


AURORA_ARTIFACT = _find_artifact(
    PROJECT_ROOT / "data" / "aurora_real_prediction.pt",
    PROJECT_ROOT / "ai" / "data" / "aurora_real_prediction.pt",
)

PRITHVI_ARTIFACT = _find_artifact(
    PROJECT_ROOT / "data" / "prithvi" / "prithvi_features.pt",
    PROJECT_ROOT / "ai" / "data" / "prithvi" / "prithvi_features.pt",
)
EARTH2_ARTIFACT = _find_artifact(
    PROJECT_ROOT / "data" / "earth2_garden_forecast.json",
    PROJECT_ROOT / "ai" / "data" / "earth2_garden_forecast.json",
)


def _load_torch_file(path):
    if not path.is_file():
        raise FileNotFoundError(f"Inference artifact not found: {path}")

    try:
        return torch.load(
            path,
            map_location="cpu",
            weights_only=False,
        )
    except TypeError:
        # Compatibility with older PyTorch versions.
        return torch.load(path, map_location="cpu")


def load_aurora_result():
    """Summarize the actual saved AuroraSmall prediction."""

    artifact = _load_torch_file(AURORA_ARTIFACT)

    prediction = artifact["prediction"]
    temperature = prediction.surf_vars["2t"].float()

    if temperature.numel() == 0:
        raise ValueError("Aurora prediction contains no values.")

    if not bool(torch.isfinite(temperature).all()):
        raise ValueError("Aurora prediction contains non-finite values.")

    celsius = temperature - 273.15

    return {
        "system": "aurora",
        "model": "Microsoft Aurora Small",
        "status": "pretrained_inference_artifact",
        "method": "cached_aurora_small_forecast",
        "input_source": artifact.get("source", "ERA5"),
        "initialization_time": artifact.get(
            "initialization", "unknown"
        ),
        "output": {
            "variable": "2m_temperature",
            "shape": list(temperature.shape),
            "grid_mean_temperature_c": round(
                celsius.mean().item(), 3
            ),
            "grid_min_temperature_c": round(
                celsius.min().item(), 3
            ),
            "grid_max_temperature_c": round(
                celsius.max().item(), 3
            ),
            "finite": True,
            "interpretation": (
                "These statistics come from an actual pretrained "
                "Aurora Small prediction using historical ERA5 input. "
                "They describe the saved regional model output, not "
                "a live forecast or a calibrated garden-level prediction."
            ),
        },
        "artifact": str(AURORA_ARTIFACT.relative_to(PROJECT_ROOT)),
    }


def _collect_tensors(value, output):
    if isinstance(value, torch.Tensor):
        output.append(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_tensors(item, output)
    elif isinstance(value, dict):
        for item in value.values():
            _collect_tensors(item, output)


def load_prithvi_result():
    """Summarize actual Prithvi-EO-2.0 learned feature tensors."""

    artifact = _load_torch_file(PRITHVI_ARTIFACT)

    tensors = []
    _collect_tensors(artifact["features"], tensors)

    if not tensors:
        raise ValueError("Prithvi artifact contains no feature tensors.")

    final_features = tensors[-1].float()

    if final_features.numel() == 0:
        raise ValueError("Prithvi final feature tensor is empty.")

    if not bool(torch.isfinite(final_features).all()):
        raise ValueError("Prithvi features contain non-finite values.")

    dates = artifact.get("dates", [])

    return {
        "system": "prithvi",
        "model": "NASA/IBM Prithvi-EO-2.0 300M",
        "status": "pretrained_inference_artifact",
        "method": "cached_prithvi_satellite_feature_extraction",
        "input_source": "NASA/USGS Harmonized Landsat Sentinel imagery",
        "observation_dates": dates,
        "output": {
            "feature_tensor_count": len(tensors),
            "feature_shapes": [
                list(tensor.shape) for tensor in tensors
            ],
            "final_feature_shape": list(final_features.shape),
            "final_feature_mean": round(
                final_features.mean().item(), 6
            ),
            "final_feature_std": round(
                final_features.std(unbiased=False).item(), 6
            ),
            "final_feature_min": round(
                final_features.min().item(), 6
            ),
            "final_feature_max": round(
                final_features.max().item(), 6
            ),
            "finite": True,
            "interpretation": (
                "These are actual learned feature representations "
                "from pretrained Prithvi-EO-2.0 using four HLS "
                "satellite observations. They are not a trained "
                "crop-health classification, soil measurement, "
                "or direct vegetation-condition score."
            ),
        },
        "artifact": str(PRITHVI_ARTIFACT.relative_to(PROJECT_ROOT)),
    }
def _parse_utc(value):
    """Parse an ISO timestamp, treating timezone-naive GFS times as UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def load_earth2_result():
    """Load and summarize the saved NVIDIA FourCastNet1 inference."""

    if not EARTH2_ARTIFACT.is_file():
        raise FileNotFoundError(
            f"Earth-2 inference artifact not found: {EARTH2_ARTIFACT}"
        )

    with EARTH2_ARTIFACT.open("r", encoding="utf-8") as file:
        artifact = json.load(file)

    required = (
        "model",
        "source",
        "location",
        "initialization_time",
        "forecast_valid_time",
        "forecast_lead_hours",
        "weather",
    )

    missing = [key for key in required if key not in artifact]
    if missing:
        raise ValueError(
            f"Earth-2 artifact is missing fields: {missing}"
        )

    weather = artifact["weather"]
    required_weather = (
        "temperature_c",
        "wind_speed_10m_m_s",
        "mean_sea_level_pressure_hpa",
        "total_column_water_kg_m2",
    )

    for key in required_weather:
        if key not in weather:
            raise ValueError(
                f"Earth-2 artifact is missing weather field: {key}"
            )

        value = float(weather[key])
        if not torch.isfinite(torch.tensor(value)):
            raise ValueError(
                f"Earth-2 weather field {key} is non-finite."
            )

    initialization = _parse_utc(artifact["initialization_time"])
    valid_time = _parse_utc(artifact["forecast_valid_time"])
    is_stale = valid_time <= datetime.now(timezone.utc)

    return {
        "system": "earth2",
        "model": "NVIDIA FourCastNet1 via Earth2Studio",
        "status": "pretrained_inference_artifact",
        "method": "cached_fourcastnet1_gfs_forecast",
        "input_source": artifact["source"],
        "initialization_time": initialization.isoformat(),
        "forecast_valid_time": valid_time.isoformat(),
        "forecast_lead_hours": artifact["forecast_lead_hours"],
        "forecast_status": "stale" if is_stale else "upcoming",
        "location": artifact["location"],
        "output": {
            "temperature_c": weather["temperature_c"],
            "wind_u_10m_m_s": weather.get("wind_u_10m_m_s"),
            "wind_v_10m_m_s": weather.get("wind_v_10m_m_s"),
            "wind_speed_10m_m_s": weather["wind_speed_10m_m_s"],
            "mean_sea_level_pressure_hpa": (
                weather["mean_sea_level_pressure_hpa"]
            ),
            "total_column_water_kg_m2": (
                weather["total_column_water_kg_m2"]
            ),
            "interpretation": (
                "This is an actual pretrained NVIDIA FourCastNet1 "
                "forecast generated through Earth2Studio using GFS "
                "input. It is a saved forecast for the recorded "
                "garden location, not a new inference for every API "
                "request. Total column water vapor is not rainfall. "
                + (
                    "The forecast valid time has already passed; "
                    "this result is retained as a historical inference "
                    "artifact and must not be presented as upcoming."
                    if is_stale else
                    "The forecast valid time is still in the future."
                )
            ),
        },
        "artifact": str(EARTH2_ARTIFACT.relative_to(PROJECT_ROOT)),
    }
