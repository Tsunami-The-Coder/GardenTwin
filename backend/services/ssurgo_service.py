from dataclasses import dataclass
import json
import math
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from simulation.contracts import SimulationSite
from simulation.water.soil_properties import SoilHydraulicProperties


SSURGO_URL = (
    "https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest"
)


@dataclass(frozen=True)
class SSURGOResult:
    properties: SoilHydraulicProperties
    map_unit_key: str
    map_unit_name: str
    dominant_component: str
    source: str = "USDA SSURGO / Soil Data Access"


def _number(value):
    """Convert a database value to a finite float, or None."""
    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(result) or result < 0:
        return None

    return result


def _post_query(sql: str, timeout: int = 45) -> list[dict]:
    """Submit a SQL query to USDA Soil Data Access."""
    payload = urlencode({
        "query": sql,
        "format": "JSON+COLUMNNAME",
    }).encode("utf-8")

    request = Request(
        SSURGO_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "GardenTwin/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"USDA SSURGO request failed: {exc}"
        ) from exc

    table = result.get("Table")

    if not isinstance(table, list) or not table:
        return []

    headers = table[0]

    if not isinstance(headers, list):
        raise RuntimeError("Unexpected SSURGO response format.")

    return [
        dict(zip(headers, row))
        for row in table[1:]
        if isinstance(row, list)
    ]


def _aggregate_horizons(
    rows: list[dict],
    root_depth_cm: float,
) -> tuple[dict, str, str, str] | None:
    """
    Aggregate horizon properties over the requested root depth.

    Horizon thickness and component percentage are used as weights.
    Only the map unit with the largest representative component
    percentage is selected when a point intersects multiple map units.
    """
    if not rows:
        return None

    # Select the map unit whose largest component has the
    # highest representative percentage.
    mapunit_scores = {}

    for row in rows:
        mukey = str(row.get("mukey", ""))
        percentage = _number(row.get("comppct_r"))

        if mukey and percentage is not None:
            mapunit_scores[mukey] = max(
                mapunit_scores.get(mukey, 0),
                percentage,
            )

    if not mapunit_scores:
        return None

    selected_mukey = max(
        mapunit_scores,
        key=mapunit_scores.get,
    )

    selected_rows = [
        row for row in rows
        if str(row.get("mukey", "")) == selected_mukey
    ]

    component_names = {}
    weighted_values = {
        "wilting_point": [],
        "field_capacity": [],
        "saturation": [],
        "ksat_mm_day": [],
    }

    for row in selected_rows:
        component = str(row.get("compname") or "Unknown")
        percentage = _number(row.get("comppct_r"))
        top = _number(row.get("hzdept_r"))
        bottom = _number(row.get("hzdepb_r"))

        if (
            percentage is None
            or top is None
            or bottom is None
            or bottom <= top
        ):
            continue

        overlap = max(
            0.0,
            min(bottom, root_depth_cm) - max(top, 0.0),
        )

        if overlap <= 0:
            continue

        weight = percentage * overlap
        component_names[component] = percentage

        # SSURGO water-content fields are percentages.
        saturation = _number(row.get("wsatiated_r"))
        field_capacity = _number(row.get("wthirdbar_r"))

        # Some sandy horizons use the 1/10-bar field instead.
        if field_capacity is None:
            field_capacity = _number(row.get("wtenthbar_r"))

        wilting_point = _number(row.get("wfifteenbar_r"))

        # SSURGO Ksat is in micrometers/second.
        ksat = _number(row.get("ksat_r"))

        values = {
            "wilting_point": wilting_point,
            "field_capacity": field_capacity,
            "saturation": saturation,
            "ksat_mm_day": (
                ksat * 86.4 if ksat is not None else None
            ),
        }

        for name, value in values.items():
            if value is not None:
                if name in (
                    "wilting_point",
                    "field_capacity",
                    "saturation",
                ):
                    value /= 100.0

                weighted_values[name].append(
                    (value, weight)
                )

    def weighted_mean(name):
        values = weighted_values[name]

        if not values:
            return None

        total_weight = sum(weight for _, weight in values)

        if total_weight <= 0:
            return None

        return sum(
            value * weight for value, weight in values
        ) / total_weight

    properties = {
        name: weighted_mean(name)
        for name in weighted_values
    }

    # All four hydraulic properties are required by our
    # current simulation model.
    if any(value is None for value in properties.values()):
        return None

    dominant_component = max(
        component_names,
        key=component_names.get,
        default="Unknown",
    )

    map_unit_name = str(
        selected_rows[0].get("muname") or "Unknown map unit"
    )

    return (
        properties,
        selected_mukey,
        map_unit_name,
        dominant_component,
    )


def fetch_ssurgo_soil(
    site: SimulationSite,
    root_depth_cm: float = 30.0,
    timeout: int = 45,
) -> SSURGOResult | None:
    """
    Fetch soil hydraulic properties for a geographic point.

    Returns None when the location has no usable SSURGO
    hydraulic data. Network and service errors raise RuntimeError.
    """
    if not -90 <= site.latitude <= 90:
        raise ValueError("Invalid latitude.")

    if not -180 <= site.longitude <= 180:
        raise ValueError("Invalid longitude.")

    if not math.isfinite(root_depth_cm) or root_depth_cm <= 0:
        raise ValueError("root_depth_cm must be positive.")

    if timeout <= 0:
        raise ValueError("timeout must be positive.")

    # WKT uses longitude first, then latitude.
    point = f"POINT({site.longitude} {site.latitude})"

    sql = f"""
    SELECT
        mapunit.mukey,
        mapunit.muname,
        component.compname,
        component.comppct_r,
        chorizon.hzdept_r,
        chorizon.hzdepb_r,
        chorizon.wsatiated_r,
        chorizon.wthirdbar_r,
        chorizon.wtenthbar_r,
        chorizon.wfifteenbar_r,
        chorizon.ksat_r
    FROM mapunit
    INNER JOIN component
        ON mapunit.mukey = component.mukey
    INNER JOIN chorizon
        ON component.cokey = chorizon.cokey
    WHERE mapunit.mukey IN (
        SELECT mukey
        FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
            '{point}'
        )
    )
      AND component.majcompflag = 'Yes'
      AND component.comppct_r IS NOT NULL
      AND chorizon.hzdept_r < {float(root_depth_cm)}
      AND chorizon.hzdepb_r > 0
    ORDER BY component.comppct_r DESC,
             chorizon.hzdept_r ASC
    """

    rows = _post_query(sql, timeout=timeout)

    aggregated = _aggregate_horizons(
        rows,
        root_depth_cm,
    )

    if aggregated is None:
        return None

    values, mukey, map_unit_name, component_name = aggregated

    try:
        properties = SoilHydraulicProperties(
            wilting_point=values["wilting_point"],
            field_capacity=values["field_capacity"],
            saturation=values["saturation"],
            saturated_hydraulic_conductivity_mm_day=(
                values["ksat_mm_day"]
            ),
            root_depth_cm=root_depth_cm,
        )
    except ValueError:
        # Invalid or internally inconsistent USDA values
        # should not silently enter the simulation.
        return None

    return SSURGOResult(
        properties=properties,
        map_unit_key=mukey,
        map_unit_name=map_unit_name,
        dominant_component=component_name,
    )
