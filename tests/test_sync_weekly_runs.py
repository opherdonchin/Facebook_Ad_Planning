"""Regression tests for Meta weekly performance capture and aggregation."""

import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import sync_weekly_runs as sync_module

from sync_weekly_runs import (
    SNAPSHOT_CHECKSUM_FIELD,
    aggregate_to_weeks,
    build_arg_parser,
    build_existing_weekly_lookup,
    build_source_snapshot,
    date_to_unix,
    load_source_snapshot,
    parse_lead_count,
    parse_spend_amount,
    snapshot_checksum,
    validate_weekly_reporting_range,
    write_source_snapshot,
)


LEAD_ACTION_TYPES = ["onsite_conversion.lead_grouped", "lead"]


def _row(day, spend, actions, *, ad_id="meta-ad-123", ad_name="Mens Ad J"):
    return {
        "ad_id": ad_id,
        "ad_name": ad_name,
        "date_start": day,
        "date_stop": day,
        "spend": str(spend),
        "actions": actions,
    }


def _key(day=date(2026, 9, 16), ad_id="meta-ad-123", ad_name="Mens Ad J"):
    return (ad_id, ad_name, day)


def test_lead_aliases_are_fallbacks_not_additive():
    rows = [
        _row(
            "2026-09-14",
            32.73,
            [
                {"action_type": "lead", "value": "1"},
                {"action_type": "onsite_conversion.lead_grouped", "value": "1"},
            ],
        ),
        _row(
            "2026-09-15",
            32.62,
            [
                {"action_type": "lead", "value": "1"},
                {"action_type": "onsite_conversion.lead_grouped", "value": "1"},
            ],
        ),
    ]

    result = aggregate_to_weeks(rows, LEAD_ACTION_TYPES)

    assert result[_key()] == {
        "spend": Decimal("65.35"),
        "leads": 2,
    }


@pytest.mark.parametrize(
    "action_type",
    ["onsite_conversion.lead_grouped", "lead"],
)
def test_each_lead_action_type_works_as_a_fallback(action_type):
    result = aggregate_to_weeks(
        [
            _row(
                "2026-09-14",
                10,
                [{"action_type": action_type, "value": "2"}],
            )
        ],
        LEAD_ACTION_TYPES,
    )

    assert result[_key()]["leads"] == 2


def test_disagreeing_lead_aliases_stop_the_sync():
    rows = [
        _row(
            "2026-09-14",
            10,
            [
                {"action_type": "onsite_conversion.lead_grouped", "value": "1"},
                {"action_type": "lead", "value": "2"},
            ],
        )
    ]

    with pytest.raises(ValueError, match="lead action aliases disagree"):
        aggregate_to_weeks(rows, LEAD_ACTION_TYPES)


def test_zero_lead_row_keeps_spend_without_inventing_a_lead():
    result = aggregate_to_weeks(
        [
            _row(
                "2026-09-13",
                34.38,
                [{"action_type": "link_click", "value": "4"}],
            )
        ],
        LEAD_ACTION_TYPES,
    )

    assert result[_key()] == {
        "spend": Decimal("34.38"),
        "leads": 0,
    }


def test_thursday_starts_a_new_reporting_week():
    rows = [
        _row(
            "2026-09-16",
            5,
            [{"action_type": "onsite_conversion.lead_grouped", "value": "1"}],
        ),
        _row(
            "2026-09-17",
            7,
            [{"action_type": "onsite_conversion.lead_grouped", "value": "1"}],
        ),
    ]

    result = aggregate_to_weeks(rows, LEAD_ACTION_TYPES)

    assert result[_key()]["leads"] == 1
    assert result[_key(date(2026, 9, 23))]["leads"] == 1


@pytest.mark.parametrize("value", [None, "", True, "1.5", "-1", "NaN", "Infinity", "abc"])
def test_invalid_lead_values_fail_closed(value):
    with pytest.raises(ValueError, match="lead count"):
        parse_lead_count(value, "test row")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), ("0", 0), (2, 2), ("2.0", 2)],
)
def test_nonnegative_integral_lead_values_are_accepted(value, expected):
    assert parse_lead_count(value, "test row") == expected


@pytest.mark.parametrize(
    "value",
    [None, "", True, False, "-0.01", "NaN", "Infinity", "-Infinity", "abc"],
)
def test_invalid_spend_values_fail_closed(value):
    with pytest.raises(ValueError, match="Meta spend"):
        parse_spend_amount(value, "test row")


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, Decimal("0")), ("0.00", Decimal("0.00")), ("32.73", Decimal("32.73"))],
)
def test_finite_nonnegative_spend_is_parsed_exactly(value, expected):
    assert parse_spend_amount(value, "test row") == expected


def test_duplicate_lead_action_type_stops_the_sync():
    row = _row(
        "2026-09-14",
        10,
        [
            {"action_type": "lead", "value": "1"},
            {"action_type": "lead", "value": "1"},
        ],
    )

    with pytest.raises(ValueError, match="appears more than once"):
        aggregate_to_weeks([row], LEAD_ACTION_TYPES)


