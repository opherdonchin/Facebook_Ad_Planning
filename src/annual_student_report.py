"""Build the annual-conversation data pack for every current Aikido student.

Read-only. Source of truth is the Grist "Students" document:

  Students            one row per person; Status, Join_Date, and one Date
                      column per rank (Kyu_6..Kyu_1, Dan_1..Dan_4)
  Sessions            one row per PRACTICE DAY (Date) with a RefList of the
                      students present; verified 1:1 rows-to-dates
  Rank_requirements   Rank -> required Classes and Months for that rank

Attendance is recorded per practice day, not per class, so every count here is
a count of distinct Sessions.Date values. Nothing is inferred about the number
of classes, sessions or hours on a given day.

Usage:
    python src/annual_student_report.py --config config.json
    python src/annual_student_report.py --snapshot path/to/snapshot.json
    python src/annual_student_report.py --config config.json --as-of 2026-09-15
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Lowest to highest. Each name is both the Students column (with the space
# replaced by an underscore) and the Rank_requirements.Rank value.
RANK_ORDER = [
    "Kyu 6", "Kyu 5", "Kyu 4", "Kyu 3", "Kyu 2", "Kyu 1",
    "Dan 1", "Dan 2", "Dan 3", "Dan 4", "Dan 5",
]

ACTIVE_STATUS = "Active Student"
WINDOW_DAYS = 365

# One row per student, pulled with distinct-date semantics so a student listed
# twice inside a single session's RefList still counts as one practice day.
SESSION_COUNT_SQL = """
SELECT COUNT(DISTINCT Date) AS n FROM Sessions WHERE Date BETWEEN :win_start AND :win_end
"""

STUDENT_SQL = """
WITH att AS (
  SELECT DISTINCT CAST(j.value AS INTEGER) AS sid, s.Date AS d
  FROM Sessions s, json_each(s.Students_Present) j
)
SELECT st.id, st.Name, st.Status, st.Sex, st.Teacher, st.Join_Date, st.Birthday,
       st.Paid_until, st.Pause_until,
       st.Kyu_6, st.Kyu_5, st.Kyu_4, st.Kyu_3, st.Kyu_2, st.Kyu_1,
       st.Dan_1, st.Dan_2, st.Dan_3, st.Dan_4,
       st.Current_Rank, st.Next_Rank, st.Required_Months, st.Required_Classes,
       st.Date_Last_Test, st.Months_Since_Last_Test, st.Sessions_Since_Testing,
       st.Total_Session,
       (SELECT COUNT(*) FROM att a WHERE a.sid = st.id) AS total_days,
       (SELECT MIN(a.d) FROM att a WHERE a.sid = st.id) AS first_ever,
       (SELECT MAX(a.d) FROM att a WHERE a.sid = st.id) AS last_ever,
       (SELECT COUNT(*) FROM att a
         WHERE a.sid = st.id AND a.d BETWEEN :win_start AND :win_end) AS days_365,
       (SELECT MIN(a.d) FROM att a
         WHERE a.sid = st.id AND a.d BETWEEN :win_start AND :win_end) AS first_365,
       (SELECT MAX(a.d) FROM att a
         WHERE a.sid = st.id AND a.d BETWEEN :win_start AND :win_end) AS last_365,
       (SELECT COUNT(*) FROM att a
         WHERE a.sid = st.id
           AND a.d > COALESCE(st.Date_Last_Test, st.Join_Date)) AS days_since_test,
       (SELECT COUNT(*) FROM att a
         WHERE a.sid = st.id AND a.d < st.Join_Date) AS days_before_join
