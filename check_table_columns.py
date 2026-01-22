#!/usr/bin/env python3
"""Check available columns in component tables."""

from src.grist import GristClient
import json

c = GristClient("c5dzrhUn5QHF", "eaa7ac30d29bd1a81816e6c5cf365b31428ee574")

print("TEXTS table sample:")
texts = c.fetch_records("Texts", flat=True)
if texts:
    print(json.dumps(texts[0], indent=2))

print("\n" + "=" * 80)
print("HEADLINES table sample:")
headlines = c.fetch_records("Headlines", flat=True)
if headlines:
    print(json.dumps(headlines[0], indent=2))

print("\n" + "=" * 80)
print("MEDIA table sample:")
media = c.fetch_records("Media", flat=True)
if media:
    print(json.dumps(media[0], indent=2))
