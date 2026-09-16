"""Safety-gate tests for weekly packaging and offline refreshes."""

import pytest

from package_weekly_uploads import read_source_validation_status
from refresh_export_from_meta_snapshot import require_passed_snapshot


def test_source_validation_status_must_be_explicit(tmp_path):
    note = tmp_path / "weekly_source_validation.md"
    assert read_source_validation_status(note) is None

    note.write_text("**Status: FAILED — investigate**\n", encoding="utf-8")
    assert read_source_validation_status(note) == "FAILED"

    note.write_text("**Status: PASSED**\n", encoding="utf-8")
    assert read_source_validation_status(note) == "PASSED"


@pytest.mark.parametrize("status", [None, "", "pending", "failed"])
def test_offline_refresh_rejects_unvalidated_snapshot(status):
    snapshot = {} if status is None else {"validation_status": status}
    with pytest.raises(ValueError, match="validation_status must be 'passed'"):
        require_passed_snapshot(snapshot)


def test_offline_refresh_accepts_passed_snapshot():
    require_passed_snapshot({"validation_status": "passed"})