FROM Students st
WHERE st.Status = :status
ORDER BY st.id
"""


# --------------------------------------------------------------------------
# dates
# --------------------------------------------------------------------------

def to_date(epoch: Optional[float]) -> Optional[dt.date]:
    """Grist Date columns are UTC-midnight epoch seconds."""
    if epoch is None or epoch == "":
        return None
    return dt.datetime.fromtimestamp(float(epoch), dt.timezone.utc).date()


def iso(d: Optional[dt.date]) -> str:
    return d.isoformat() if d else ""


def to_epoch(d: dt.date) -> int:
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def whole_months(start: Optional[dt.date], end: dt.date) -> Optional[int]:
    """Completed calendar months between two dates, matching Grist DATEDIF 'M'."""
    if start is None:
        return None
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def add_months(start: dt.date, months: int) -> dt.date:
    total = start.year * 12 + (start.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0)
                          else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return dt.date(year, month, day)


def years_and_months(start: Optional[dt.date], end: dt.date) -> str:
    m = whole_months(start, end)
    if m is None:
        return ""
    return f"{m // 12}y {m % 12}m"


# --------------------------------------------------------------------------
# rank
# --------------------------------------------------------------------------

def rank_history(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every rank this student holds a date for, lowest first."""
    out = []
    for rank in RANK_ORDER:
        d = to_date(rec.get(rank.replace(" ", "_")))
        if d:
            out.append({"rank": rank, "date": d})
    return out


def next_rank(current: Optional[str]) -> Optional[str]:
    if current is None:
        return RANK_ORDER[0]
    i = RANK_ORDER.index(current)
    return RANK_ORDER[i + 1] if i + 1 < len(RANK_ORDER) else None


# --------------------------------------------------------------------------
# per-student derivation
# --------------------------------------------------------------------------

def summarise(rec: Dict[str, Any], ref: dt.date, reqs: Dict[str, Dict[str, float]],
              sessions_in_window: Optional[int] = None) -> Dict[str, Any]:
    history = rank_history(rec)
    current = history[-1] if history else None
    previous = history[-2] if len(history) > 1 else None

    join = to_date(rec.get("Join_Date"))
    first_ever = to_date(rec.get("first_ever"))
    days_365 = int(rec.get("days_365") or 0)

    # The dojo's eligibility rule, read off Students.Eligible in Grist:
    #   months_since_last_test >= required_months - 1
    #   AND practice_days_since_last_test >= required_classes * 0.9
    # When a student has never tested, Join_Date stands in for the test date.
    anchor = current["date"] if current else join
    months_since = whole_months(anchor, ref)
    nxt = next_rank(current["rank"] if current else None)
    req = reqs.get(nxt or "", {})
    req_months = req.get("Months")
    req_classes = req.get("Classes")
    days_since_test = int(rec.get("days_since_test") or 0)

    months_ok = classes_ok = eligible = None
    months_met_on = None
    classes_short = None
    if req_months is not None and req_classes is not None and months_since is not None:
        months_ok = months_since >= req_months - 1
        classes_ok = days_since_test >= req_classes * 0.9
        eligible = bool(months_ok and classes_ok)
        # The months half of the rule resolves to an exact date; the classes
        # half cannot, because it depends on attendance that has not happened.
        months_met_on = add_months(anchor, int(req_months) - 1) if anchor else None
        classes_short = max(0, int(round(req_classes * 0.9)) - days_since_test)

    return {
        "student_id": rec["id"],
        "name": rec["Name"],
        "sex": rec.get("Sex") or "",
        "is_teacher": bool(rec.get("Teacher")),
        "practice_days_365": days_365,
        "practices_per_week": round(days_365 / (WINDOW_DAYS / 7), 2),
        "first_practice_in_window": to_date(rec.get("first_365")),
        "last_practice_in_window": to_date(rec.get("last_365")),
        "first_practice_ever": first_ever,
        "last_practice_ever": to_date(rec.get("last_ever")),
        "join_date": join,
        "time_with_us": years_and_months(join, ref),
        "months_with_us": whole_months(join, ref),
        "total_practice_days": int(rec.get("total_days") or 0),
        "practice_days_available": sessions_in_window,
        "share_of_practice_days": (round(days_365 / sessions_in_window, 3)
                                   if sessions_in_window else None),
        "current_rank": current["rank"] if current else "",
        "current_rank_date": current["date"] if current else None,
        # Only meaningful when a rank date exists. For never-tested students the
        # rule falls back to Join_Date; that value lives in months_since_anchor.
        "months_since_rank": months_since if current else None,
        "months_since_anchor": months_since,
        "rule_anchor_date": anchor,
        "previous_rank": previous["rank"] if previous else "",
        "previous_rank_date": previous["date"] if previous else None,
        "rank_anchor_is_join_date": current is None,
        "next_rank": nxt or "",
        "required_months": req_months,
        "required_classes": req_classes,
        "practice_days_since_rank": days_since_test,
        "months_criterion_met": months_ok,
        "months_criterion_met_on": months_met_on,
        "classes_criterion_met": classes_ok,
        "practice_days_still_needed": classes_short,
        "eligible_now": eligible,
        "paid_until": to_date(rec.get("Paid_until")),
        "birthday": to_date(rec.get("Birthday")),
        "practice_days_before_join_date": int(rec.get("days_before_join") or 0),
        "grist_total_session": rec.get("Total_Session"),
        "grist_sessions_since_testing": rec.get("Sessions_Since_Testing"),
        "grist_months_since_last_test": rec.get("Months_Since_Last_Test"),
    }


