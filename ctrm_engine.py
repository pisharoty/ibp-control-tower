import math
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Any
from scipy.stats import norm


# =====================================================================
# 1. ENUMS & DATA STRUCTURES
# =====================================================================

class RiskEventType(Enum):
    STANDARD_VOLATILITY = "Standard_Price_Volatility"
    CLIMATE_SHOCK_EL_NINO = "Climate_Shock_El_Nino"
    CROP_YIELD_DEFICIT = "Geospatial_Crop_Yield_Deficit"


class ModelType(Enum):
    MODEL_ALPHA_BLACK76 = "Model_Alpha_Black76"
    MODEL_BETA_HAWKES = "Model_Beta_Hawkes_Jump_Diffusion"
    MODEL_GAMMA_PARAMETRIC = "Model_Gamma_Geospatial_Parametric"


@dataclass
class DSSolverOutput:
    """Output ingested directly from the existing D/S Match Solver."""
    scenario_name: str
    commodity_name: str
    incremental_gross_profit: float  # e.g., $7,137,631
    flex_capacity_cost: float        # e.g., $930,194
    volume_shortfall_units: float    # Required raw material tonnage/bushels
    baseline_price: float            # Agreed baseline $/unit
    spot_price: float                # Current market spot $/unit
    implied_volatility: float        # Annualized market volatility
    risk_event_type: RiskEventType
    network_throughput_ratio: float  # \theta \in [0, 1] (1 = Full flow, < 1 = Choked)


@dataclass
class HedgeOrder:
    """Structured CTRM ticket generated for desk execution."""
    order_id: str
    scenario_name: str
    commodity_name: str
    selected_model: ModelType
    notional_volume: float
    strike_price: float
    estimated_premium: float
    status: str  # "STAGED", "APPROVED_BY_DESK", "EXECUTED"


# =====================================================================
# 2. THE ADDITIONAL CTRM EXTENSION ENGINE
# =====================================================================

