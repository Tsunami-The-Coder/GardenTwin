from datetime import date

import pytest

from backend.schemas.simulation import SimulationRequest
from backend.services import simulation_service
from backend.services.ssurgo_service import SSURGOResult
from simulation.contracts import SimulationRun, SimulationSite
from simulation.water.soil_properties import SoilHydraulicProperties


def make_request(soil_mode="auto"):
    return SimulationRequest(
        location_name="Test Garden",
        latitude=39.4273,
        longitude=-75.2341,
        crop_name="Tomato",
        planting_date=date(2025, 6, 1),
        start_date=date(2025, 6, 1),
        end_date=date(2025, 6, 3),
        soil_mode=soil_mode,
    )


def make_soil_properties():
    return SoilHydraulicProperties(
        wilting_point=0.10,
        field_capacity=0.25,
        saturation=0.42,
        saturated_hydraulic_conductivity_mm_day=20.0,
        root_depth_cm=30.0,
    )


def make_ssurgo_result():
    return SSURGOResult(
        properties=make_soil_properties(),
        map_unit_key="12345",
        map_unit_name="Test soil map unit",
        dominant_component="Test soil",
    )


def install_fake_weather(monkeypatch):
    monkeypatch.setattr(
        simulation_service,
        "fetch_nasa_power_weather",
        lambda **kwargs: [object()],
    )


def install_fake_season(monkeypatch):
    def fake_season(**kwargs):
        return SimulationRun(
            run_id=kwargs["run_id"],
            site=kwargs["site"],
            crop_name=kwargs["initial_crop"].crop_name,
            planting_date=kwargs["planting_date"],
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 3),
        )

    monkeypatch.setattr(
        simulation_service,
        "simulate_season",
        fake_season,
    )


def test_auto_mode_uses_ssurgo_when_available(monkeypatch):
    install_fake_weather(monkeypatch)
    install_fake_season(monkeypatch)

    monkeypatch.setattr(
        simulation_service,
        "fetch_ssurgo_soil",
        lambda **kwargs: make_ssurgo_result(),
    )

    run = simulation_service.run_garden_simulation(
        make_request("auto")
    )

    assert run.soil_data_source == "USDA SSURGO / Soil Data Access"
    assert run.soil_map_unit_key == "12345"
    assert run.soil_map_unit_name == "Test soil map unit"
    assert run.soil_properties["field_capacity"] == 0.25


def test_auto_mode_falls_back_when_ssurgo_has_no_data(monkeypatch):
    install_fake_weather(monkeypatch)
    install_fake_season(monkeypatch)

    monkeypatch.setattr(
        simulation_service,
        "fetch_ssurgo_soil",
        lambda **kwargs: None,
    )

    run = simulation_service.run_garden_simulation(
        make_request("auto")
    )

    assert run.soil_data_source == "Manual user inputs"
    assert run.soil_lookup_note is not None
    assert run.soil_properties["field_capacity"] == 0.30


def test_auto_mode_falls_back_when_ssurgo_request_fails(monkeypatch):
    install_fake_weather(monkeypatch)
    install_fake_season(monkeypatch)

    def failed_lookup(**kwargs):
        raise RuntimeError("Service unavailable")

    monkeypatch.setattr(
        simulation_service,
        "fetch_ssurgo_soil",
        failed_lookup,
    )

    run = simulation_service.run_garden_simulation(
        make_request("auto")
    )

    assert run.soil_data_source == "Manual user inputs"
    assert "Service unavailable" in run.soil_lookup_note


def test_ssurgo_mode_requires_usable_data(monkeypatch):
    install_fake_weather(monkeypatch)
    install_fake_season(monkeypatch)

    monkeypatch.setattr(
        simulation_service,
        "fetch_ssurgo_soil",
        lambda **kwargs: None,
    )

    with pytest.raises(RuntimeError, match="no usable hydraulic"):
        simulation_service.run_garden_simulation(
            make_request("ssurgo")
        )


def test_manual_mode_skips_ssurgo(monkeypatch):
    install_fake_weather(monkeypatch)
    install_fake_season(monkeypatch)

    def unexpected_lookup(**kwargs):
        raise AssertionError("SSURGO should not be called in manual mode")

    monkeypatch.setattr(
        simulation_service,
        "fetch_ssurgo_soil",
        unexpected_lookup,
    )

    run = simulation_service.run_garden_simulation(
        make_request("manual")
    )

    assert run.soil_data_source == "Manual user inputs"
    assert run.soil_map_unit_key is None