def eligibility_label(row: Dict[str, Any]) -> str:
    """Status only. No date is invented for the classes half of the rule."""
    if row["eligible_now"] is None:
        return "no rule (top rank)"
    if row["eligible_now"]:
        return f"Eligible now for {row['next_rank']}"
    if row["months_criterion_met"]:
        return f"{row['next_rank']}: {row['practice_days_still_needed']} more practice days"
    if row["classes_criterion_met"]:
        return f"{row['next_rank']}: time from {iso(row['months_criterion_met_on'])}"
    return (f"{row['next_rank']}: {row['practice_days_still_needed']} more days, "
            f"time from {iso(row['months_criterion_met_on'])}")


# --------------------------------------------------------------------------
# io
# --------------------------------------------------------------------------

MAIN_COLUMNS = [
    ("name", "Student"),
    ("practice_days_365", "Practice days last 365d"),
    ("practices_per_week", "Practices/week"),
    ("share_of_practice_days", "Share of dojo practice days"),
    ("first_practice_ever", "First practice"),
    ("join_date", "Join date"),
    ("time_with_us", "Time with us"),
    ("total_practice_days", "Total practice days"),
    ("current_rank", "Current rank"),
    ("current_rank_date", "Rank date"),
    ("months_since_rank", "Months since rank"),
    ("eligibility", "Next shinsa/eligibility"),
]


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def write_csv(rows: List[Dict[str, Any]], path: Path, ref: dt.date) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow([f"Reference date: {ref.isoformat()}"])
        w.writerow([f"Window: {(ref - dt.timedelta(days=WINDOW_DAYS - 1)).isoformat()}"
                    f" to {ref.isoformat()} (365 days inclusive)"])
        w.writerow([])
        w.writerow([label for _, label in MAIN_COLUMNS])
        for row in rows:
            w.writerow([fmt(row.get(key)) for key, _ in MAIN_COLUMNS])


