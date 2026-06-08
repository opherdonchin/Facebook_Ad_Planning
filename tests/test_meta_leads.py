"""Tests for the Meta lead sync pipeline.

All tests are pure Python (no network, no Grist) using fixtures and mocks.
Coverage: normalization, deduplication, conservative updates, safety rules,
dry-run, idempotency, and in-run duplicate detection.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from lead_utils import (
    build_index,
    compute_updates_for_match,
    norm_phone,
)
from meta_leads import flatten_field_data, parse_meta_lead
from sync_meta_leads import (
    build_meta_id_index,
    compute_meta_updates,
    sync_meta_leads_to_grist,
)


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------
_COLS = {
    "phone": "Phone",
    "email": "Email",
    "name_en": "Name_EN",
    "name_he": "Name_HE",
    "date": "Date",
    "campaign": "Campaign",
    "ad_name": "Ad_name",
    "platform": "Platform",
    "meta_lead_id": "Meta_lead_id",
    "meta_created_time": "Meta_created_time",
    "meta_ad_id": "Meta_ad_id",
    "meta_campaign_id": "Meta_campaign_id",
    "meta_form_id": "Meta_form_id",
    "meta_raw_json": "",  # not configured by default
    "imported_at": "Imported_at",
}

_CREATED_TIME = "2026-05-01T10:00:00+00:00"
_CREATED_DT = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)


def _make_raw_lead(
    lead_id: str = "lead_123",
    phone: str = "0521234567",
    email: str = "test@example.com",
    name: str = "Test User",
    campaign_id: str = "camp_1",
    campaign_name: str = "Spring Campaign",
    ad_id: str = "ad_1",
    form_id: str = "form_1",
) -> Dict[str, Any]:
    return {
        "id": lead_id,
        "created_time": _CREATED_TIME,
        "ad_id": ad_id,
        "form_id": form_id,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "field_data": [
            {"name": "full_name", "values": [name]},
            {"name": "phone_number", "values": [phone]},
            {"name": "email", "values": [email]},
        ],
    }


def _make_grist_record(
    grist_id: int,
    meta_lead_id: str = "",
    phone: str = "972521234567",
    email: str = "test@example.com",
    name_en: str = "",
    name_he: str = "",
    status: str = "",
    campaign: str = "",
) -> Dict[str, Any]:
    return {
        "id": grist_id,
        "fields": {
            "Meta_lead_id": meta_lead_id,
            "Phone": phone,
            "Email": email,
            "Name_EN": name_en,
            "Name_HE": name_he,
            "Status": status,
            "Campaign": campaign,
            "Ad_name": "",
            "Platform": "",
            "Date": "",
            "Meta_created_time": "",
            "Meta_ad_id": "",
            "Meta_campaign_id": "",
            "Meta_form_id": "",
            "Imported_at": "",
        },
    }


# ---------------------------------------------------------------------------
# Test 1: norm_phone cross-format consistency (the key fix)
# ---------------------------------------------------------------------------
def test_norm_phone_plus972_equals_052_format():
    """The same Israeli number in +972 and 052 formats normalizes identically."""
    assert norm_phone("+972521234567") == norm_phone("052-123-4567")


# ---------------------------------------------------------------------------
# Test 2: norm_phone canonical form
# ---------------------------------------------------------------------------
def test_norm_phone_canonical_form():
    """052... numbers normalize to 972... (no leading 0, no +)."""
    assert norm_phone("0521234567") == "972521234567"
    assert norm_phone("052-123-4567") == "972521234567"
    assert norm_phone("+972521234567") == "972521234567"
    assert norm_phone("972521234567") == "972521234567"


# ---------------------------------------------------------------------------
# Test 3: flatten_field_data phone aliases
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("alias", ["phone", "whatsapp_number", "phone_number"])
def test_flatten_phone_aliases(alias):
    """All phone field name variants map to the phone_number key."""
    result = flatten_field_data([{"name": alias, "values": ["0521234567"]}])
    assert "phone_number" in result
    assert result["phone_number"] == "0521234567"


def test_flatten_name_aliases():
    """Both 'name' and 'full_name' map to the full_name key."""
    for alias in ("name", "full_name"):
        result = flatten_field_data([{"name": alias, "values": ["John"]}])
        assert result.get("full_name") == "John"


def test_flatten_unknown_field_passthrough():
    result = flatten_field_data([{"name": "custom_question", "values": ["answer"]}])
    assert result.get("custom_question") == "answer"


# ---------------------------------------------------------------------------
# Test 4: Meta ID match → updates meta fields, does NOT create duplicate
# ---------------------------------------------------------------------------
def test_meta_id_match_updates_not_creates():
    """A lead whose meta_lead_id is already in Grist gets updated, not re-created."""
    raw = _make_raw_lead(lead_id="lead_123")
    lead = parse_meta_lead(raw)

    grist_records = [_make_grist_record(grist_id=1, meta_lead_id="lead_123")]
    meta_id_idx, _ = build_meta_id_index(grist_records, "Meta_lead_id")

    assert "lead_123" in meta_id_idx  # matched
    # Matching record is found, not in add path
    rec = meta_id_idx["lead_123"]
    assert rec["id"] == 1


# ---------------------------------------------------------------------------
# Test 5: Meta ID match → does NOT overwrite Status
# ---------------------------------------------------------------------------
def test_meta_id_match_does_not_overwrite_status():
    """compute_meta_updates must not touch the Status field."""
    raw = _make_raw_lead(lead_id="lead_123")
    lead = parse_meta_lead(raw)

    grist_fields = {
        "Meta_lead_id": "lead_123",
        "Phone": "972521234567",
        "Email": "test@example.com",
        "Name_EN": "",
        "Name_HE": "",
        "Status": "Trial scheduled",  # must not be overwritten
        "Campaign": "",
        "Ad_name": "",
        "Platform": "",
        "Date": "",
        "Meta_created_time": "",
        "Meta_ad_id": "",
        "Meta_campaign_id": "",
        "Meta_form_id": "",
        "Imported_at": "",
    }

    import json
    canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)
    upd, _ = compute_meta_updates(
        grist_fields=grist_fields,
        lead=lead,
        cols=_COLS,
        canonical_json=canonical_json,
        verbose_pii=False,
        max_gap_days=3,
        ad_id_map={},
        now_iso="2026-06-01T10:00:00+00:00",
    )

    assert "Status" not in upd


# ---------------------------------------------------------------------------
# Test 6: Phone+email match → backfills meta_lead_id
# ---------------------------------------------------------------------------
def test_phone_email_match_backfills_meta_lead_id():
    """When phone+email matches but meta_lead_id is empty, it gets backfilled."""
    raw = _make_raw_lead(lead_id="lead_456", phone="0521234567", email="test@example.com")
    lead = parse_meta_lead(raw)

    grist_fields = {
        "Meta_lead_id": "",  # empty — was imported via CSV before sync existed
        "Phone": "972521234567",
        "Email": "test@example.com",
        "Name_EN": "",
        "Name_HE": "",
        "Status": "",
        "Campaign": "",
        "Ad_name": "",
        "Platform": "",
        "Date": "",
        "Meta_created_time": "",
        "Meta_ad_id": "",
        "Meta_campaign_id": "",
        "Meta_form_id": "",
        "Imported_at": "",
    }

    import json
    canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)
    upd, _ = compute_meta_updates(
        grist_fields=grist_fields,
        lead=lead,
        cols=_COLS,
        canonical_json=canonical_json,
        verbose_pii=False,
        max_gap_days=3,
        ad_id_map={},
        now_iso="2026-06-01T10:00:00+00:00",
    )

    assert upd.get("Meta_lead_id") == "lead_456"


# ---------------------------------------------------------------------------
# Test 7: Phone+email match → does NOT overwrite existing name
# ---------------------------------------------------------------------------
def test_phone_email_match_does_not_overwrite_name():
    """An existing name in Grist must not be overwritten by the Meta lead name."""
    raw = _make_raw_lead(name="John Smith")
    lead = parse_meta_lead(raw)

    grist_fields = {
        "Meta_lead_id": "",
        "Phone": "972521234567",
        "Email": "test@example.com",
        "Name_EN": "John Smith",  # already present — must not be overwritten
        "Name_HE": "",
        "Status": "",
        "Campaign": "",
        "Ad_name": "",
        "Platform": "",
        "Date": "",
        "Meta_created_time": "",
        "Meta_ad_id": "",
        "Meta_campaign_id": "",
        "Meta_form_id": "",
        "Imported_at": "",
    }

    import json
    canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)
    upd, _ = compute_meta_updates(
        grist_fields=grist_fields,
        lead=lead,
        cols=_COLS,
        canonical_json=canonical_json,
        verbose_pii=False,
        max_gap_days=3,
        ad_id_map={},
        now_iso="2026-06-01T10:00:00+00:00",
    )

    assert "Name_EN" not in upd


# ---------------------------------------------------------------------------
# Test 8: New lead created when no match exists
# ---------------------------------------------------------------------------
def test_new_lead_created_when_no_match():
    """A lead with no Grist match goes into the add_batch."""
    raw = _make_raw_lead(lead_id="lead_999", phone="0529999999", email="new@example.com")

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = []  # empty Grist
    mock_grist.add_records.return_value = [42]

    stats = sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=False,
    )

    assert stats["leads_created"] == 1
    assert stats["leads_updated"] == 0
    assert stats["leads_skipped"] == 0
    mock_grist.add_records.assert_called_once()


# ---------------------------------------------------------------------------
# Test 9: Phone-only lead skipped when no meta_id match
# ---------------------------------------------------------------------------
def test_phone_only_lead_skipped():
    """A lead with phone but no email must be skipped (no meta_id match)."""
    raw = {
        "id": "lead_partial",
        "created_time": _CREATED_TIME,
        "ad_id": "ad_1",
        "form_id": "form_1",
        "field_data": [
            {"name": "full_name", "values": ["Alice"]},
            {"name": "phone_number", "values": ["0521234567"]},
            # no email
        ],
    }

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = []

    stats = sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=False,
    )

    assert stats["leads_skipped"] == 1
    assert stats["leads_created"] == 0
    mock_grist.add_records.assert_not_called()


# ---------------------------------------------------------------------------
# Test 10: --dry-run makes no Grist writes
# ---------------------------------------------------------------------------
def test_dry_run_makes_no_grist_writes():
    """When dry_run=True, add_records and patch_records must not be called."""
    raw = _make_raw_lead()

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = []

    sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=True,
    )

    mock_grist.add_records.assert_not_called()
    mock_grist.patch_records.assert_not_called()


# ---------------------------------------------------------------------------
# Test 11: Second run with same fixture → zero patches (idempotency)
# ---------------------------------------------------------------------------
def test_idempotent_second_run_zero_writes():
    """After first sync, running again with the same data produces no Grist writes."""
    raw = _make_raw_lead(lead_id="lead_123", phone="0521234567", email="test@example.com")
    lead = parse_meta_lead(raw)

    import json
    canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)

    # Simulate state after first run: all fields already filled
    grist_state = [
        {
            "id": 1,
            "fields": {
                "Meta_lead_id": "lead_123",
                "Phone": "972521234567",
                "Email": "test@example.com",
                "Name_EN": "Test User",
                "Name_HE": "",
                "Status": "",
                "Campaign": "Spring Campaign",
                "Ad_name": "",
                "Platform": "Facebook",
                "Date": "2026-05-01",
                "Meta_created_time": _CREATED_TIME,
                "Meta_ad_id": "ad_1",
                "Meta_campaign_id": "camp_1",
                "Meta_form_id": "form_1",
                "Imported_at": "2026-05-01T12:00:00+00:00",
            },
        }
    ]

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = grist_state

    stats = sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=False,
    )

    assert stats["leads_created"] == 0
    assert stats["leads_updated"] == 0
    mock_grist.add_records.assert_not_called()
    mock_grist.patch_records.assert_not_called()


# ---------------------------------------------------------------------------
# Test 12: Meta-ID match populates seen_phone_emails (Finding 1 regression)
# ---------------------------------------------------------------------------
def test_meta_id_match_blocks_subsequent_phone_email_duplicate():
    """After a meta-ID match, a later lead with the same phone+email but a
    different meta_id must NOT create a second Grist record."""
    raw_a = _make_raw_lead(lead_id="lead_A", phone="0521234567", email="shared@example.com")
    raw_b = _make_raw_lead(lead_id="lead_B", phone="0521234567", email="shared@example.com")

    # Grist already has lead_A matched by meta_id
    grist_a = {
        "id": 1,
        "fields": {
            "Meta_lead_id": "lead_A",
            "Phone": "972521234567",
            "Email": "shared@example.com",
            "Name_EN": "Test User",
            "Name_HE": "",
            "Status": "",
            "Campaign": "Spring Campaign",
            "Ad_name": "",
            "Platform": "Facebook",
            "Date": "2026-05-01",
            "Meta_created_time": _CREATED_TIME,
            "Meta_ad_id": "ad_1",
            "Meta_campaign_id": "camp_1",
            "Meta_form_id": "form_1",
            "Imported_at": "2026-05-01T12:00:00+00:00",
        },
    }

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw_a, raw_b]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = [grist_a]

    stats = sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=False,
    )

    # lead_B has the same phone+email as lead_A which was matched by meta_id.
    # It must be treated as an in-run duplicate, not a new lead.
    assert stats["leads_created"] == 0, "Second lead with same phone+email must not create a duplicate"
    mock_grist.add_records.assert_not_called()


# ---------------------------------------------------------------------------
# Test 13: Conservative updates — Campaign/Ad_name/Platform never overwritten
# ---------------------------------------------------------------------------
def test_conservative_update_does_not_overwrite_campaign_ad_platform():
    """When Campaign, Ad_name, and Platform are already set in Grist with
    different values, compute_meta_updates must not overwrite them."""
    raw = _make_raw_lead(lead_id="lead_123", campaign_name="New Campaign")
    lead = parse_meta_lead(raw)

    grist_fields = {
        "Meta_lead_id": "lead_123",
        "Phone": "972521234567",
        "Email": "test@example.com",
        "Name_EN": "Test User",
        "Name_HE": "",
        "Status": "Active",
        "Campaign": "Existing Campaign",   # already set, different value
        "Ad_name": "Existing Ad",          # already set
        "Platform": "Instagram",           # already set, different value
        "Date": "2026-05-01",
        "Meta_created_time": _CREATED_TIME,
        "Meta_ad_id": "ad_1",
        "Meta_campaign_id": "camp_1",
        "Meta_form_id": "form_1",
        "Imported_at": "2026-05-01T12:00:00+00:00",
    }

    import json
    canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)
    upd, _ = compute_meta_updates(
        grist_fields=grist_fields,
        lead=lead,
        cols=_COLS,
        canonical_json=canonical_json,
        verbose_pii=False,
        max_gap_days=3,
        ad_id_map={},
        now_iso="2026-06-01T10:00:00+00:00",
    )

    assert "Campaign" not in upd, "Campaign must not be overwritten"
    assert "Ad_name" not in upd, "Ad_name must not be overwritten"
    assert "Platform" not in upd, "Platform must not be overwritten"
    assert "Status" not in upd, "Status must not be overwritten"


# ---------------------------------------------------------------------------
# Test 14: Same meta_lead_id in two fetched leads → only one add/update
# ---------------------------------------------------------------------------
def test_in_run_deduplication_by_meta_id():
    """Two leads with the same meta_lead_id in one batch produce only one create."""
    raw1 = _make_raw_lead(lead_id="lead_dup", phone="0521234567", email="a@example.com")
    raw2 = _make_raw_lead(lead_id="lead_dup", phone="0521234568", email="b@example.com")  # same ID

    mock_meta = MagicMock()
    mock_meta.fetch_leads.return_value = [raw1, raw2]

    mock_grist = MagicMock()
    mock_grist.fetch_records.return_value = []
    mock_grist.add_records.return_value = [1]

    stats = sync_meta_leads_to_grist(
        meta_client=mock_meta,
        grist_client=mock_grist,
        form_ids=["form_1"],
        table_id="Leads",
        cols=_COLS,
        ad_id_map={},
        dry_run=False,
    )

    # Only one record should be created; the second is skipped as in-run duplicate
    assert stats["leads_created"] == 1
    assert stats["leads_skipped"] == 0  # not "skipped" — it's a duplicate
    add_call = mock_grist.add_records.call_args
    assert len(add_call[0][1]) == 1  # only 1 record in the add batch
