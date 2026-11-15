"""Build the decision-focused overview from simulation records."""

from dataclasses import dataclass
from datetime import date, timedelta

from simulation.contracts import DailySimulationRecord, SimulationRun


@dataclass
class OverviewResponse:
    selected_date: date
    crop_name: str
    location_name: str

    today: DailySimulationRecord
    next_7_days: list[DailySimulationRecord]

    alerts: list[str]


def build_overview(
    run: SimulationRun,
    selected_date: date,
) -> OverviewResponse:
    """Return the selected day's data and the following seven days."""

    records_by_date = {
        record.date: record
        for record in run.records
    }

    required_dates = [
        selected_date + timedelta(days=offset)
        for offset in range(8)
    ]

    missing_dates = [
        day for day in required_dates
        if day not in records_by_date
    ]

    if missing_dates:
        formatted = ", ".join(day.isoformat() for day in missing_dates)
        raise ValueError(
            f"Cannot build a complete 7-day overview. Missing: {formatted}"
        )

    today = records_by_date[selected_date]
    next_7_days = [
        records_by_date[selected_date + timedelta(days=offset)]
        for offset in range(1, 8)
    ]

    return OverviewResponse(
        selected_date=selected_date,
        crop_name=run.crop_name,
        location_name=run.site.location_name,
        today=today,
        next_7_days=next_7_days,
        alerts=today.alerts,
    )
