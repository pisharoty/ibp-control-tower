import uvicorn
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
from scipy.optimize import linprog

app = FastAPI(
    title="Digital Brain — Enterprise IBP Orchestration API",
    description="Full-stack IBP Backend Engine",
    version="2.0.0"
)

@app.get("/")
def health_check():
    return {"status": "ONLINE", "system": "IBP Enterprise Engine v2.0"}

class DSSolverInput(BaseModel):
    scenario_id: str = "SCENARIO_2026_01"
    scenario_version: str = "Base S&OP Plan"
    demand_units: float = Field(100000.0, ge=0)
    base_list_price: float = Field(50.0, ge=0)
    trade_spend_pct: float = Field(0.12, ge=0, le=1.0)
    plant_capacities: List[float] = [40000.0, 45000.0]
    mfg_unit_costs: List[float] = [12.0, 14.0]
    logistics_unit_costs: List[float] = [2.5, 3.0]
    expedite_premium_unit: float = Field(10.0, ge=0)

@app.post("/api/v1/ibp/scenarios/run-ds-solver")
def run_ds_solver(payload: DSSolverInput):
    gross_revenue = payload.demand_units * payload.base_list_price
    trade_spend = gross_revenue * payload.trade_spend_pct
    net_revenue = gross_revenue - trade_spend
    
    cap_a, cap_b = payload.plant_capacities[0], payload.plant_capacities[1]
    cost_a = payload.mfg_unit_costs[0] + payload.logistics_unit_costs[0]
    cost_b = payload.mfg_unit_costs[1] + payload.logistics_unit_costs[1]
    cost_exp = cost_a + payload.expedite_premium_unit
    
    c = [cost_a, cost_b, cost_exp]
    A_eq = [[1, 1, 1]]
    b_eq = [payload.demand_units]
    bounds = [(0, cap_a), (0, cap_b), (0, None)]
    
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    if not res.success:
        raise HTTPException(status_code=400, detail="Solver failed to find feasible allocation.")
        
    q_a, q_b, q_exp = res.x[0], res.x[1], res.x[2]
    total_cost = res.fun
    net_margin = net_revenue - total_cost
    
    return {
        "scenario_id": payload.scenario_id,
        "solver_status": "Optimal",
        "allocation": {
            "plant_a_std_units": round(q_a, 2),
            "plant_b_std_units": round(q_b, 2),
            "expedited_units": round(q_exp, 2)
        },
        "waterfall": {
            "gross_revenue": round(gross_revenue, 2),
            "trade_spend": round(trade_spend, 2),
            "net_revenue": round(net_revenue, 2),
            "total_cogs_logistics": round(total_cost, 2),
            "net_margin": round(net_margin, 2)
        }
    }

class NPIInput(BaseModel):
    new_product_name: str = "Cosmo Cola Zero Sugar"
    launch_quarter: str = "Q3 2026"
    target_launch_units: float = 30000.0
    like_item_baseline_units: float = 25000.0
    estimated_cannibalization_pct: float = 0.20
    base_price: float = 4.50

@app.post("/api/v1/ibp/npi/cannibalization-analysis")
def analyze_npi_launch(payload: NPIInput):
    gross_new_revenue = payload.target_launch_units * payload.base_price
    cannibalized_units = payload.target_launch_units * payload.estimated_cannibalization_pct
    cannibalized_revenue = cannibalized_units * payload.base_price
    net_incremental_units = payload.target_launch_units - cannibalized_units
    net_incremental_revenue = gross_new_revenue - cannibalized_revenue
    
    return {
        "new_product_name": payload.new_product_name,
        "stage_gate_status": "Stage 3: Pilot Run & Tooling",
        "gross_launch_units": payload.target_launch_units,
        "cannibalized_legacy_units": cannibalized_units,
        "net_incremental_units": net_incremental_units,
        "financial_impact": {
            "gross_new_revenue": gross_new_revenue,
            "cannibalized_revenue_loss": cannibalized_revenue,
            "net_incremental_revenue": net_incremental_revenue
        }
    }

class NLPParseInput(BaseModel):
    raw_text: str

@app.post("/api/v1/ibp/nlp/parse-intelligence")
def parse_nlp_intelligence(payload: NLPParseInput):
    text_lower = payload.raw_text.lower()
    
    # Dynamic Retailer Recognition
    retailers = ["costco", "walmart", "target", "kroger", "amazon", "albertsons", "sam's club"]
    customer = "Key Customer"
    for r in retailers:
        if r in text_lower:
            customer = r.title()
            break
            
    # Dynamic Number Extraction (e.g. 50,000 or 50000)
    numbers = re.findall(r'\b\d{1,3}(?:,\d{3})+|\b\d+\b', payload.raw_text)
    quantity = int(numbers[0].replace(',', '')) if numbers else 10000
    
    # Dynamic Product Recognition
    if "teed off" in text_lower or "energy" in text_lower:
        product = "Teed Off Energy Drink"
    elif "cola" in text_lower:
        product = "Cosmo Cola 20oz"
    else:
        product = "Core Beverage SKU"
        
    return {
        "parsed_entities": {
            "customer": customer,
            "product_family": product,
            "incremental_volume_cases": quantity,
            "timeframe": "Promotional Surge Window"
        },
        "auto_generated_pulse_tag": f"COMMERCIAL_DEMAND_SURGE_{customer.upper().replace(' ', '_')}",
        "routed_target_planner_role": f"Demand Planner - {customer} Retail Account"
    }

