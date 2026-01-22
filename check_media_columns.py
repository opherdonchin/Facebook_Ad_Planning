#!/usr/bin/env python3
"""Check actual column names in media table."""

from src.grist import GristClient
import json

c = GristClient("c5dzrhUn5QHF", "eaa7ac30d29bd1a81816e6c5cf365b31428ee574")

media = c.fetch_records("Derived_Component_Media_Lifetime", flat=True)
print("Media table first row:")
print(json.dumps(media[0], indent=2))