class CTRMExtensionEngine:
    def __init__(self, risk_free_rate: float = 0.045):
        self.r = risk_free_rate  # 4.5% Risk-free rate

    # -----------------------------------------------------------------
    # STEP 1: Physical-to-Financial Arbitrage Detector
    # -----------------------------------------------------------------
    def detect_arbitrage_risk(self, ds_output: DSSolverOutput) -> Dict[str, Any]:
        """Calculates unhedged margin risk and evaluates if hedging is required."""
        unhedged_margin_risk = ds_output.volume_shortfall_units * max(0.0, ds_output.spot_price - ds_output.baseline_price)
        profit_at_risk_pct = (unhedged_margin_risk / ds_output.incremental_gross_profit) * 100.0 if ds_output.incremental_gross_profit > 0 else 0.0
        
        return {
            "unhedged_margin_risk_usd": round(unhedged_margin_risk, 2),
            "profit_at_risk_pct": round(profit_at_risk_pct, 2),
            "requires_hedge_activation": unhedged_margin_risk > 0 or ds_output.network_throughput_ratio < 1.0
        }

    # -----------------------------------------------------------------
    # STEP 2: Disguised Pricing Engines & Model Selector
    # -----------------------------------------------------------------
    def _price_model_alpha_black76(self, F: float, K: float, T: float, sigma: float, volume: float) -> float:
        """Model Alpha: Standard Black-76 European Call Option."""
        if T <= 0 or sigma <= 0:
            return max(0.0, F - K) * volume
            
        d1 = (math.log(F / K) + (0.5 * (sigma ** 2)) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        call_per_unit = math.exp(-self.r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
        return call_per_unit * volume

    def _price_model_beta_hawkes(self, F: float, K: float, T: float, sigma: float, volume: float, theta: float) -> float:
        """Model Beta: Hawkes Jump-Diffusion Engine accounting for network bottlenecks."""
        base_premium = self._price_model_alpha_black76(F, K, T, sigma, volume)
        # Self-exciting intensity factor based on throughput choke (1 - theta)
        hawkes_multiplier = 1.0 + 1.75 * ((1.0 - theta) ** 2)
        return base_premium * hawkes_multiplier

    def _price_model_gamma_parametric(self, F: float, K: float, T: float, volume: float, theta: float) -> float:
        """Model Gamma: Parametric Earth-Sensing / Weather Index Contract."""
        base_exposure = (1.0 - theta) * F * volume
        parametric_spread_rate = 0.125  # Fixed parametric index rate
        return base_exposure * parametric_spread_rate

    def select_model_and_structure_hedge(self, ds_output: DSSolverOutput) -> HedgeOrder:
        """Selects appropriate disguised model and structures the CTRM order ticket."""
        F = ds_output.spot_price
        K = ds_output.baseline_price * 1.03  # Caps purchase price at 3% above baseline
        T = 0.25  # 3-month option duration
        vol = ds_output.volume_shortfall_units

        # Model Routing Logic
        if ds_output.risk_event_type == RiskEventType.STANDARD_VOLATILITY:
            model = ModelType.MODEL_ALPHA_BLACK76
            premium = self._price_model_alpha_black76(F, K, T, ds_output.implied_volatility, vol)

        elif ds_output.risk_event_type == RiskEventType.CLIMATE_SHOCK_EL_NINO:
            model = ModelType.MODEL_BETA_HAWKES
            premium = self._price_model_beta_hawkes(F, K, T, ds_output.implied_volatility, vol, ds_output.network_throughput_ratio)

        else:
            model = ModelType.MODEL_GAMMA_PARAMETRIC
            premium = self._price_model_gamma_parametric(F, K, T, vol, ds_output.network_throughput_ratio)

        return HedgeOrder(
            order_id="ORD-CTRM-2026-8831",
            scenario_name=ds_output.scenario_name,
            commodity_name=ds_output.commodity_name,
            selected_model=model,
            notional_volume=vol,
            strike_price=round(K, 2),
            estimated_premium=round(premium, 2),
            status="STAGED"
        )

    # -----------------------------------------------------------------
    # STEP 3: Operational Hand-off & Desk Governance
    # -----------------------------------------------------------------
    def approve_hedge_order(self, order: HedgeOrder) -> HedgeOrder:
        """Simulates CTRM Risk Desk approval."""
        order.status = "APPROVED_BY_DESK"
        return order

    # -----------------------------------------------------------------
    # STEP 4: Market Execution & Closed-Loop Financial Return
    # -----------------------------------------------------------------
    def execute_and_close_loop(self, ds_output: DSSolverOutput, order: HedgeOrder, market_price_at_expiry: float) -> Dict[str, Any]:
        """Executes trade, calculates financial payouts, and returns closed-loop metrics."""
        order.status = "EXECUTED"

        # Calculate Derivative Payout at Expiry
        payoff_per_unit = max(0.0, market_price_at_expiry - order.strike_price)

        # Apply network severity scaling if Model Beta was selected
        if order.selected_model == ModelType.MODEL_BETA_HAWKES:
            payoff_per_unit *= (1.0 + 0.60 * (1.0 - ds_output.network_throughput_ratio))

        total_hedge_payout = payoff_per_unit * order.notional_volume

        # Closed-Loop Formula: Net Realized Profit
        net_realized_profit = (
            ds_output.incremental_gross_profit 
            - ds_output.flex_capacity_cost 
            - order.estimated_premium 
            + total_hedge_payout
        )

        return {
            "scenario": ds_output.scenario_name,
            "ctrm_order_id": order.order_id,
            "order_status": order.status,
            "model_executed": order.selected_model.value,
            "financial_waterfall": {
                "incremental_gross_profit_usd": ds_output.incremental_gross_profit,
                "flex_capacity_cost_usd": ds_output.flex_capacity_cost,
                "hedge_premium_paid_usd": order.estimated_premium,
                "hedge_payout_received_usd": round(total_hedge_payout, 2),
                "net_realized_profit_usd": round(net_realized_profit, 2)
            },
            "margin_protected": total_hedge_payout > order.estimated_premium
        }


# =====================================================================
# 3. END-TO-END WORKFLOW SIMULATION
# =====================================================================

if __name__ == "__main__":
    # Ingesting output from your D/S Match Solver (El Niño scenario on Sugar/Coffee inputs)
    ds_run = DSSolverOutput(
        scenario_name="Walmart Upside - El Niño Risk",
        commodity_name="Raw Sugar / Sweetener",
        incremental_gross_profit=7137631.0,  # $7.1M Gross Profit
        flex_capacity_cost=930194.0,         # $930K Flex Capacity Cost
        volume_shortfall_units=120000.0,     # 120,000 cwt
        baseline_price=22.50,                # $22.50 / cwt
        spot_price=28.40,                    # $28.40 / cwt (Spike due to El Niño)
        implied_volatility=0.32,             # 32% Volatility
        risk_event_type=RiskEventType.CLIMATE_SHOCK_EL_NINO,
        network_throughput_ratio=0.70        # 30% Physical Network Capacity Bottleneck
    )

    ctrm_bridge = CTRMExtensionEngine()

    print("--- STEP 1: PHYSICAL-TO-FINANCIAL ARBITRAGE DETECTION ---")
    arbitrage_status = ctrm_bridge.detect_arbitrage_risk(ds_run)
    print(f"Unhedged Risk: ${arbitrage_status['unhedged_margin_risk_usd']:,.2f}")
    print(f"Profit at Risk: {arbitrage_status['profit_at_risk_pct']}%")

    print("\n--- STEP 2: MODEL SELECTION & HEDGE STRUCTURING ---")
    staged_ticket = ctrm_bridge.select_model_and_structure_hedge(ds_run)
    print(f"Selected Model: {staged_ticket.selected_model.value}")
    print(f"Notional Volume: {staged_ticket.notional_volume:,.0f} units")
    print(f"Strike Ceiling Price: ${staged_ticket.strike_price}/unit")
    print(f"Calculated Premium: ${staged_ticket.estimated_premium:,.2f}")
    print(f"Ticket Status: {staged_ticket.status}")

    print("\n--- STEP 3: OPERATIONAL HAND-OFF & DESK APPROVAL ---")
    approved_ticket = ctrm_bridge.approve_hedge_order(staged_ticket)
    print(f"Ticket {approved_ticket.order_id} Status Updated to: {approved_ticket.status}")

    print("\n--- STEP 4: MARKET EXECUTION & CLOSED-LOOP RETURN ---")
    # Simulate market price at option expiry spiking to $32.00 due to severe weather
    final_sop_results = ctrm_bridge.execute_and_close_loop(ds_run, approved_ticket, market_price_at_expiry=32.00)
    
    import json
    print(json.dumps(final_sop_results, indent=2))