@app.get("/api/v1/ibp/geospatial/nodes")
def get_geospatial_nodes():
    return [
        {"name": "Plant A (Atlanta)", "type": "Plant", "lat": 33.7490, "lon": -84.3880, "status": "Normal", "capacity_util": "88%", "otif_risk": "Low"},
        {"name": "Plant B (Chicago)", "type": "Plant", "lat": 41.8781, "lon": -87.6298, "status": "High Utilization", "capacity_util": "96%", "otif_risk": "Medium"},
        {"name": "East Coast DC (NJ)", "type": "DC", "lat": 40.0583, "lon": -74.4057, "status": "Normal", "stockout_risk": "5%", "otif_risk": "Low"},
        {"name": "West Coast DC (LA)", "type": "DC", "lat": 34.0522, "lon": -118.2437, "status": "Stockout Risk", "stockout_risk": "34%", "otif_risk": "High"},
        {"name": "Dallas Hub", "type": "Retail Retailer Node", "lat": 32.7767, "lon": -96.7970, "status": "Normal", "stockout_risk": "2%", "otif_risk": "Low"}
    ]

@app.get("/api/v1/ibp/ekg/graph")
def get_ekg_graph():
    return {
        "nodes": [
            {"id": "Market_Intel", "group": "Market Knowledge", "label": "Competitor Launch Delay"},
            {"id": "Customer_Target", "group": "Demand Knowledge", "label": "Target Stores Promo"},
            {"id": "SKU_CosmoCola", "group": "Demand Knowledge", "label": "Cosmo Cola 20oz"},
            {"id": "Plant_Atlanta", "group": "Supply Knowledge", "label": "Atlanta Mfg Plant"},
            {"id": "Supplier_SugarCo", "group": "Supply Knowledge", "label": "SugarCo Ingredient Supplier"},
            {"id": "PL_GrossRev", "group": "Revenue / Finance", "label": "Gross Revenue Target ($5M)"},
            {"id": "PL_NetMargin", "group": "Revenue / Finance", "label": "Net Margin ($2.68M)"}
        ],
        "edges": [
            {"source": "Market_Intel", "target": "Customer_Target", "relation": "Drives Demand Surge"},
            {"source": "Customer_Target", "target": "SKU_CosmoCola", "relation": "Requests Volume"},
            {"source": "SKU_CosmoCola", "target": "Plant_Atlanta", "relation": "Allocated Production"},
            {"source": "Plant_Atlanta", "target": "Supplier_SugarCo", "relation": "Requires Raw Materials"},
            {"source": "SKU_CosmoCola", "target": "PL_GrossRev", "relation": "Generates Sales"},
            {"source": "Plant_Atlanta", "target": "PL_NetMargin", "relation": "Incurs Production Cost"}
        ]
    }

@app.post("/api/v1/ibp/ingestion/sync-all")
def sync_enterprise_data():
    return {
        "status": "Success",
        "sync_timestamp": "2026-07-30T08:45:00Z",
        "ingestion_summary": [
            {"source": "SAP S/4HANA (ERP)", "records_ingested": 14200, "latency_ms": 120, "status": "HEALTHY"},
            {"source": "Salesforce (CRM)", "records_ingested": 3400, "latency_ms": 85, "status": "HEALTHY"},
            {"source": "FourKites (Logistics)", "records_ingested": 890, "latency_ms": 210, "status": "HEALTHY"},
            {"source": "Coupa (Procurement)", "records_ingested": 1250, "latency_ms": 95, "status": "HEALTHY"}
        ]
    }

class GapCInput(BaseModel):
    period_id: str = "FY2027_Q1"
    long_range_target_revenue: float
    aop_budget_revenue: float
    stat_baseline_forecast_revenue: float
    constrained_ibp_forecast_revenue: float

@app.post("/api/v1/ibp/strategy/aop-gap-analysis")
def calculate_aop_gaps(payload: GapCInput):
    strategic_gap = payload.long_range_target_revenue - payload.constrained_ibp_forecast_revenue
    aop_execution_gap = payload.aop_budget_revenue - payload.constrained_ibp_forecast_revenue
    unconstrained_risk = payload.stat_baseline_forecast_revenue - payload.constrained_ibp_forecast_revenue
    
    return {
        "period_id": payload.period_id,
        "strategic_gap": strategic_gap,
        "aop_execution_gap": aop_execution_gap,
        "unconstrained_to_constrained_risk": unconstrained_risk
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
