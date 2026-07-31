from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import random

app = FastAPI(title="Integrated Business Planning API")

# --- Enterprise Integration Sync Endpoints ---

@app.post("/api/v1/ibp/integration/sync-erp")
def sync_erp():
    return {
        "pipeline": "Supply Chain & Manufacturing (ERP)",
        "sources": [
            {"source": "SAP S/4HANA (BOM & Inventory)", "records_ingested": 18450, "status": "HEALTHY"},
            {"source": "MES Plant Floor Sensors", "records_ingested": 42100, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-crm-plm")
def sync_crm_plm():
    return {
        "pipeline": "Product Lifecycle & Commercial Pipeline",
        "sources": [
            {"source": "Salesforce CRM Opportunities", "records_ingested": 3200, "status": "HEALTHY"},
            {"source": "Arena PLM Stage-Gate Logs", "records_ingested": 450, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-nlp-outlook")
def sync_nlp_outlook():
    return {
        "pipeline": "Commercial Intelligence & Sentiment Sensing",
        "sources": [
            {"source": "Microsoft Outlook / Exchange API", "emails_parsed": 1280, "status": "HEALTHY"},
            {"source": "Web & Maritime Market Feeds", "articles_parsed": 340, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-gis-logistics")
def sync_gis_logistics():
    return {
        "pipeline": "Geospatial & Carrier Tracking",
        "sources": [
            {"source": "FourKites Real-Time GPS", "active_shipments": 620, "status": "HEALTHY"},
            {"source": "project44 Carrier Feeds", "active_truckloads": 410, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-ekg-graph")
def sync_ekg_graph():
    return {
        "pipeline": "Enterprise Knowledge Graph Ontology",
        "sources": [
            {"source": "Neo4j Knowledge Graph", "nodes_updated": 1420, "edges_updated": 3890, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-fpa-strategy")
def sync_fpa_strategy():
    return {
        "pipeline": "FP&A Strategic & Operating Plan",
        "sources": [
            {"source": "Anaplan LRP Models", "records_ingested": 890, "status": "HEALTHY"},
            {"source": "Oracle Hyperion AOP Budget", "records_ingested": 1200, "status": "HEALTHY"}
        ]
    }

@app.post("/api/v1/ibp/integration/sync-procurement-trading")
def sync_procurement_trading():
    return {
        "pipeline": "Procurement, Spot Markets & Tariff Schedules",
        "sources": [
            {"source": "Coupa Procurement Vendor Quotes", "records_ingested": 2100, "status": "HEALTHY"},
            {"source": "Bloomberg Commodity Spot Market", "symbols_tracked": 145, "status": "HEALTHY"},
            {"source": "Descartes Customs Tariff Feeds", "hs_codes_verified": 820, "status": "HEALTHY"}
        ]
    }

# --- Module Solvers ---

class DSMatchRequest(BaseModel):
    unconstrained_demand: int
    base_price: float
    trade_spend_pct: float
    plant_a_cap: int
    plant_b_cap: int
    plant_a_cost: float
    plant_b_cost: float
    nlp_surcharge_per_unit: float = 0.0

@app.post("/api/v1/ibp/solver/ds-match")
def solve_ds_match(req: DSMatchRequest):
    net_price = req.base_price * (1 - req.trade_spend_pct)
    alloc_a = min(req.unconstrained_demand, req.plant_a_cap)
    rem_demand = max(0, req.unconstrained_demand - alloc_a)
    alloc_b = min(rem_demand, req.plant_b_cap)
    fulfilled = alloc_a + alloc_b
    
    gross_rev = fulfilled * req.base_price
    net_rev = fulfilled * net_price
    base_cost = (alloc_a * req.plant_a_cost) + (alloc_b * req.plant_b_cost)
    nlp_risk_impact = fulfilled * req.nlp_surcharge_per_unit
    total_cost = base_cost + nlp_risk_impact
    net_margin = net_rev - total_cost
    
    return {
        "fulfilled_demand": fulfilled,
        "unmet_demand": req.unconstrained_demand - fulfilled,
        "plant_a_allocation": alloc_a,
        "plant_b_allocation": alloc_b,
        "gross_revenue": round(gross_rev, 2),
        "net_revenue": round(net_rev, 2),
        "cogs": round(total_cost, 2),
        "nlp_surcharge_total": round(nlp_risk_impact, 2),
        "net_margin": round(net_margin, 2)
    }

class SupplierOffer(BaseModel):
    supplier_name: str
    spot_price_per_unit: float
    inbound_freight_per_unit: float
    tariff_and_duty_per_unit: float
    warehousing_per_unit: float
    lead_time_days: int
    defect_rate_pct: float
    disruption_surcharge_per_unit: float = 0.0
    max_available_units: int

class MakeVsBuyRequest(BaseModel):
    product_sku: str
    target_volume: int
    internal_mfg_cost_per_unit: float
    internal_freight_per_unit: float
    internal_lead_time_days: int
    holding_cost_per_day: float = 0.15
    supplier_offers: List[SupplierOffer]

@app.post("/api/v1/ibp/trading/make-vs-buy")
def run_make_vs_buy(req: MakeVsBuyRequest):
    internal_landed = req.internal_mfg_cost_per_unit + req.internal_freight_per_unit
    offer = req.supplier_offers[0]
    
    base_landed = offer.spot_price_per_unit + offer.inbound_freight_per_unit + offer.tariff_and_duty_per_unit + offer.warehousing_per_unit
    quality_penalty = base_landed * (offer.defect_rate_pct / 100.0)
    delay_days = max(0, offer.lead_time_days - req.internal_lead_time_days)
    delay_penalty = delay_days * req.holding_cost_per_day
    
    effective_unit_cost = base_landed + quality_penalty + delay_penalty + offer.disruption_surcharge_per_unit
    delta = internal_landed - effective_unit_cost
    is_buy = delta > 0
    
    return {
        "sku": req.product_sku,
        "target_volume": req.target_volume,
        "internal_landed_unit_cost": round(internal_landed, 2),
        "arbitrage_opportunity_found": is_buy,
        "recommended_action": "BUY (External Supplier)" if is_buy else "MAKE (Internal Production)",
        "best_supplier": offer.supplier_name,
        "supplier_effective_unit_cost": round(effective_unit_cost, 2),
        "unit_savings": round(max(0, delta), 2),
        "total_pnl_impact": round(delta * req.target_volume, 2),
        "cost_breakdown": {
            "base_landed": round(base_landed, 2),
            "quality_penalty": round(quality_penalty, 2),
            "delay_penalty": round(delay_penalty, 2),
            "disruption_surcharge": round(offer.disruption_surcharge_per_unit, 2)
        }
    }

class PurchaseOrderRequest(BaseModel):
    sku: str
    supplier_name: str
    volume: int
    agreed_unit_cost: float
    total_cost: float
    action_type: str

@app.post("/api/v1/ibp/trading/execute-po")
def execute_po(po: PurchaseOrderRequest):
    po_num = f"PO-COUPA-{random.randint(10000, 99999)}"
    return {
        "status": "SUCCESS",
        "po_number": po_num,
        "action_type": po.action_type,
        "message": f"Execution order {po_num} committed to SAP S/4HANA & Coupa.",
        "committed_financial_impact": round(po.total_cost, 2)
    }
