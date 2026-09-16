"""Focused regression tests for derived advertising conversion metrics."""

import ibis
import pandas as pd

from transforms import (
    last_contiguous_run_ad_metrics_transform,
    lifetime_ad_conversions_transform,
)


def _run_lifetime_conversion_transform(leads, events):
    connection = ibis.duckdb.connect()
    tables = {
        "leads": connection.create_table("leads", pd.DataFrame(leads)),
        "events": connection.create_table("events", pd.DataFrame(events)),
    }
    return lifetime_ad_conversions_transform(tables)


def _run_last_contiguous_run_transform(runs, ads):
    connection = ibis.duckdb.connect()
    tables = {
        "perf": connection.create_table("perf", pd.DataFrame(runs)),
        "ads": connection.create_table("ads", pd.DataFrame(ads)),
    }
    return last_contiguous_run_ad_metrics_transform(tables)


def test_lifetime_conversions_exclude_special_event_rows():
    result = _run_lifetime_conversion_transform(
        leads=[
            {
                "id": 1,
                "Campaign": "Mens campaign",
                "Ad": "Mens Ad B",
                "Status": "Interested",
            },
            {
                "id": 2,
                "Campaign": "Mens campaign",
                "Ad": "Mens Ad B",
                "Status": "Special event",
            },
        ],
        events=[
            {"Lead_id": 1, "Event": "Interest"},
            # Even a malformed conversion event must not make a Special-event
            # placeholder appear in an ad's lead or registration totals.
            {"Lead_id": 2, "Event": "Registration"},
        ],
    )

    row = result.iloc[0]
    assert row["Leads_Attributed"] == 1
    assert row["Leads_Registered"] == 0
    assert row["Registration_Conversion_Rate"] == 0


def test_return_events_do_not_count_as_new_ad_acquisitions():
    result = _run_lifetime_conversion_transform(
        leads=[
            {
                "id": 1,
                "Campaign": "Womens Campaign",
                "Ad": "Womens Ad A",
                "Status": "Registered",
            },
            {
                "id": 2,
                "Campaign": "Womens Campaign",
                "Ad": "Womens Ad A",
                "Status": "Reactivated",
            },
        ],
        events=[
            {"Lead_id": 1, "Event": "Registration"},
            {"Lead_id": 1, "Event": "Return"},
            {"Lead_id": 2, "Event": "Return"},
        ],
    )

    row = result.iloc[0]
    assert row["Leads_Attributed"] == 2
    # A lead with Registration + Return is still one acquisition; a lead with
    # Return only is not a new acquisition.
    assert row["Leads_Registered"] == 1
    assert row["Registration_Conversion_Rate"] == 0.5


def test_last_run_excludes_incidental_delivery_from_boundaries_and_bridges():
    result = _run_last_contiguous_run_transform(
        runs=[
            {
                "Week": "2026-W34",
                "Ad_id": 1,
                "Spend": 100.0,
                "Leads": 2,
                "Intended_run": "True",
            },
            {
                "Week": "2026-W35",
                "Ad_id": 1,
                "Spend": 7.0,
                "Leads": 0,
                "Intended_run": "False",
            },
            {
                "Week": "2026-W36",
                "Ad_id": 1,
                "Spend": 120.0,
                "Leads": 3,
                "Intended_run": "True",
            },
            {
                "Week": "2026-W37",
                "Ad_id": 1,
                "Spend": 5.0,
                "Leads": 0,
                "Intended_run": "False",
            },
            {
                "Week": "2026-W37",
                "Ad_id": 2,
                "Spend": 9.0,
                "Leads": 1,
                "Intended_run": "False",
            },
        ],
        ads=[
            {"id": 1, "Name": "Mens Ad B", "Campaign": "M"},
            {"id": 2, "Name": "Residual-only Ad", "Campaign": "M"},
        ],
    )

    assert result["Ad"].tolist() == ["Mens Ad B"]
    row = result.iloc[0]
    assert row["Week_last_run_start"] == "2026-W36"
    assert row["Week_last_run_end"] == "2026-W36"
    assert row["Weeks_in_last_run"] == 1
    assert row["Spend_last_run"] == 120.0
    assert row["Leads_last_run"] == 3


def test_last_run_keeps_intended_zero_delivery_week_in_run():
    result = _run_last_contiguous_run_transform(
        runs=[
            {
                "Week": "2026-W35",
                "Ad_id": 1,
                "Spend": 80.0,
                "Leads": 2,
                "Intended_run": True,
            },
            {
                "Week": "2026-W36",
                "Ad_id": 1,
                "Spend": 0.0,
                "Leads": 0,
                "Intended_run": True,
            },
            {
                "Week": "2026-W37",
                "Ad_id": 1,
                "Spend": 4.0,
                "Leads": 0,
                "Intended_run": False,
            },
        ],
        ads=[{"id": 1, "Name": "Womens Ad G", "Campaign": "W"}],
    )

    row = result.iloc[0]
    assert row["Week_last_run_start"] == "2026-W35"
    assert row["Week_last_run_end"] == "2026-W36"
    assert row["Weeks_in_last_run"] == 2
    assert row["Spend_last_run"] == 80.0
    assert row["Leads_last_run"] == 2
    assert row["CPL_last_run"] == 40.0
