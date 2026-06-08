"""Shared normalization, deduplication, and logging helpers.

Used by both the CSV lead importer (grist_leads_source.py) and the
Meta Graph API lead sync (sync_meta_leads.py). This module must not call
print() directly -- all formatted output is produced by format_squawk()
and emitted by the CLI layer.
"""
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
_HEBREW_RE = re.compile(r"[֐-׿]")
_EMAIL_RE = re.compile(r"^\s*[^@\s]+@[^@\s]+\.[^@\s]+\s*$", re.IGNORECASE)


def is_hebrew(s: str) -> bool:
    return bool(_HEBREW_RE.search(s or ""))


def norm_email(email: Optional[str]) -> str:
    if not email:
        return ""
    e = str(email).strip().lower()
    return e  # keep as-is; validation is best-effort


def norm_phone(phone: Optional[str]) -> str:
    """Normalize a phone number to a canonical digit-only form.

    Canonical form for Israeli numbers: 972XXXXXXXXX (no +, no leading 0).
    Non-Israeli or unknown formats are returned as digits only after stripping
    the leading + (if present).
    """
    if not phone:
        return ""
    p = re.sub(r"[^\d+]", "", str(phone).strip())
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("972"):
        return p                            # already canonical
    if p.startswith("0") and len(p) in {9, 10}:
        return "972" + p[1:]               # 052... or 05... → 97252...
    return p                               # non-Israeli or unknown, return as-is


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None

    formats = [
        None,             # fromisoformat: handles 2025-12-26T10:13:34+02:00
        "%Y-%m-%d",       # Grist date columns
        "%m/%d/%Y %I:%M%p",  # CSV export: 01/01/2026 7:10am
        "%d/%m/%Y %I:%M%p",
    ]
    for fmt in formats:
        try:
            dt = datetime.fromisoformat(s) if fmt is None else datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None


def dt_to_grist_date(d: datetime) -> str:
    return d.date().isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pick_first_nonempty(*vals: Optional[str]) -> str:
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def safe_get(fields: Dict[str, Any], col: str) -> str:
    v = fields.get(col)
    return "" if v is None else str(v).strip()


# ---------------------------------------------------------------------------
# Grist index building
# ---------------------------------------------------------------------------
def build_index(
    grist_records: List[Dict[str, Any]],
    col_phone: str,
    col_email: str,
) -> Tuple[Dict[Tuple[str, str], Dict[str, Any]], List[Dict[str, Any]]]:
    """Build (norm_phone, norm_email) → grist_record index.

    Returns (index, warnings) where warnings are structured dicts for
    format_squawk.
    """
    idx: Dict[Tuple[str, str], Dict[str, Any]] = {}
    warnings: List[Dict[str, Any]] = []
    for rec in grist_records:
        fields = rec.get("fields", {}) or {}
        key = (norm_phone(fields.get(col_phone)), norm_email(fields.get(col_email)))
        if key == ("", ""):
            continue
        if key in idx:
            warnings.append({
                "type": "DUPLICATE_GRIST_KEY",
                "phone": key[0],
                "email": key[1],
                "detail": {
                    "kept_id": idx[key].get("id"),
                    "also_saw_id": rec.get("id"),
                },
            })
            continue
        idx[key] = rec
    return idx, warnings


