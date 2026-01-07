import json
import os
from typing import Dict, Any


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
