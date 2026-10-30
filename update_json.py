import json

# Load existing robot_signals.json if present
try:
    with open("robot_signals.json", "r") as f:
        data = json.load(f)
except Exception:
    data = {"signals": []}

debriefs = [
    {
        "id": "deb_ag_01", "sector": "Agriculture & Biofuels", "source": "Global Agri Trade Wire",
        "author": "VP Sourcing @ Archer Daniels Midland (ADM)", "commodity": "Arabica Coffee & Softs",
        "title": "ADM Ag Debrief: Minas Gerais Polar Frost Wipes 25% of Arabica Coffee Crop",
        "headline": "ADM Ag Debrief: Minas Gerais Polar Frost Wipes 25% of Arabica Coffee Crop",
        "content": "Severe frost damage across key Brazilian growing belts drives ICE Arabica futures +40% with multi-year supply deficits.",
        "sentiment_score": -0.72, "impact_demand": 32000, "impact_leadtime": 4.5
    },
    {
        "id": "deb_ag_02", "sector": "Agriculture & Biofuels", "source": "Softs Market Intelligence",
        "author": "Director of Supply Chain @ Cargill", "commodity": "CBOT Milling Wheat",
        "title": "Cargill Commodity Update: Black Sea Grain Corridor Restrictions Tighten Milling Wheat",
        "headline": "Cargill Commodity Update: Black Sea Grain Corridor Restrictions Tighten Milling Wheat",
        "content": "Port infrastructure constraints and insurance surcharges restrict Ukrainian grain shipments to North Africa.",
        "sentiment_score": -0.48, "impact_demand": 24000, "impact_leadtime": 3.8
    },
    {
        "id": "deb_chem_01", "sector": "Fertilizers & Industrial Chemicals", "source": "Chemical Sourcing Dispatch",
        "author": "Global Procurement Lead @ Nutrien", "commodity": "Potassium Chloride & Acid",
        "title": "Nutrien Executive Brief: European Gas Volatility Constrains Ammonia & Acid Synthesis",
        "headline": "Nutrien Executive Brief: European Gas Volatility Constrains Ammonia & Acid Synthesis",
        "content": "Natural gas feedstock spikes force European fertilizer plants to cut operating rates, driving import demand for US Gulf MOP.",
        "sentiment_score": -0.40, "impact_demand": 18500, "impact_leadtime": 3.0
    },
    {
        "id": "deb_frt_01", "sector": "Global Freight & Maritime Logistics", "source": "Ocean Carrier Network Advisory",
        "author": "Chief Operating Officer @ Maersk Line", "commodity": "Ocean Freight (FBX)",
        "title": "Maersk Fleet Advisory: Panama Canal Draft Restrictions Extended Through Q4",
        "headline": "Maersk Fleet Advisory: Panama Canal Draft Restrictions Extended Through Q4",
        "content": "Daily vessel transits remain capped at 24 slots, forcing neo-Panamax container ships to pay record auction premiums.", 
        "sentiment_score": -0.58, "impact_demand": 26000, "impact_leadtime": 6.2
    }
]

data["email_debriefs"] = debriefs
data["executive_social_stream"] = debriefs
data["field_intelligence"] = debriefs

with open("robot_signals.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ Updated robot_signals.json successfully.")
