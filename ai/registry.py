"""Registry describing GardenTwin's four primary AI integrations.

A configuration variable being present does NOT mean that a model
has successfully loaded or produced valid output.
"""

import os
from pathlib import Path

from ai.artifacts import (
    AURORA_ARTIFACT,
    PRITHVI_ARTIFACT,
)

MODEL_DEFINITIONS = [
    {
        "id": "aurora",
        "name": "Microsoft Aurora",
        "category": "weather",
        "role": "Atmospheric conditions and weather intelligence",
        "configuration_variables": [
            "AURORA_MODEL_PATH",
            "AURORA_ENDPOINT",
        ],
        "notes": (
            "Intended for weather intelligence. Historical observations "
            "remain the source for historical-season reconstruction."
        ),
    },
    {
        "id": "prithvi",
        "name": "Prithvi-EO-2.0",
        "category": "satellite",
        "role": "Satellite imagery and land-surface analysis",
        "configuration_variables": [
            "PRITHVI_MODEL_PATH",
            "PRITHVI_ENDPOINT",
        ],
        "notes": (
            "Requires suitable multispectral satellite imagery and "
            "preprocessing. Not a direct backyard soil test."
        ),
    },
    {
        "id": "agrifm_e",
        "name": "AgriFM-E",
        "category": "agriculture",
        "role": "Agricultural environmental intelligence",
        "configuration_variables": [
            "AGRIFM_E_MODEL_PATH",
            "AGRIFM_E_ENDPOINT",
        ],
        "notes": (
            "Checkpoint and inference access must be verified before "
            "this integration can be marked operational."
        ),
    },
    {
        "id": "earth2",
        "name": "NVIDIA Earth-2",
        "category": "weather",
        "role": "Weather modeling and spatial refinement",
        "configuration_variables": [
            "EARTH2_ENDPOINT",
        ],
        "notes": (
            "Intended as an optional weather-modeling integration. "
            "It should complement, not silently replace, historical data."
        ),
    },
]


def get_ai_status() -> dict:
    """Report configuration and inference-artifact availability separately."""

    artifact_paths = {
        "aurora": AURORA_ARTIFACT,
        "prithvi": PRITHVI_ARTIFACT,
        "earth2": (
            Path(__file__).resolve().parents[1]
            / "data"
            / "earth2_garden_forecast.json"
        ),
    }

    models = []

    for definition in MODEL_DEFINITIONS:
        model_id = definition["id"]

        configured_variables = [
            variable
            for variable in definition["configuration_variables"]
            if os.getenv(variable)
        ]

        artifact_path = artifact_paths.get(model_id)
        artifact_present = (
            artifact_path.is_file()
            if artifact_path is not None
            else False
        )

        models.append({
            "id": model_id,
            "name": definition["name"],
            "category": definition["category"],
            "role": definition["role"],
            "status": (
                "configuration_present"
                if configured_variables
                else "not_configured"
            ),
            "configured_variables": configured_variables,
            "inference_artifact_present": artifact_present,
            "notes": definition["notes"],
        })

    return {
        "models": models,
        "total": len(models),
        "configuration_present": sum(
            model["status"] == "configuration_present"
            for model in models
        ),
        "inference_artifacts_present": sum(
            model["inference_artifact_present"]
            for model in models
        ),
        "operational": 0,
        "important_note": (
            "Artifact presence confirms a saved inference result exists, "
            "not that the model is loaded or running live. Operational "
            "status requires a successful inference execution."
        ),
    }