def write_markdown(rows, path, ref, sessions_in_window):
    win_start = ref - dt.timedelta(days=WINDOW_DAYS - 1)
    L = []
    L.append("# Annual student conversation data")
    L.append("")
    L.append(f"**Reference date:** {ref.isoformat()}  ")
    L.append(f"**Practice window:** {win_start.isoformat()} to {ref.isoformat()} "
             f"(365 days, inclusive)  ")
    L.append(f"**Active students:** {len(rows)} (`Students.Status = \"Active Student\"`)  ")
    if sessions_in_window:
        L.append(f"**Practice days the dojo recorded in the window:** {sessions_in_window} "
                 f"({sessions_in_window / (WINDOW_DAYS / 7):.2f}/week) — this is the ceiling "
                 f"for every student's count  ")
    L.append("")
    L.append("Attendance is recorded one row per practice day. Every count below is a count "
             "of distinct practice dates; no classes, sessions or hours are inferred.")
    L.append("")
    L.append("## Summary table")
    L.append("")
    headers = [label for _, label in MAIN_COLUMNS]
    L.append("| " + " | ".join(headers) + " |")
    L.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        cells = []
        for key, _ in MAIN_COLUMNS:
            v = r.get(key)
            if key == "share_of_practice_days" and v is not None:
                cells.append(f"{v * 100:.0f}%")
            else:
                cells.append(fmt(v) or "—")
        L.append("| " + " | ".join(cells) + " |")
    L.append("")
    L.append("## Per-student detail")
    L.append("")
    for r in rows:
        L.append(f"### {r['name']}")
        L.append("")
        L.append(f"- **Practice, last 365 days:** {r['practice_days_365']} days "
                 f"({r['practices_per_week']}/week"
                 + (f", {r['share_of_practice_days'] * 100:.0f}% of the "
                    f"{sessions_in_window} practice days offered"
                    if r["share_of_practice_days"] is not None else "") + ")")
        L.append(f"- **First / last practice in window:** "
                 f"{fmt(r['first_practice_in_window']) or '—'} → "
                 f"{fmt(r['last_practice_in_window']) or '—'}")
        L.append(f"- **Join date (field):** {fmt(r['join_date']) or '—'}  ·  "
                 f"**First recorded practice:** {fmt(r['first_practice_ever']) or '—'}")
        L.append(f"- **Time with us:** {r['time_with_us']} "
                 f"({r['months_with_us']} months from Join date)")
        L.append(f"- **Total practice days on record:** {r['total_practice_days']}")
        if r["current_rank"]:
            L.append(f"- **Current rank:** {r['current_rank']}, graded "
                     f"{fmt(r['current_rank_date'])} ({r['months_since_rank']} months ago)")
            if r["previous_rank"]:
                L.append(f"- **Previous rank:** {r['previous_rank']}, "
                         f"{fmt(r['previous_rank_date'])}")
            else:
                L.append("- **Previous rank:** none recorded (first rank in this database)")
        else:
            L.append("- **Current rank:** none recorded (never tested here)")
        if r["next_rank"]:
            L.append(f"- **Next rank:** {r['next_rank']} — dojo requirement "
                     f"{fmt(r['required_months'])} months and "
                     f"{fmt(r['required_classes'])} classes")
            anchor_note = ("since joining" if r["rank_anchor_is_join_date"]
                           else "since last shinsa")
            L.append(f"- **Progress {anchor_note}** (from "
                     f"{fmt(r['rule_anchor_date'])}): {r['months_since_anchor']} months, "
                     f"{r['practice_days_since_rank']} practice days")
            L.append(f"- **Eligibility (dojo rule):** "
                     f"{'ELIGIBLE NOW' if r['eligible_now'] else 'not yet'} — "
                     f"time criterion {'met' if r['months_criterion_met'] else 'not met'} "
                     f"(threshold {fmt(r['months_criterion_met_on'])}), "
                     f"practice criterion "
                     f"{'met' if r['classes_criterion_met'] else 'not met'}"
                     + (f" ({r['practice_days_still_needed']} more practice days needed)"
                        if r["practice_days_still_needed"] else ""))
        else:
            L.append("- **Next rank:** none — highest rank in the requirements table")
        extras = []
        if r["is_teacher"]:
            extras.append("marked as a teacher")
        if r["paid_until"]:
            state = "expired" if r["paid_until"] < ref else "current"
            extras.append(f"paid until {fmt(r['paid_until'])} ({state})")
        else:
            extras.append("no Paid until date on file")
        if r["practice_days_before_join_date"]:
            extras.append(f"{r['practice_days_before_join_date']} practice day(s) recorded "
                          f"BEFORE the Join date")
        if r["last_practice_ever"] and (ref - r["last_practice_ever"]).days > 60:
            extras.append(f"last practised {(ref - r['last_practice_ever']).days} days ago")
        if extras:
            L.append("- **Notes:** " + "; ".join(extras))
        L.append("")
    path.write_text("\n".join(L), encoding="utf-8")