def test_missing_meta_ad_id_stops_the_sync():
    row = _row("2026-09-14", 10, [], ad_id="")

    with pytest.raises(ValueError, match="missing ad_id"):
        aggregate_to_weeks([row], LEAD_ACTION_TYPES)


def test_meta_identity_is_retained_in_aggregate_keys():
    rows = [
        _row("2026-09-14", 10, [], ad_id="111", ad_name="Mens Ad J"),
        _row("2026-09-14", 20, [], ad_id="222", ad_name="Womens Ad G"),
    ]

    result = aggregate_to_weeks(rows, LEAD_ACTION_TYPES)

    assert ("111", "Mens Ad J", date(2026, 9, 16)) in result
    assert ("222", "Womens Ad G", date(2026, 9, 16)) in result


def test_same_meta_name_with_multiple_ids_stops_instead_of_merging():
    rows = [
        _row("2026-09-14", 10, [], ad_id="111", ad_name="Mens Ad J"),
        _row("2026-09-15", 20, [], ad_id="222", ad_name="Mens Ad J"),
    ]

    with pytest.raises(ValueError, match="maps to multiple IDs"):
        aggregate_to_weeks(rows, LEAD_ACTION_TYPES)


def test_duplicate_meta_ad_day_stops_instead_of_double_counting():
    row = _row("2026-09-14", 10, [])

    with pytest.raises(ValueError, match="Duplicate Meta daily row"):
        aggregate_to_weeks([row, dict(row)], LEAD_ACTION_TYPES)


def test_existing_partial_week_date_maps_to_canonical_wednesday():
    partial_week_ts = date_to_unix(date(2026, 6, 6))
    canonical_week_ts = date_to_unix(date(2026, 6, 10))

    result = build_existing_weekly_lookup(
        [{"id": 199, "Week": partial_week_ts, "Ad": 24}]
    )

    assert result == {(canonical_week_ts, 24): 199}


def test_partial_and_canonical_rows_for_same_week_are_rejected():
    records = [
        {"id": 199, "Week": date_to_unix(date(2026, 6, 6)), "Ad": 24},
        {"id": 204, "Week": date_to_unix(date(2026, 6, 10)), "Ad": 24},
    ]

    with pytest.raises(ValueError, match="Duplicate Grist Weekly_runs rows"):
        build_existing_weekly_lookup(records)


def test_explicit_until_is_available_on_the_cli():
    args = build_arg_parser().parse_args(
        [
            "--since",
            "2026-09-10",
            "--until",
            "2026-09-16",
            "--snapshot-in",
            "snapshot.json",
        ]
    )

    assert args.since == "2026-09-10"
    assert args.until == "2026-09-16"


def test_weekly_reporting_range_requires_exact_thursday_to_wednesday():
    validate_weekly_reporting_range(date(2026, 9, 10), date(2026, 9, 16))
    validate_weekly_reporting_range(date(2026, 9, 3), date(2026, 9, 16))

    with pytest.raises(ValueError, match="Thursday"):
        validate_weekly_reporting_range(date(2026, 9, 11), date(2026, 9, 16))
    with pytest.raises(ValueError, match="Wednesday"):
        validate_weekly_reporting_range(date(2026, 9, 10), date(2026, 9, 15))
    with pytest.raises(ValueError, match="before"):
        validate_weekly_reporting_range(date(2026, 9, 17), date(2026, 9, 16))


def _snapshot_rows():
    return [
        _row(
            "2026-09-14",
            "32.73",
            [
                {"action_type": "lead", "value": "1"},
                {"action_type": "onsite_conversion.lead_grouped", "value": "1"},
            ],
        )
    ]


def _build_snapshot():
    return build_source_snapshot(
        ad_account_id="act_318717175",
        account_timezone="America/Los_Angeles",
        since=date(2026, 9, 10),
        until=date(2026, 9, 16),
        api_version="v25.0",
        lead_action_types=LEAD_ACTION_TYPES,
        daily_rows=_snapshot_rows(),
        captured_at_utc=datetime(2026, 9, 16, 9, 17, tzinfo=timezone.utc),
    )


def test_source_snapshot_round_trip_and_checksum(tmp_path):
    snapshot = _build_snapshot()
    path = tmp_path / "meta-source.json"

    write_source_snapshot(path, snapshot)
    loaded = load_source_snapshot(
        path,
        expected_account_id="act_318717175",
        expected_since=date(2026, 9, 10),
        expected_until=date(2026, 9, 16),
        expected_account_timezone="America/Los_Angeles",
    )

    assert loaded == snapshot
    assert loaded["daily_rows"] == _snapshot_rows()
    assert loaded["captured_at_utc"] == "2026-09-16T09:17:00Z"
    assert loaded[SNAPSHOT_CHECKSUM_FIELD] == snapshot_checksum(loaded)
    assert "access_token" not in path.read_text(encoding="utf-8")


