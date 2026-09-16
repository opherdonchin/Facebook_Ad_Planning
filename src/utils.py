import json
import os
from typing import Any, Dict
from urllib.parse import urlsplit


def load_config(path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        The configuration dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Configuration file '{path}' not found. "
            "Please copy config.example.json to config.json and add your credentials."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def require_grist_profile(
    config: Dict[str, Any], profile_name: str
) -> Dict[str, Any]:
    """Return a Grist profile with an explicit document, key, and server."""
    profile = config.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"Grist profile {profile_name!r} is missing or invalid.")

    required = ("doc_id", "api_key", "server")
    missing = [
        key
        for key in required
        if not isinstance(profile.get(key), str) or not profile[key].strip()
    ]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(
            f"Grist profile {profile_name!r} must include non-empty {joined}."
        )

    normalized = dict(profile)
    for key in required:
        normalized[key] = profile[key].strip()

    server = normalized["server"].rstrip("/")
    parsed_server = urlsplit(server)
    if parsed_server.scheme not in {"http", "https"} or not parsed_server.netloc:
        raise ValueError(
            f"Grist profile {profile_name!r} server must be an absolute HTTP(S) URL."
        )
    normalized["server"] = server
    return normalized