# ---------------------------------------------------------------------------
# Conservative update logic
# ---------------------------------------------------------------------------
def compute_updates_for_match(
    *,
    grist_fields: Dict[str, Any],
    fb_name: str,
    fb_phone: str,
    fb_email: str,
    fb_campaign: str,
    fb_ad: str,
    fb_platform: str,
    fb_created: Optional[datetime],
    cols: Dict[str, str],
    max_gap_days: int,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Return (fields_to_update, structured_warnings).

    Only fills fields that are blank in Grist. Never overwrites Status,
    names, campaign attribution, or other manually-entered CRM data.
    Warnings are structured dicts (no raw formatting) for redaction at
    the CLI layer via format_squawk().
    """
    squawks: List[Dict[str, Any]] = []
    upd: Dict[str, Any] = {}

    existing_phone = safe_get(grist_fields, cols["phone"])
    existing_email = safe_get(grist_fields, cols["email"])
    existing_name_en = safe_get(grist_fields, cols["name_en"])
    existing_name_he = safe_get(grist_fields, cols["name_he"])
    existing_campaign = safe_get(grist_fields, cols["campaign"])
    existing_ad = safe_get(grist_fields, cols["ad_name"])
    existing_platform = safe_get(grist_fields, cols["platform"])
    existing_date = parse_dt(safe_get(grist_fields, cols["date"]))

    fb_is_he = is_hebrew(fb_name)
    fb_name = fb_name.strip()

    if fb_name:
        if fb_is_he and not existing_name_he:
            upd[cols["name_he"]] = fb_name
            if existing_name_en:
                squawks.append({
                    "type": "NAME_COMPLEMENT",
                    "phone": fb_phone,
                    "email": fb_email,
                    "detail": {"added_he": fb_name, "existing_en": existing_name_en},
                })
        elif (not fb_is_he) and not existing_name_en:
            upd[cols["name_en"]] = fb_name
            if existing_name_he:
                squawks.append({
                    "type": "NAME_COMPLEMENT",
                    "phone": fb_phone,
                    "email": fb_email,
                    "detail": {"added_en": fb_name, "existing_he": existing_name_he},
                })
        else:
            if fb_is_he and existing_name_he and fb_name != existing_name_he:
                squawks.append({
                    "type": "NAME_MISMATCH",
                    "phone": fb_phone,
                    "email": fb_email,
                    "detail": {"script": "he", "grist": existing_name_he, "fb": fb_name},
                })
            if (not fb_is_he) and existing_name_en and fb_name != existing_name_en:
                squawks.append({
                    "type": "NAME_MISMATCH",
                    "phone": fb_phone,
                    "email": fb_email,
                    "detail": {"script": "en", "grist": existing_name_en, "fb": fb_name},
                })

    # Source columns: never overwrite; only fill if blank
    if fb_campaign and not existing_campaign:
        upd[cols["campaign"]] = fb_campaign
    elif fb_campaign and existing_campaign and fb_campaign != existing_campaign:
        squawks.append({
            "type": "SOURCE_MISMATCH",
            "phone": fb_phone,
            "email": fb_email,
            "detail": {"field": "campaign", "grist": existing_campaign, "fb": fb_campaign},
        })

    if fb_ad and not existing_ad:
        upd[cols["ad_name"]] = fb_ad
    elif fb_ad and existing_ad and fb_ad != existing_ad:
        squawks.append({
            "type": "SOURCE_MISMATCH",
            "phone": fb_phone,
            "email": fb_email,
            "detail": {"field": "ad_name", "grist": existing_ad, "fb": fb_ad},
        })

    if fb_platform and not existing_platform:
        upd[cols["platform"]] = fb_platform
    elif fb_platform and existing_platform and fb_platform != existing_platform:
        squawks.append({
            "type": "SOURCE_MISMATCH",
            "phone": fb_phone,
            "email": fb_email,
            "detail": {"field": "platform", "grist": existing_platform, "fb": fb_platform},
        })

    # Time gap check
    if fb_created and existing_date:
        fb_aware = fb_created if fb_created.tzinfo else fb_created.replace(tzinfo=timezone.utc)
        ex_aware = existing_date if existing_date.tzinfo else existing_date.replace(tzinfo=timezone.utc)
        gap_days = abs(fb_aware - ex_aware).days
        if gap_days > max_gap_days:
            squawks.append({
                "type": "TIME_GAP",
                "phone": fb_phone,
                "email": fb_email,
                "detail": {
                    "fb_created": fb_created.isoformat(),
                    "grist_date": existing_date.isoformat(),
                    "gap_days": gap_days,
                    "max_gap_days": max_gap_days,
                },
            })

    # Fill missing date from FB created_time
    if fb_created and not safe_get(grist_fields, cols["date"]):
        upd[cols["date"]] = dt_to_grist_date(fb_created)

    # Fill missing phone/email
    if fb_phone and not existing_phone:
        upd[cols["phone"]] = fb_phone
    if fb_email and not existing_email:
        upd[cols["email"]] = fb_email

    return upd, squawks


# ---------------------------------------------------------------------------
# PII-safe logging
# ---------------------------------------------------------------------------
def redact_phone(phone: str) -> str:
    """Show only the last 4 digits: ***4567."""
    digits = re.sub(r"\D", "", phone)
    if not digits:
        return "***"
    return "***" + digits[-4:]


def redact_email(email: str) -> str:
    """Show first character + *** + @domain: o***@gmail.com."""
    if "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    first = local[0] if local else ""
    return f"{first}***@{domain}"


def format_squawk(w: Dict[str, Any], verbose_pii: bool = False) -> str:
    """Format a structured warning dict into a printable string.

    Phone and email are redacted unless verbose_pii=True.
    """
    t = w.get("type", "UNKNOWN")
    raw_phone = w.get("phone", "")
    raw_email = w.get("email", "")
    detail = w.get("detail", {})

    phone_str = raw_phone if verbose_pii else redact_phone(raw_phone)
    email_str = raw_email if verbose_pii else redact_email(raw_email)

    if t == "NAME_MISMATCH":
        script = detail.get("script", "?")
        return (
            f"[NAME MISMATCH] phone={phone_str} email={email_str} : "
            f"Grist {script.upper()}='{detail.get('grist')}' vs "
            f"FB {script.upper()}='{detail.get('fb')}'. (No overwrite.)"
        )
    if t == "NAME_COMPLEMENT":
        added_he = detail.get("added_he")
        added_en = detail.get("added_en")
        if added_he:
            return (
                f"[NAME COMPLEMENT] Added Hebrew name='{added_he}' "
                f"(English already present '{detail.get('existing_en')}')."
            )
        return (
            f"[NAME COMPLEMENT] Added English name='{added_en}' "
            f"(Hebrew already present '{detail.get('existing_he')}')."
        )
    if t == "SOURCE_MISMATCH":
        field = detail.get("field", "?")
        return (
            f"[SOURCE MISMATCH] phone={phone_str} email={email_str} : "
            f"{field} Grist='{detail.get('grist')}' vs FB='{detail.get('fb')}'. (No overwrite.)"
        )
    if t == "TIME_GAP":
        return (
            f"[TIME GAP] phone={phone_str} email={email_str} : "
            f"FB created={detail.get('fb_created')} vs Grist date={detail.get('grist_date')} "
            f"(gap={detail.get('gap_days')}d > max={detail.get('max_gap_days')}d)."
        )
    if t == "DUPLICATE_GRIST_KEY":
        return (
            f"[DUPLICATE KEY] Multiple Grist rows share phone+email "
            f"phone={phone_str} email={email_str}. "
            f"Keeping id={detail.get('kept_id')}, also saw id={detail.get('also_saw_id')}."
        )
    if t == "PARTIAL_CONTACT_SKIPPED":
        reason = detail.get("reason", "missing phone or email")
        return f"[SKIP] Lead skipped ({reason}). meta_lead_id={detail.get('meta_lead_id', '')}."
    if t == "DUPLICATE_IN_RUN":
        return (
            f"[DUPLICATE IN RUN] Lead already processed this run, skipping. "
            f"meta_lead_id={detail.get('meta_lead_id', '')} "
            f"phone={phone_str} email={email_str}."
        )
    if t == "DUPLICATE_META_ID_IN_GRIST":
        return (
            f"[DUPLICATE META ID] Multiple Grist rows share meta_lead_id="
            f"'{detail.get('meta_lead_id')}'. "
            f"Keeping id={detail.get('kept_id')}, also saw id={detail.get('also_saw_id')}."
        )
    # Fallback for unknown warning types
    return f"[{t}] phone={phone_str} email={email_str} detail={json.dumps(detail)}"
