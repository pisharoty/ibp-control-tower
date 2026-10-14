#!/usr/bin/env python3
"""Commodity Location Sentinel: Pinpoints direct yfinance calls and price dicts in main.py."""

import re
from pathlib import Path

main_src = Path("main.py").read_text()

print("==================================================")
print("🔍 AUDITING COMMODITY LOCATION IN MAIN.PY")
print("==================================================\n")

# 1. Search for yfinance or HTTP ticker fetches
yf_matches = [
    (i + 1, line.strip())
    for i, line in enumerate(main_src.splitlines())
    if re.search(r"\b(yfinance|yf\.|Ticker|download)\b", line, re.IGNORECASE)
]

print(f"--- 1. Direct Ticker / YFinance Calls in main.py ({len(yf_matches)} found) ---")
for line_num, code in yf_matches:
    print(f"  Line {line_num}: {code}")

if not yf_matches:
    print("  ✅ No direct yfinance network calls found in main.py.")

# 2. Search for hardcoded commodity price dictionaries or st.metric assignments
comm_matches = [
    (i + 1, line.strip())
    for i, line in enumerate(main_src.splitlines())
    if re.search(r"\b(copper|aluminum|brent|crude|resin|polyethylene)\b", line, re.IGNORECASE)
    and ("=" in line or ":" in line or "st.metric" in line)
]

print(f"\n--- 2. Inline Commodity Definitions in main.py ({len(comm_matches)} found) ---")
for line_num, code in comm_matches[:15]:  # Display top 15 lines
    print(f"  Line {line_num}: {code}")

