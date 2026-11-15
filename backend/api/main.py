from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas.simulation import SimulationRequest
from backend.services.simulation_service import run_garden_simulation
from backend.services.overview_service import build_overview
from backend.services.forecast_service import build_seven_day_forecast

from ai.registry import get_ai_status
from ai.pipelines import analyze_simulation_with_ai

from backend.services.intervention_service import (
    compare_irrigation_intervention,
)


app = FastAPI(
    title="GardenTwin API",
    description="Backend for the GardenTwin gardening simulation.",
    version="1.0.0",
)

# Allow local frontend development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory storage for the hackathon demo.
simulation_runs = {}


@app.get("/health")
def health():
    return {
        "status": "running",
        "application": "GardenTwin",
    }


@app.post("/simulation/run")
def create_simulation(request: SimulationRequest):
    try:
        run = run_garden_simulation(request)

        simulation_runs[run.run_id] = run

        return jsonable_encoder(asdict(run))

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/simulation/{run_id}")
def get_simulation(run_id: str):
    run = simulation_runs.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation not found.",
        )

    return jsonable_encoder(asdict(run))


@app.get("/simulation/{run_id}/overview")
def get_overview(run_id: str, selected_date: str):
    run = simulation_runs.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation not found.",
        )

    from datetime import date

    try:
        overview = build_overview(
            run=run,
            selected_date=date.fromisoformat(selected_date),
        )

        return jsonable_encoder(asdict(overview))

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/ai/status")
def ai_status():
    return get_ai_status()

@app.get("/ai/analyze/{run_id}")
def analyze_run_with_ai(run_id: str):
    run = simulation_runs.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation not found.",
        )

    try:
        return jsonable_encoder(
            analyze_simulation_with_ai(run)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/simulation/{run_id}/intervention/irrigation")
def get_irrigation_intervention(run_id: str):
    run = simulation_runs.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation run not found.",
        )

    try:
        return compare_irrigation_intervention(run)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@app.get("/simulation/{run_id}/forecast")
def get_seven_day_forecast(run_id: str):
    run = simulation_runs.get(run_id)

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Simulation run not found.",
        )

    try:
        return jsonable_encoder(build_seven_day_forecast(run))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))