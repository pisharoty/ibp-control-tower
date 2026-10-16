import json
import os
import streamlit as st
from inventory_manager import TOP_50_COMMODITIES_REGISTRY

ROBOT_SIGNALS_FILE = "robot_signals.json"

def get_merged_market_signals():
    """Option B Hybrid Pipeline:
    - Maintains full coverage for all 50 registry commodities.
    - Superimposes active Genspark tactical news signals when present.
    """
    merged_signals = {}

    # Step 1: Default all 50 commodities to neutral baseline
    for commodity_name, details in TOP_50_COMMODITIES_REGISTRY.items():
        merged_signals[commodity_name] = {
            "commodity": commodity_name,
            "category": details["category"],
            "si_composite": 0.00,
            "sentiment_label": "Neutral / Stable",
            "demand_surge_flag": False,
            "supply_disruption_flag": False,
            "headline_summary": "No active tactical disruptions reported in last Genspark scan.",
            "top_source_url": "",
            "source": "Baseline Engine"
        }

    # Step 2: Superimpose active Genspark tactical signals
    if os.path.exists(ROBOT_SIGNALS_FILE):
        try:
            with open(ROBOT_SIGNALS_FILE, "r") as f:
                data = json.load(f)

            signals_list = data if isinstance(data, list) else data.get("signals", [])

            for item in signals_list:
                name = item.get("commodity")
                if name in merged_signals:
                    merged_signals[name].update({
                        "si_composite": float(item.get("si_composite", 0.0)),
                        "sentiment_label": item.get("sentiment_label", "Active Event"),
                        "demand_surge_flag": bool(item.get("demand_surge_flag", False)),
                        "supply_disruption_flag": bool(item.get("supply_disruption_flag", False)),
                        "headline_summary": item.get("headline_summary", ""),
                        "top_source_url": item.get("top_source_url", ""),
                        "source": "📡 Genspark Agent"
                    })
        except Exception as e:
            st.warning(f"Could not parse Genspark signals overlay: {e}")

    return merged_signals
