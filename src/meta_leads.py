"""Meta Graph API lead fetcher and normalizer.

Fetches lead submissions from the Meta Leads API for configured form IDs,
normalizes the raw API response into a canonical internal shape, and returns
a list of lead dicts for the sync layer to process.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests

from lead_utils import norm_email, norm_phone, parse_dt


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class MetaLeadsError(Exception):
    """Base error for Meta Graph API problems."""


class MetaAuthError(MetaLeadsError):
    """401 / 403 or missing permissions."""


class MetaRateLimitError(MetaLeadsError):
    """HTTP 429 — rate limit hit."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
_CORE_FIELDS = "created_time,id,ad_id,form_id,field_data"
_ENRICHMENT_FIELDS = "ad_name,adset_id,campaign_id,campaign_name"


class MetaLeadsClient:
    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: Optional[str] = None,
        api_version: str = "v25.0",
    ) -> None:
        """Load token from param → META_ACCESS_TOKEN env var.

        Raises ValueError if no token is found.
        """
        token = access_token or os.environ.get("META_ACCESS_TOKEN", "")
        if not token:
            raise ValueError(
                "Meta access token is required. "
                "Set the META_ACCESS_TOKEN environment variable, "
                "or provide access_token in config['meta']['access_token']."
            )
        self.access_token = token
        self.api_version = api_version
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.BASE_URL}/{self.api_version}/{path.lstrip('/')}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = dict(params or {})
        p["access_token"] = self.access_token
        r = self.session.get(self._url(path), params=p, timeout=30)

        if r.status_code in (401, 403):
            try:
                msg = r.json().get("error", {}).get("message", r.text)
            except Exception:
                msg = r.text
            raise MetaAuthError(
                f"Meta API authentication/permission error ({r.status_code}): {msg}"
            )
        if r.status_code == 429:
            raise MetaRateLimitError(
                f"Meta API rate limit hit ({r.status_code}). Back off before retrying. "
                f"Response: {r.text[:200]}"
            )
        r.raise_for_status()
        return r.json()

    def fetch_leads(
        self,
        form_id: str,
        lookback_days: int = 14,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all leads for form_id submitted since the lookback window.

        Tries server-side date filtering first; if Meta returns an API error
        on that parameter, falls back to fetching all pages and filtering
        client-side by created_time.

        Returns a flat list of raw lead dicts as returned by the Graph API.
        """
        if since is not None:
            since_ts = int(since.timestamp())
        else:
            since_ts = int(
                (datetime.now(timezone.utc) - timedelta(days=lookback_days)).timestamp()
            )

        fields = f"{_CORE_FIELDS},{_ENRICHMENT_FIELDS}"
        base_params: Dict[str, Any] = {"fields": fields, "limit": 100}

        # Attempt server-side filtering
        filter_json = json.dumps(
            [{"field": "time_created", "operator": "GREATER_THAN", "value": since_ts}]
        )
        server_side_ok = True
        all_leads: List[Dict[str, Any]] = []

        try:
            all_leads = self._paginate(form_id, {**base_params, "filtering": filter_json})
        except requests.HTTPError as exc:
            resp = exc.response
            if resp is not None and resp.status_code == 400:
                # Meta rejected the filtering param — fall back to client-side
                print(
                    f"[INFO] Server-side date filtering not supported for form {form_id}. "
                    f"Falling back to client-side filtering (fetching all pages)."
                )
                server_side_ok = False
            else:
                raise

        if not server_side_ok:
            all_pages = self._paginate(form_id, base_params)
            cutoff = datetime.fromtimestamp(since_ts, tz=timezone.utc)
            all_leads = [
                lead for lead in all_pages
                if _lead_created_after(lead, cutoff)
            ]

        return all_leads

    def _paginate(
        self,
        form_id: str,
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Paginate through all pages for a given form leads request."""
        results: List[Dict[str, Any]] = []
        path = f"{form_id}/leads"
        current_params = dict(params)

        while True:
            data = self._get(path, current_params)
            page = data.get("data", [])
            results.extend(page)

            paging = data.get("paging", {})
            cursors = paging.get("cursors", {})
            after = cursors.get("after")

            if not after or not page:
                break
            current_params = dict(params)
            current_params["after"] = after

        return results


def _lead_created_after(raw: Dict[str, Any], cutoff: datetime) -> bool:
    """Return True if the lead's created_time is at or after cutoff."""
    dt = parse_dt(raw.get("created_time"))
    if dt is None:
        return True  # include leads with unparseable timestamps
    return dt >= cutoff


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
_PHONE_ALIASES = {"phone_number", "phone", "whatsapp_number", "whatsapp"}
_NAME_ALIASES = {"full_name", "name"}


def flatten_field_data(field_data: List[Dict[str, Any]]) -> Dict[str, str]:
    """Flatten Meta field_data list into a plain dict.

    Normalizes field name aliases:
      phone_number / phone / whatsapp_number → "phone_number"
      full_name / name                       → "full_name"
      email                                  → "email"
    Unknown field names are preserved as-is.
    """
    out: Dict[str, str] = {}
    for item in field_data or []:
        raw_name = (item.get("name") or "").strip().lower()
        values = item.get("values") or []
        value = str(values[0]) if values else ""

        if raw_name in _PHONE_ALIASES:
            out["phone_number"] = value
        elif raw_name in _NAME_ALIASES:
            out["full_name"] = value
        elif raw_name == "email":
            out["email"] = value
        else:
            out[raw_name] = value
    return out


def parse_meta_lead(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single raw Meta lead dict into the internal shape.

    Returns:
      {
        "meta_lead_id": str,
        "created_time": Optional[datetime],
        "ad_id": str,
        "ad_name": str,          # "" if absent
        "adset_id": str,         # "" if absent
        "campaign_id": str,      # "" if absent
        "campaign_name": str,    # "" if absent
        "form_id": str,
        "phone_number": str,     # norm_phone applied
        "email": str,            # norm_email applied
        "full_name": str,
        "raw": dict,             # original unmodified dict
      }
    """
    flat = flatten_field_data(raw.get("field_data") or [])

    def _s(key: str) -> str:
        v = raw.get(key)
        return str(v).strip() if v is not None else ""

    return {
        "meta_lead_id": _s("id"),
        "created_time": parse_dt(_s("created_time")),
        "ad_id": _s("ad_id"),
        "ad_name": _s("ad_name"),
        "adset_id": _s("adset_id"),
        "campaign_id": _s("campaign_id"),
        "campaign_name": _s("campaign_name"),
        "form_id": _s("form_id"),
        "phone_number": norm_phone(flat.get("phone_number", "")),
        "email": norm_email(flat.get("email", "")),
        "full_name": flat.get("full_name", "").strip(),
        "raw": raw,
    }