def test_source_snapshot_checksum_detects_changed_raw_data(tmp_path):
    path = tmp_path / "meta-source.json"
    write_source_snapshot(path, _build_snapshot())
    tampered = json.loads(path.read_text(encoding="utf-8"))
    tampered["daily_rows"][0]["spend"] = "999.00"
    path.write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch"):
        load_source_snapshot(
            path,
            expected_account_id="act_318717175",
            expected_since=date(2026, 9, 10),
            expected_until=date(2026, 9, 16),
        )


@pytest.mark.parametrize(
    ("account_id", "since", "until", "message"),
    [
        ("act_wrong", date(2026, 9, 10), date(2026, 9, 16), "account mismatch"),
        ("act_318717175", date(2026, 9, 3), date(2026, 9, 16), "range mismatch"),
        ("act_318717175", date(2026, 9, 10), date(2026, 9, 23), "range mismatch"),
    ],
)
def test_source_snapshot_must_match_requested_account_and_range(
    tmp_path, account_id, since, until, message
):
    path = tmp_path / "meta-source.json"
    write_source_snapshot(path, _build_snapshot())

    with pytest.raises(ValueError, match=message):
        load_source_snapshot(
            path,
            expected_account_id=account_id,
            expected_since=since,
            expected_until=until,
        )


def test_source_snapshot_must_match_lead_action_configuration(tmp_path):
    path = tmp_path / "meta-source.json"
    write_source_snapshot(path, _build_snapshot())

    with pytest.raises(ValueError, match="lead-action configuration mismatch"):
        load_source_snapshot(
            path,
            expected_account_id="act_318717175",
            expected_since=date(2026, 9, 10),
            expected_until=date(2026, 9, 16),
            expected_lead_action_types=["lead"],
        )


def test_source_snapshot_rejects_rows_outside_declared_range():
    rows = [_row("2026-09-17", 10, [])]

    with pytest.raises(ValueError, match="outside the declared range"):
        build_source_snapshot(
            ad_account_id="act_318717175",
            account_timezone="America/Los_Angeles",
            since=date(2026, 9, 10),
            until=date(2026, 9, 16),
            api_version="v25.0",
            lead_action_types=LEAD_ACTION_TYPES,
            daily_rows=rows,
        )


def test_snapshot_replay_writes_captured_rows_without_refetching_meta(
    tmp_path, monkeypatch
):
    path = tmp_path / "meta-source.json"
    write_source_snapshot(path, _build_snapshot())
    writes = []

    class FakeGristClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def fetch_records(self, table_id, flat=True):
            assert flat is True
            if table_id == "Weekly_runs":
                return []
            if table_id == "Ads":
                return [{"id": 77, "Name": "Mens Ad J"}]
            raise AssertionError(f"Unexpected table: {table_id}")

        def add_records(self, table_id, records):
            writes.append((table_id, records))

        def patch_records(self, table_id, records):
            writes.append((table_id, records))

    class MetaMustNotBeCreated:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("Snapshot replay attempted to contact Meta")

    monkeypatch.setattr(
        sync_module,
        "load_config",
        lambda _path: {
            "ad_tracking": {
                "doc_id": "test",
                "api_key": "test",
                "server": "https://team.getgrist.com",
            },
            "meta": {"ad_account_id": "act_318717175", "api_version": "v25.0"},
        },
    )
    monkeypatch.setattr(sync_module, "GristClient", FakeGristClient)
    monkeypatch.setattr(sync_module, "MetaInsightsClient", MetaMustNotBeCreated)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sync_weekly_runs.py",
            "--since",
            "2026-09-10",
            "--until",
            "2026-09-16",
            "--snapshot-in",
            str(path),
        ],
    )

    sync_module.main()

    assert writes == [
        (
            "Weekly_runs",
            [
                {
                    "fields": {
                        "Week": 1789516800,
                        "Ad": 77,
                        "Spend": 32.73,
                        "Leads": 1,
                    }
                }
            ],
        )
    ]


def test_missing_grist_server_fails_before_client_construction(monkeypatch):
    client_was_constructed = False

    class GristMustNotBeCreated:
        def __init__(self, *_args, **_kwargs):
            nonlocal client_was_constructed
            client_was_constructed = True

    monkeypatch.setattr(
        sync_module,
        "load_config",
        lambda _path: {
            "ad_tracking": {"doc_id": "test", "api_key": "test"},
            "meta": {"ad_account_id": "act_318717175"},
        },
    )
    monkeypatch.setattr(sync_module, "GristClient", GristMustNotBeCreated)
    monkeypatch.setattr(sys, "argv", ["sync_weekly_runs.py", "--dry-run"])

    with pytest.raises(SystemExit, match="'server' missing"):
        sync_module.main()

    assert client_was_constructed is False
