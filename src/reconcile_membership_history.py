"""Reconcile person-level Students with the Leads membership event ledger.

This is a one-off, idempotent repair for the decisions made on 2026-09-16.
It defaults to a read-only plan. Pass ``--apply`` to write the reviewed changes.

The two Grist documents cannot contain cross-document Ref columns, so this repair
uses integer ``Leads.Student_ID`` and ``Students.Lead_ID`` columns.  A student's
first membership start is ``Registration``; a later start after cancellation is
``Return``.  That keeps paid-acquisition conversion counts tied to first-time
registrations while still allowing membership-flow reporting to count returns.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from grist.grist import GristClient
from utils import load_config


# Reviewed, high-confidence identity links.  Keys are Student row IDs and values
# are Lead row IDs.  This includes the user's approved transliteration matches.
EXISTING_STUDENT_TO_LEAD: Dict[int, int] = {
    4: 23,  # Hanwen Liu
    16: 28,  # Zhuoxin Liu
    41: 36,  # Benjamin Deutsch
    57: 15,  # Evgeni Zaidman
    70: 41,  # Levy Shenkar
    71: 42,  # Meir Kashani
    74: 22,  # Moti Leizerovitch
    86: 160,  # Slava Chadin
    101: 31,  # Renata Kovalchuk
    108: 46,  # Oleg Dolgapolshki
    109: 61,  # Dor Zourno
    110: 63,  # Dvora Milchiker
    111: 94,  # Eran Gavrieli
    112: 99,  # Sophie Fogel
    113: 103,  # Ariel Tsesarsky
    114: 64,  # Shlomit Tzadik
    115: 106,  # Shifra Parnas
    116: 82,  # Ori Rubin
    117: 130,  # Yehonatan Simhon
    118: 145,  # Naor Nismayam
    119: 142,  # Daniel Kraus
    120: 171,  # Ronen Sarusi
    121: 156,  # Meydan Kaplan
    122: 187,  # Reuven Mordechai
    123: 194,  # Mark Idelman
    124: 228,  # Robert Bocking
    125: 203,  # Ilana Bloch
    126: 244,  # Bakar Algoayn
    127: 284,  # Aviv Berkovski
    129: 362,  # Yael Belassen
    130: 355,  # Roah Farhat
    131: 351,  # Agan Farhat
    132: 344,  # Ariel Natan
    133: 348,  # Nir Doron
}

ACTIVE_LEGACY_NEW_LEADS = (26, 32, 45, 56, 89, 105)
TOMER_STUDENT_ID = 107

PAUSE_LEAD_IDS = (
    4,
    13,
    25,
    27,
    30,
    33,
    36,
    38,
    47,
    48,
    52,
    53,
    56,
    95,
    116,
    119,
    126,
    158,
    176,
)


def epoch(day: str) -> int:
    return int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return datetime.fromtimestamp(int(value), timezone.utc).date().isoformat()


def list_refs(value: Any) -> Iterable[int]:
    if not isinstance(value, list):
        return ()
    if value and value[0] == "L":
        return (x for x in value[1:] if isinstance(x, int))
    return (x for x in value if isinstance(x, int))


def first_last_attendance(
    students: Mapping[int, Mapping[str, Any]], sessions: Sequence[Mapping[str, Any]]
) -> Dict[int, Tuple[int, int]]:
    dates: MutableMapping[int, List[int]] = defaultdict(list)
    for session in sessions:
        session_date = session.get("Date")
        if not session_date:
            continue
        for student_id in list_refs(session.get("Students_Present")):
            if student_id in students:
                dates[student_id].append(int(session_date))
    out: Dict[int, Tuple[int, int]] = {}
    for student_id, values in dates.items():
        out[student_id] = (min(values), max(values))
    return out


def ensure_column(
    client: GristClient,
    table_id: str,
    column_id: str,
    fields: Mapping[str, Any],
    apply: bool,
) -> None:
    existing = {c["id"] for c in client.get_table_columns(table_id)}
    if column_id in existing:
        return
    print(f"[PLAN] Add {table_id}.{column_id} ({fields.get('type')})")
    if apply:
        client.create_columns(
            table_id, [{"id": column_id, "fields": dict(fields)}]
        )


def ensure_return_choice(client: GristClient, apply: bool) -> None:
    event_col = next(c for c in client.get_table_columns("Sales_events") if c["id"] == "Event")
    options = json.loads(event_col.get("fields", {}).get("widgetOptions") or "{}")
    choices = list(options.get("choices") or [])
    if "Return" in choices:
        return
    choices.append("Return")
    options["choices"] = choices
    choice_options = dict(options.get("choiceOptions") or {})
    choice_options["Return"] = {"fillColor": "#75B5FC", "textColor": "#000000"}
    options["choiceOptions"] = choice_options
    print("[PLAN] Add Return to Sales_events.Event choices")
    if apply:
        client.update_columns(
            "Sales_events",
            [{"id": "Event", "fields": {"widgetOptions": json.dumps(options)}}],
        )


def make_lead_fields(student: Mapping[str, Any], first: int) -> Dict[str, Any]:
    return {
        "Name": (student.get("Name") or "").strip(),
        "Date": first,
        "Phone": student.get("Phone_number") or "",
        "Email": (student.get("Email") or "").strip(),
        "Status": "Registered",
        "Sex": student.get("Sex") or "",
        "Student_ID": student["id"],
    }


def add_missing_leads(
    leads_client: GristClient,
    students: Mapping[int, Mapping[str, Any]],
    attendance: Mapping[int, Tuple[int, int]],
    student_to_lead: MutableMapping[int, int],
    target_ids: Sequence[int],
    apply: bool,
) -> None:
    missing = [sid for sid in target_ids if sid not in student_to_lead]
    if not missing:
        return
    for sid in missing:
        if sid not in attendance:
            raise RuntimeError(f"Student {sid} has no attendance; refusing to invent a Lead date")
    print(f"[PLAN] Create {len(missing)} Lead rows for Student IDs {missing}")
    if not apply:
        # Negative placeholders make the remainder of the dry-run plan readable.
        for n, sid in enumerate(missing, 1):
            student_to_lead[sid] = -n
        return
    records = [
        {"fields": make_lead_fields(students[sid], attendance[sid][0])}
        for sid in missing
    ]
    new_ids = leads_client.add_records("Leads", records)
    if len(new_ids) != len(missing):
        raise RuntimeError("Grist did not return one Lead ID for every new row")
    student_to_lead.update(dict(zip(missing, new_ids)))


def event_key(lead_id: int, event: str, event_date: int) -> Tuple[int, str, int]:
    return lead_id, event, event_date


def coalesce_updates(records: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Merge multiple field patches for the same record into one API row."""
    merged: Dict[int, Dict[str, Any]] = {}
    for record in records:
        record_id = int(record["id"])
        merged.setdefault(record_id, {}).update(record.get("fields", {}))
    return [
        {"id": record_id, "fields": fields}
        for record_id, fields in sorted(merged.items())
    ]


