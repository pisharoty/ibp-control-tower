import requests
import json
import sys

API_BASE = "http://127.0.0.1:8000"

tests = [
    ("1. Data Ingestion Sync", "POST", "/api/v1/ibp/ingestion/sync-all", None),
    ("2. D/S Match & Net Margin Solver", "POST", "/api/v1/ibp/scenarios/run-ds-solver", {
        "demand_units": 150000,
        "base_list_price": 50.0,
        "trade_spend_pct": 0.12,
        "plant_capacities": [40000, 45000],
        "mfg_unit_costs": [12.0, 14.0],
        "logistics_unit_costs": [2.5, 3.0],
        "expedite_premium_unit": 10.0
    }),
    ("3. NPI Cannibalization Analysis", "POST", "/api/v1/ibp/npi/cannibalization-analysis", {
        "new_product_name": "Teed Off Energy Drink Zero",
        "target_launch_units": 50000,
        "estimated_cannibalization_pct": 0.20,
        "base_price": 4.50
    }),
    ("4. Commercial Sensing NLP", "POST", "/api/v1/ibp/nlp/parse-intelligence", {
        "raw_text": "Costco wants 50,000 extra cases of Teed off energy drink for a promo"
    }),
    ("5. GIS Control Tower Nodes", "GET", "/api/v1/ibp/geospatial/nodes", None),
    ("6. Enterprise Knowledge Graph", "GET", "/api/v1/ibp/ekg/graph", None),
    ("7. Strategy & AOP Gap Analysis", "POST", "/api/v1/ibp/strategy/aop-gap-analysis", {
        "period_id": "FY2027_Q1",
        "long_range_target_revenue": 10000000.0,
        "aop_budget_revenue": 8500000.0,
        "stat_baseline_forecast_revenue": 7500000.0,
        "constrained_ibp_forecast_revenue": 6600000.0
    })
]

print("\nRunning Sequential Integration Test Suite...\n" + "="*60)

passed = 0
failed = 0

for name, method, endpoint, payload in tests:
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            res = requests.get(url)
        else:
            res = requests.post(url, json=payload)
            
        if res.status_code == 200:
            print(f"  PASS | {name} [{res.status_code}]")
            passed += 1
        else:
            print(f"  FAIL | {name} [{res.status_code}] -> {res.text}")
            failed += 1
    except Exception as e:
        print(f" ERROR | {name} -> Could not connect to FastAPI server ({e})")
        failed += 1

print("="*60)
print(f"Test Summary: {passed} Passed, {failed} Failed out of {len(tests)} tests.\n")

if failed > 0:
    sys.exit(1)