def fetch_from_grist(config_path: Path, ref: dt.date):
    import requests

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    section = cfg.get("students") or cfg.get("aikido") or {}
    doc_id = section["doc_id"]
    server = section.get("server", "https://docs.getgrist.com").rstrip("/")
    headers = {"Authorization": f"Bearer {section['api_key']}"}

    win_start = to_epoch(ref - dt.timedelta(days=WINDOW_DAYS - 1))
    win_end = to_epoch(ref)

    def sql(query: str, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        r = requests.post(f"{server}/api/docs/{doc_id}/sql",
                          json={"sql": query, "args": args},
                          headers=headers, timeout=60)
        r.raise_for_status()
        return [rec["fields"] for rec in r.json()["records"]]

    students = sql(STUDENT_SQL, {"win_start": win_start, "win_end": win_end,
                                 "status": ACTIVE_STATUS})
    reqs = sql("SELECT Rank, Classes, Months FROM Rank_requirements", {})
    n = sql(SESSION_COUNT_SQL, {"win_start": win_start, "win_end": win_end})[0]["n"]
    return students, {r["Rank"]: r for r in reqs}, n


# Mirrors Rank_requirements; used only when running from a snapshot.
FALLBACK_REQUIREMENTS = [
    {"Rank": "Kyu 6", "Classes": 30, "Months": 3},
    {"Rank": "Kyu 5", "Classes": 60, "Months": 4},
    {"Rank": "Kyu 4", "Classes": 60, "Months": 4},
    {"Rank": "Kyu 3", "Classes": 70, "Months": 4},
    {"Rank": "Kyu 2", "Classes": 80, "Months": 6},
    {"Rank": "Kyu 1", "Classes": 90, "Months": 6},
    {"Rank": "Dan 1", "Classes": 120, "Months": 12},
    {"Rank": "Dan 2", "Classes": 400, "Months": 30},
    {"Rank": "Dan 3", "Classes": 500, "Months": 40},
    {"Rank": "Dan 4", "Classes": 640, "Months": 48},
    {"Rank": "Dan 5", "Classes": 800, "Months": 60},
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, help="config.json holding the Grist doc_id/api_key")
    ap.add_argument("--snapshot", type=Path, help="pre-fetched STUDENT_SQL result as JSON")
    ap.add_argument("--sessions-in-window", type=int,
                    help="dojo-wide practice days in the window (snapshot mode only)")
    ap.add_argument("--as-of", default=dt.date.today().isoformat(),
                    help="reference date, YYYY-MM-DD (default: today)")
    ap.add_argument("--outdir", type=Path,
                    default=Path(__file__).resolve().parent.parent / "outputs" / "student_reviews")
    args = ap.parse_args()

    ref = dt.date.fromisoformat(args.as_of)

    if args.snapshot:
        records = json.loads(args.snapshot.read_text(encoding="utf-8"))
        reqs = {r["Rank"]: r for r in FALLBACK_REQUIREMENTS}
        sessions_in_window = args.sessions_in_window
    elif args.config:
        records, reqs, sessions_in_window = fetch_from_grist(args.config, ref)
    else:
        ap.error("pass --config or --snapshot")

    rows = [summarise(rec, ref, reqs, sessions_in_window) for rec in records]
    for row in rows:
        row["eligibility"] = eligibility_label(row)
    rows.sort(key=lambda r: (-r["practice_days_365"], r["name"]))

    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = f"annual_student_conversation_data_{ref.isoformat()}"

    csv_path = args.outdir / f"{stem}.csv"
    write_csv(rows, csv_path, ref)

    md_path = args.outdir / f"{stem}.md"
    write_markdown(rows, md_path, ref, sessions_in_window)

    json_path = args.outdir / f"{stem}.json"
    json_path.write_text(
        json.dumps([{k: fmt(v) if isinstance(v, dt.date) else v for k, v in r.items()}
                    for r in rows], ensure_ascii=False, indent=2),
        encoding="utf-8")

    print(f"Reference date {ref.isoformat()}; {len(rows)} active students; "
          f"{sessions_in_window} dojo practice days in window")
    for pth in (csv_path, md_path, json_path):
        print(f"  {pth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
