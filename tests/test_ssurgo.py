from backend.services.ssurgo_service import _aggregate_horizons


def make_row(
    mukey="123",
    compname="Example soil",
    percentage=80,
    top=0,
    bottom=30,
    saturation=45,
    field_capacity=30,
    wilting_point=12,
    ksat=10,
):
    return {
        "mukey": mukey,
        "muname": "Example map unit",
        "compname": compname,
        "comppct_r": percentage,
        "hzdept_r": top,
        "hzdepb_r": bottom,
        "wsatiated_r": saturation,
        "wthirdbar_r": field_capacity,
        "wtenthbar_r": None,
        "wfifteenbar_r": wilting_point,
        "ksat_r": ksat,
    }


def test_converts_ssurgo_units():
    result = _aggregate_horizons(
        [make_row(ksat=10)],
        30,
    )

    values = result[0]

    assert values["saturation"] == 0.45
    assert values["field_capacity"] == 0.30
    assert values["wilting_point"] == 0.12
    assert values["ksat_mm_day"] == 864.0


def test_uses_only_requested_root_depth():
    rows = [
        make_row(top=0, bottom=10, field_capacity=30),
        make_row(top=10, bottom=30, field_capacity=20),
        make_row(top=30, bottom=60, field_capacity=5),
    ]

    result = _aggregate_horizons(rows, 30)

    # 10 cm at 0.30 and 20 cm at 0.20.
    assert abs(result[0]["field_capacity"] - 0.2333333333) < 1e-8


def test_selects_map_unit_with_largest_component():
    rows = [
        make_row(mukey="A", percentage=40),
        make_row(mukey="B", percentage=75),
    ]

    result = _aggregate_horizons(rows, 30)

    assert result[1] == "B"


def test_returns_none_when_required_data_is_missing():
    row = make_row()
    row["ksat_r"] = None

    assert _aggregate_horizons([row], 30) is None


def test_returns_none_for_no_rows():
    assert _aggregate_horizons([], 30) is None