def patch_grouped(
    client: GristClient, table_id: str, records: Sequence[Mapping[str, Any]]
) -> None:
    """Patch records in groups with identical field sets, as Grist requires."""
    groups: MutableMapping[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        fields = dict(record.get("fields", {}))
        groups[tuple(sorted(fields))].append(
            {"id": int(record["id"]), "fields": fields}
        )
    for field_names, group in sorted(groups.items()):
        print(
            f"[PATCH] {table_id}: {len(group)} rows with fields "
            f"{list(field_names)}"
        )
        client.patch_records(table_id, group)


def ensure_formula_column(
    client: GristClient,
    table_id: str,
    column_id: str,
    formula: str,
    apply: bool,
    column_type: str = "Int",
) -> None:
    columns = {c["id"]: c for c in client.get_table_columns(table_id)}
    if column_id not in columns:
        print(f"[PLAN] Add formula column {table_id}.{column_id}")
        if apply:
            client.create_columns(
                table_id,
                [
                    {
                        "id": column_id,
                        "fields": {
                            "label": column_id.replace("_", " "),
                            "type": column_type,
                            "isFormula": True,
                            "formula": formula,
                        },
                    }
                ],
            )
        return
    fields = columns[column_id].get("fields", {})
    if fields.get("formula") == formula and fields.get("isFormula"):
        return
    print(f"[PLAN] Update formula {table_id}.{column_id}")
    if apply:
        client.update_columns(
            table_id,
            [
                {
                    "id": column_id,
                    "fields": {"isFormula": True, "formula": formula},
                }
            ],
        )


def rebuild_sales_summaries(client: GristClient, apply: bool) -> None:
    """Make weekly/monthly membership flows replay directly from Sales_events."""
    ensure_formula_column(
        client,
        "Sales_events_summary_Week",
        "Return",
        "sum(r.Event == 'Return' for r in $group)",
        apply,
    )

    weekly_columns = {c["id"] for c in client.get_table_columns("Weekly_Summary")}
    if "Returned" not in weekly_columns:
        print("[PLAN] Add Weekly_Summary.Returned")
        if apply:
            client.create_columns(
                "Weekly_Summary",
                [{"id": "Returned", "fields": {"label": "Returned", "type": "Int"}}],
            )
    ensure_formula_column(
        client,
        "Weekly_Summary",
        "Active_Starts",
        "$Registered + $Returned",
        apply,
    )
    ensure_formula_column(
        client,
        "Weekly_Summary",
        "Growth2",
        "$Registered + $Returned - $Cancelled",
        apply,
    )
    ensure_formula_column(
        client,
        "Weekly_Summary",
        "Month",
        "import datetime\n"
        "d = datetime.date.fromisocalendar(int($Week[:4]), int($Week[6:]), 1) "
        "+ datetime.timedelta(days=3)\n"
        "d.strftime('%Y-%m')",
        apply,
        column_type="Text",
    )

    ensure_formula_column(
        client,
        "Weekly_Summary_summary_Month",
        "Returned",
        "SUM($group.Returned)",
        apply,
        column_type="Numeric",
    )
    ensure_formula_column(
        client,
        "Weekly_Summary_summary_Month",
        "Active_Starts",
        "$Registered + $Returned",
        apply,
        column_type="Numeric",
    )
    ensure_formula_column(
        client,
        "Weekly_Summary_summary_Month",
        "Growth",
        "$Registered + $Returned - $Cancelled",
        apply,
        column_type="Numeric",
    )

    # Summary-source groups cannot be filtered, so make every metric ignore the
    # Special-event placeholders explicitly.
    for column_id, formula in {
        "count": "sum(r.Status != 'Special event' for r in $group)",
        "Has_trial": "sum(r.Has_trial for r in $group if r.Status != 'Special event')",
        "Has_registration": "sum(r.Has_registration for r in $group if r.Status != 'Special event')",
        "Is_failed": "sum(r.Is_failed for r in $group if r.Status != 'Special event')",
    }.items():
        ensure_formula_column(
            client,
            "Leads_summary_Ad_name",
            column_id,
            formula,
            apply,
            column_type="Int",
        )

    if not apply:
        return

    # Re-fetch after adding the Return formula so its calculated values are
    # available, then replace every manual event total in Weekly_Summary.
    by_week = {
        row.get("Week"): row
        for row in client.fetch_records("Sales_events_summary_Week", flat=True)
        if row.get("Week")
    }
    weekly = client.fetch_records("Weekly_Summary", flat=True)
    existing_weeks = {row.get("Week") for row in weekly}
    current_date = datetime.now(timezone.utc).date()
    current_iso_year, current_iso_week, _ = current_date.isocalendar()
    current_week = f"{current_iso_year}-W{current_iso_week:02d}"
    missing_weeks = sorted(
        week
        for week in by_week
        if "2025-W21" <= week <= current_week and week not in existing_weeks
    )
    if missing_weeks:
        additions: List[Dict[str, Any]] = []
        for week in missing_weeks:
            source = by_week[week]
            additions.append(
                {
                    "fields": {
                        "Week": week,
                        "Total_spent": 0,
                        "Num_leads": 0,
                        "Interest": int(source.get("Interest") or 0),
                        "Appointment": int(source.get("Appointment") or 0),
                        "Lesson": int(source.get("Introductory_lesson") or 0),
                        "Registered": int(source.get("Registration") or 0),
                        "Notified": int(source.get("Notification") or 0),
                        "Cancelled": int(source.get("Cancellation") or 0),
                        "Returned": int(source.get("Return") or 0),
                    }
                }
            )
        print(f"[PLAN] Add missing event weeks to Weekly_Summary: {missing_weeks}")
        client.add_records("Weekly_Summary", additions)
        weekly = client.fetch_records("Weekly_Summary", flat=True)

    updates: List[Dict[str, Any]] = []
    for row in weekly:
        source = by_week.get(row.get("Week"), {})
        updates.append(
            {
                "id": row["id"],
                "fields": {
                    "Interest": int(source.get("Interest") or 0),
                    "Appointment": int(source.get("Appointment") or 0),
                    "Lesson": int(source.get("Introductory_lesson") or 0),
                    "Registered": int(source.get("Registration") or 0),
                    "Notified": int(source.get("Notification") or 0),
                    "Cancelled": int(source.get("Cancellation") or 0),
                    "Returned": int(source.get("Return") or 0),
                },
            }
        )
    print(f"[PLAN] Rebuild {len(updates)} Weekly_Summary event rows from Sales_events")
    patch_grouped(client, "Weekly_Summary", updates)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument(
        "--students-doc-id",
        help="Override leads.students_doc_id from config.json.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)["leads"]
    students_doc_id = args.students_doc_id or cfg.get("students_doc_id")
    if not students_doc_id:
        raise SystemExit(
            "[CONFIG ERROR] Set leads.students_doc_id in config.json or pass "
            "--students-doc-id."
        )
    leads_client = GristClient(cfg["doc_id"], cfg["api_key"], cfg["server"])
    students_client = GristClient(
        students_doc_id, cfg["api_key"], cfg["server"]
    )

    apply = args.apply
    print("[MODE] APPLY" if apply else "[MODE] DRY RUN")

    leads = {r["id"]: r for r in leads_client.fetch_records("Leads", flat=True)}
    events = {r["id"]: r for r in leads_client.fetch_records("Sales_events", flat=True)}
    students = {r["id"]: r for r in students_client.fetch_records("Students", flat=True)}
    sessions = students_client.fetch_records("Sessions", flat=True)
    attendance = first_last_attendance(students, sessions)

    print(
        f"[BEFORE] Leads={len(leads)} Events={len(events)} Students={len(students)} "
        f"Cancelled={sum(s.get('Status') == 'Cancelled' for s in students.values())}"
    )

    ensure_column(
        leads_client,
        "Leads",
        "Student_ID",
        {"label": "Student ID", "type": "Int"},
        apply,
    )
    ensure_column(
        students_client,
        "Students",
        "Lead_ID",
        {"label": "Lead ID", "type": "Int"},
        apply,
    )
    ensure_column(
        students_client,
        "Students",
        "Cancellation_Date",
        {
            "label": "Cancellation Date",
            "type": "Date",
            "widgetOptions": json.dumps(
                {
                    "dateFormat": "YYYY-MM-DD",
                    "timeFormat": "",
                    "isCustomDateFormat": False,
                    "isCustomTimeFormat": True,
                }
            ),
        },
        apply,
    )
    ensure_return_choice(leads_client, apply)

    # Add Ying Lin to Students with only what is supportable.  Her 2025-06-19
    # cancellation is known; retained data contains no join/attendance date.
    ying_candidates = [
        sid
        for sid, student in students.items()
        if student.get("Lead_ID") == 24
        or (student.get("Name") or "").strip().casefold() == "ying lin"
    ]
    if ying_candidates:
        ying_student_id = ying_candidates[0]
    else:
        print("[PLAN] Create cancelled Student for Ying Lin; Join_Date remains unknown")
        if apply:
            created = students_client.add_records(
                "Students",
                [
                    {
                        "fields": {
                            "Name": "Ying Lin",
                            "Status": "Cancelled",
                            "Join_Date": None,
                            "Lead_ID": 24,
                            "Cancellation_Date": epoch("2025-06-19"),
                        }
                    }
                ],
            )
            if len(created) != 1:
                raise RuntimeError("Could not create the Ying Lin Student row")
            ying_student_id = created[0]
            students[ying_student_id] = {
                "id": ying_student_id,
                "Name": "Ying Lin",
                "Status": "Cancelled",
                "Lead_ID": 24,
                "Cancellation_Date": epoch("2025-06-19"),
                "Join_Date": None,
            }
        else:
            ying_student_id = -999

    student_to_lead: Dict[int, int] = dict(EXISTING_STUDENT_TO_LEAD)
    student_to_lead[ying_student_id] = 24
    # Reuse links from a prior successful or partially successful run.
    for sid, student in students.items():
        linked_lead = student.get("Lead_ID")
        if isinstance(linked_lead, int) and linked_lead > 0:
            student_to_lead.setdefault(sid, linked_lead)
    for lid, lead in leads.items():
        linked_student = lead.get("Student_ID")
        if isinstance(linked_student, int) and linked_student > 0:
            student_to_lead.setdefault(linked_student, lid)

    # All unmatched cancelled students have actual attendance.  Student 51 is
    # deliberately not merged into modern failed Lead 300 (name-only collision).
    legacy_cancelled_targets = sorted(
        sid
        for sid, student in students.items()
        if student.get("Status") == "Cancelled"
        and sid != ying_student_id
        and sid not in EXISTING_STUDENT_TO_LEAD
    )
    if len(legacy_cancelled_targets) != 88:
        raise RuntimeError(
            f"Expected 88 legacy cancelled Student targets, found "
            f"{len(legacy_cancelled_targets)}: {legacy_cancelled_targets}"
        )
    add_missing_leads(
        leads_client,
        students,
        attendance,
        student_to_lead,
        legacy_cancelled_targets,
        apply,
    )
    add_missing_leads(
        leads_client,
        students,
        attendance,
        student_to_lead,
        ACTIVE_LEGACY_NEW_LEADS,
        apply,
    )
    add_missing_leads(
        leads_client,
        students,
        attendance,
        student_to_lead,
        (TOMER_STUDENT_ID,),
        apply,
    )

    # Bidirectional integer links, plus the exact record corrections approved by
    # the user.  Current-status fields are intentionally not inferred from events.
    lead_updates: List[Dict[str, Any]] = []
    student_updates: List[Dict[str, Any]] = []
    for sid, lid in sorted(student_to_lead.items()):
        if lid < 0 or sid < 0:
            continue
        lead_updates.append({"id": lid, "fields": {"Student_ID": sid}})
        student_updates.append({"id": sid, "fields": {"Lead_ID": lid}})
    for lid in PAUSE_LEAD_IDS:
        lead_updates.append({"id": lid, "fields": {"Status": "Failed"}})
    student_updates.extend(
        [
            {"id": ying_student_id, "fields": {"Join_Date": None}},
            {"id": 118, "fields": {"Phone_number": "0542110885"}},
            {"id": 111, "fields": {"Join_Date": epoch("2025-10-21")}},
            {"id": 32, "fields": {"Join_Date": attendance[32][0]}},
            {"id": 56, "fields": {"Join_Date": attendance[56][0]}},
        ]
    )
    lead_updates = coalesce_updates(lead_updates)
    student_updates = coalesce_updates(student_updates)
    print(
        f"[PLAN] Patch {len(lead_updates)} Lead link/status values and "
        f"{len(student_updates)} Student link/data values"
    )
    if apply:
        patch_grouped(leads_client, "Leads", lead_updates)
        patch_grouped(students_client, "Students", student_updates)

    # Remove all sales events belonging to Special-event pseudo-leads, plus the
    # two adjudicated duplicate registrations.
    special_leads = {lid for lid, row in leads.items() if row.get("Status") == "Special event"}
    special_event_ids = sorted(
        eid for eid, row in events.items() if row.get("Name") in special_leads
    )
    if len(special_leads) != 17 or len(special_event_ids) not in (0, 17):
        raise RuntimeError(
            f"Expected 17 Special-event Leads and either 17 first-run or 0 "
            f"already-deleted events, found "
            f"{len(special_leads)}/{len(special_event_ids)}"
        )
    delete_event_ids = list(special_event_ids)
    for eid, expected in {
        121: (61, "Registration", "2025-09-02"),
        135: (94, "Registration", "2025-10-14"),
    }.items():
        row = events.get(eid)
        if row:
            actual = (row.get("Name"), row.get("Event"), iso(row.get("Date")))
            if actual != expected:
                raise RuntimeError(f"Event {eid} precondition failed: {actual} != {expected}")
            delete_event_ids.append(eid)
    print(f"[PLAN] Delete {len(delete_event_ids)} Sales_events: {delete_event_ids}")
    if apply and delete_event_ids:
        leads_client.delete_records("Sales_events", delete_event_ids)

    tomer_lead_id = student_to_lead[TOMER_STUDENT_ID]
    event_updates = [
        {"id": 71, "fields": {"Event": "Return"}},  # Levy
        {"id": 60, "fields": {"Event": "Return"}},  # Meir
        {"id": 242, "fields": {"Event": "Return"}},  # Slava
        {"id": 51, "fields": {"Name": tomer_lead_id, "Event": "Return"}},
        {"id": 76, "fields": {"Date": epoch("2025-08-19")}},  # Oleg
        {"id": 147, "fields": {"Date": epoch("2025-10-23")}},  # Sophie
        {"id": 292, "fields": {"Date": epoch("2026-01-29")}},  # Meydan
        {"id": 583, "fields": {"Date": epoch("2017-07-18")}},  # Slava Interest
    ]
    print(f"[PLAN] Patch {len(event_updates)} adjudicated Sales_events")
    if apply:
        patch_grouped(leads_client, "Sales_events", event_updates)

    # Build the complete set of additions and suppress exact duplicates.  After
    # an apply, patched events are folded into this index before additions.
    remaining_events = {
        eid: dict(row) for eid, row in events.items() if eid not in delete_event_ids
    }
    for update in event_updates:
        if update["id"] in remaining_events:
            remaining_events[update["id"]].update(update["fields"])
    existing_event_keys = {
        event_key(int(row["Name"]), row["Event"], int(row["Date"]))
        for row in remaining_events.values()
        if isinstance(row.get("Name"), int)
        and row.get("Name", 0) > 0
        and row.get("Event")
        and row.get("Date")
    }
    event_additions: List[Dict[str, Any]] = []

    def add_event(lid: int, kind: str, day: int | str) -> None:
        event_date = epoch(day) if isinstance(day, str) else int(day)
        key = event_key(lid, kind, event_date)
        if key in existing_event_keys:
            return
        existing_event_keys.add(key)
        event_additions.append(
            {"fields": {"Name": lid, "Event": kind, "Date": event_date}}
        )

    for sid in legacy_cancelled_targets:
        first, last = attendance[sid]
        add_event(student_to_lead[sid], "Registration", first)
        add_event(student_to_lead[sid], "Cancellation", last)

    for sid in ACTIVE_LEGACY_NEW_LEADS:
        first, _ = attendance[sid]
        add_event(student_to_lead[sid], "Interest", first)
        add_event(student_to_lead[sid], "Registration", first)

    tomer_first, _ = attendance[TOMER_STUDENT_ID]
    add_event(tomer_lead_id, "Interest", tomer_first)
    add_event(tomer_lead_id, "Registration", tomer_first)
    add_event(tomer_lead_id, "Cancellation", "2025-04-03")

    add_event(23, "Registration", "2024-11-12")  # Hanwen
    add_event(28, "Interest", "2023-05-04")  # Zhuoxin
    add_event(28, "Registration", "2023-05-04")
    add_event(28, "Return", "2025-07-29")

    add_event(41, "Registration", "2020-06-18")  # Levy original cycle
    add_event(41, "Cancellation", "2021-08-17")
    add_event(42, "Registration", "2017-03-07")  # Meir original cycle
    add_event(42, "Cancellation", "2024-03-14")
    add_event(160, "Registration", "2017-07-18")  # Slava original cycle
    add_event(160, "Cancellation", "2024-09-24")

    add_event(61, "Notification", "2026-09-14")  # Dor scheduled cancellation
    add_event(61, "Cancellation", "2026-10-14")

    print(f"[PLAN] Add {len(event_additions)} Sales_events")
    if apply and event_additions:
        leads_client.add_records("Sales_events", event_additions)

    if not apply:
        print(
            "[DRY RUN COMPLETE] Expected first apply: "
            "Leads 383->478, Students 131->132, Sales_events 605->789."
        )
        return

    rebuild_sales_summaries(leads_client, apply=True)

    # Populate actual current cancellation dates only after the event writes.
    events_after = leads_client.fetch_records("Sales_events", flat=True)
    cancellations_by_lead: MutableMapping[int, List[int]] = defaultdict(list)
    for row in events_after:
        if (
            row.get("Event") == "Cancellation"
            and isinstance(row.get("Name"), int)
            and row.get("Date")
        ):
            cancellations_by_lead[int(row["Name"])].append(int(row["Date"]))

    cancellation_updates: List[Dict[str, Any]] = []
    for sid, student in students.items():
        if student.get("Status") != "Cancelled":
            continue
        lid = student_to_lead[sid]
        dates = cancellations_by_lead.get(lid, [])
        if not dates:
            raise RuntimeError(f"Cancelled Student {sid} / Lead {lid} has no cancellation")
        cancellation_updates.append(
            {"id": sid, "fields": {"Cancellation_Date": max(dates)}}
        )
    students_client.patch_records("Students", cancellation_updates)

    # Final read-back assertions are deliberately strict so a partial or changed
    # dataset is obvious immediately.
    final_leads = leads_client.fetch_records("Leads", flat=True)
    final_events = leads_client.fetch_records("Sales_events", flat=True)
    final_students = students_client.fetch_records("Students", flat=True)
    lead_by_id = {r["id"]: r for r in final_leads}
    linked_students = {r["id"]: r for r in final_students if r.get("Status") != "Guest"}

    pause_count = sum(r.get("Status") == "Pause" for r in final_leads)
    special_events_left = sum(
        lead_by_id.get(r.get("Name"), {}).get("Status") == "Special event"
        for r in final_events
    )
    registration_count = sum(r.get("Event") == "Registration" for r in final_events)
    return_count = sum(r.get("Event") == "Return" for r in final_events)
    cancellation_count = sum(r.get("Event") == "Cancellation" for r in final_events)

    current_cancelled = [r for r in final_students if r.get("Status") == "Cancelled"]
    missing_cancel_date = [r["id"] for r in current_cancelled if not r.get("Cancellation_Date")]
    missing_links = [
        r["id"]
        for r in final_students
        if r.get("Status") != "Guest" and not r.get("Lead_ID")
    ]
    reciprocal_failures = [
        r["id"]
        for r in final_students
        if r.get("Status") != "Guest"
        and lead_by_id.get(r.get("Lead_ID"), {}).get("Student_ID") != r["id"]
    ]

    expected = {
        "Leads": 478,
        "Students": 132,
        "Events": 789,
        "Registrations": 129,
        "Returns": 5,
        "Cancellations": 114,
        "Pause": 0,
        "Special events with sales rows": 0,
        "Current Cancelled": 108,
    }
    actual = {
        "Leads": len(final_leads),
        "Students": len(final_students),
        "Events": len(final_events),
        "Registrations": registration_count,
        "Returns": return_count,
        "Cancellations": cancellation_count,
        "Pause": pause_count,
        "Special events with sales rows": special_events_left,
        "Current Cancelled": len(current_cancelled),
    }
    if actual != expected:
        raise RuntimeError(f"Final count mismatch: actual={actual}, expected={expected}")
    if missing_cancel_date or missing_links or reciprocal_failures:
        raise RuntimeError(
            "Final integrity failure: "
            f"missing_cancel_date={missing_cancel_date}, missing_links={missing_links}, "
            f"reciprocal_failures={reciprocal_failures}"
        )

    ying = next(r for r in final_students if r.get("Lead_ID") == 24)
    if ying.get("Join_Date"):
        raise RuntimeError("Ying Lin Join_Date must remain unknown")

    print(f"[AFTER] {actual}")
    print(
        "[VERIFIED] Every non-Guest Student has a reciprocal Lead link; every "
        "currently Cancelled Student has Cancellation_Date and a Lead cancellation."
    )
    print(
        "[KNOWN EXCEPTION] Ying Lin has no Registration because her first attendance "
        "cannot be recovered; cancellation 2025-06-19 is preserved."
    )


if __name__ == "__main__":
    main()
