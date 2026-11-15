from ai.registry import get_ai_status


def test_registry_contains_four_primary_models():
    result = get_ai_status()

    assert result["total"] == 4

    model_ids = {
        model["id"]
        for model in result["models"]
    }

    assert model_ids == {
        "aurora",
        "prithvi",
        "agrifm_e",
        "earth2",
    }


def test_models_are_not_claimed_operational_without_inference():
    result = get_ai_status()

    assert result["operational"] == 0

    for model in result["models"]:
        assert model["status"] in {
            "configuration_present",
            "not_configured",
        }
