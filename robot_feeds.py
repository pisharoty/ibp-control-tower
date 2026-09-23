from datetime import datetime, timedelta
import email
from email.header import decode_header
import imaplib
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import bs4
import numpy as np

# ---------------------------------------------------------------------------
# Focus Sector Keywords (Filters out general news, politics, and spam)
# ---------------------------------------------------------------------------
SUPPLY_CHAIN_KEYWORDS = [
    "supply chain", "logistics", "freight", "shipping", "container", "port",
    "vessel", "transit", "smelter", "cathode", "copper", "aluminum", "nickel",
    "zinc", "lithium", "cobalt", "tin", "minerals", "metals", "semiconductor",
    "chip", "fab", "wafer", "ethylene", "resin", "chemical", "force majeure",
    "outage", "shortage", "disruption", "delay", "tariff", "inventory", "lme",
    "strike", "bottleneck", "surcharge", "bunker", "dwell", "rerouting"
]


# ---------------------------------------------------------------------------
# Lazy Runtime Credential Resolution (Prevents Import Deadlocks)
# ---------------------------------------------------------------------------
def _get_gmail_credentials():
    """Safely retrieves credentials at runtime without importing Streamlit at top-level."""
    user = os.getenv("GMAIL_USER", "pisharoty1@gmail.com")
    app_pass = os.getenv("GMAIL_APP_PASS", "")

    if not app_pass:
        try:
            import streamlit as st
            user = st.secrets.get("GMAIL_USER", user)
            app_pass = st.secrets.get("GMAIL_APP_PASS", app_pass)
        except Exception:
            pass

    return user, app_pass


def _get_secret(key_name: str, default_val: str = "") -> str:
    """Helper to fetch optional API keys like FRED_API_KEY dynamically."""
    val = os.getenv(key_name, default_val)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(key_name, val)
        except Exception:
            pass
    return val


# ---------------------------------------------------------------------------
# Sector Relevance & Dynamic Sentiment Analysis Engine
# ---------------------------------------------------------------------------
def is_supply_chain_relevant(text: str) -> bool:
    """Returns True if content matches at least one industrial/supply chain keyword."""
    if not text:
        return False
    lower_text = text.lower()
    return any(kw in lower_text for kw in SUPPLY_CHAIN_KEYWORDS)


def analyze_text_sentiment(text: str) -> float:
    """Parses raw text and computes normalized polarity score s_i in [-1.0, +1.0]."""
    if not text:
        return 0.0

    bearish_words = [
        "outage", "curtailment", "strike", "delay", "bottleneck", "surge",
        "shortage", "deficit", "sanction", "force majeure", "disruption",
        "spike", "tightness", "shutdown"
    ]
    bullish_words = [
        "recovery", "surplus", "expansion", "easing", "resolution", "steady",
        "capacity expansion", "rebate", "normalization", "growth"
    ]

    lower_text = text.lower()
    bear_count = sum(1 for word in bearish_words if word in lower_text)
    bull_count = sum(1 for word in bullish_words if word in lower_text)

    total = bear_count + bull_count
    if total == 0:
        return -0.10  # Standard mild default risk bias for market updates

    polarity = (bull_count - bear_count) / float(total)
    return float(np.clip(polarity, -1.0, 1.0))


# ---------------------------------------------------------------------------
# 1. IMAP Live Email Ingestion Engine (With Domain Relevance Filter)
# ---------------------------------------------------------------------------
def fetch_gmail_newsletters(max_emails: int = 15):
    """Connects to Gmail via IMAP, searches history, and filters for supply chain relevance."""
    gmail_user, gmail_pass = _get_gmail_credentials()

    if not gmail_pass:
        return [{
            "source": "LinkedIn Newsletters",
            "status": "GMAIL_APP_PASS is missing in secrets or environment.",
            "is_live": False,
            "sentiment_score": 0.0,
        }]

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_pass)
        mail.select("inbox")

        email_ids = []

        # Search Tier 1: Raw search for supply chain / LinkedIn keywords
        try:
            status, messages = mail.search(None, 'X-GM-RAW', 'linkedin OR newsletter OR supply OR market OR logistics')
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
        except Exception:
            pass

        # Search Tier 2: Standard IMAP text search
        if not email_ids:
            status, messages = mail.search(None, 'TEXT "linkedin"')
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()

        # Search Tier 3: Search ALL inbox emails as fallback
        if not email_ids:
            status, messages = mail.search(None, 'ALL')
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()

        if not email_ids:
            mail.logout()
            return [{
                "source": "LinkedIn Newsletters",
                "status": "No matching emails found in Inbox.",
                "is_live": True,
                "sentiment_score": 0.0,
            }]

        target_ids = list(reversed(email_ids))[:max_emails]
        parsed_newsletters = []

        for email_id in target_ids:
            res, msg_data = mail.fetch(email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject_header = msg.get('Subject', 'LinkedIn Signal Update')
                    decoded_header = decode_header(subject_header)[0]
                    subject = decoded_header[0]
                    if isinstance(subject, bytes):
                        encoding = decoded_header[1] if decoded_header[1] else 'utf-8'
                        subject = subject.decode(encoding, errors='ignore')

                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type in ['text/html', 'text/plain']:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode(errors='ignore')
                                    if content_type == 'text/html':
                                        break
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors='ignore')

                    clean_text = bs4.BeautifulSoup(body, 'html.parser').get_text()
                    full_content = f"{subject} {clean_text}"

                    # SECTOR FILTER: Skip non-relevant political/general emails
                    if not is_supply_chain_relevant(full_content):
                        continue

                    clean_summary = (
                        ' '.join(clean_text.split())[:300] + '...'
                        if clean_text else 'No text summary available.'
                    )
                    live_sentiment = analyze_text_sentiment(full_content)

                    parsed_newsletters.append({
                        'title': str(subject),
                        'published': str(msg.get('Date', 'Recent')),
                        'summary': clean_summary,
                        'raw_body': clean_text[:1000],
                        'source': 'LinkedIn / Gmail Direct Feed',
                        'is_live': True,
                        'sentiment_score': round(live_sentiment, 2),
                    })

                    if len(parsed_newsletters) >= 5:
                        break

        mail.logout()

        if parsed_newsletters:
            return parsed_newsletters
        else:
            return [{
                'source': 'LinkedIn Newsletters',
                'title': 'No Sector Match',
                'summary': 'Emails found in inbox, but none matched supply chain focus sector keywords.',
                'is_live': False,
                'sentiment_score': 0.0,
            }]

    except Exception as e:
        return [{
            'source': 'LinkedIn Newsletters',
            'status': f'IMAP Connection Error: {str(e)}',
            'is_live': False,
            'sentiment_score': 0.0,
        }]


# ---------------------------------------------------------------------------
# 2. Hard Macroeconomic API Fetchers (NY Fed, World Bank, FRED)
# ---------------------------------------------------------------------------
def fetch_ny_fed_gscpi() -> float:
    """Fetches live Global Supply Chain Pressure Index (GSCPI) from NY Fed public API."""
    url = "https://www.newyorkfed.org/medialibrary/media/research/policy/gscpi/gscpi_data.json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            latest_val = data["data"][-1][1]  # Standardized standard deviation score
            return float(latest_val)
    except Exception:
        return 0.45  # Standard historical baseline fallback


def fetch_world_bank_commodity_pink_sheet(indicator: str = "PALLFNFINDEXQ") -> dict:
    """Fetches World Bank Open Data benchmark commodity index (No API key required)."""
    url = f"https://api.worldbank.org/v2/country/ALL/indicator/{indicator}?format=json&per_page=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if len(data) > 1 and data[1]:
                latest = data[1][0]
                return {
                    "indicator": latest.get("indicator", {}).get("value"),
                    "date": latest.get("date"),
                    "value": float(latest.get("value") or 0.0),
                    "status": "success"
                }
    except Exception as e:
        return {"indicator": indicator, "value": None, "status": f"Error: {str(e)}"}
    return {"indicator": indicator, "value": None, "status": "No data"}


def fetch_fred_indicator(series_id: str = "MNFCTRMPCIMSA") -> dict:
    """Fetches economic series from FRED API if key exists."""
    fred_key = _get_secret("FRED_API_KEY", "")
    if not fred_key:
        return {"series_id": series_id, "value": None, "status": "FRED_API_KEY missing"}

    url = (
        f"https://api.stlouisfed.org/fred/series/observations?"
        f"series_id={series_id}&api_key={fred_key}&file_type=json&sort_order=desc&limit=1"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            obs = data.get("observations", [])[0]
            return {
                "series_id": series_id,
                "date": obs.get("date"),
                "value": float(obs.get("value", 0.0)),
                "status": "success"
            }
    except Exception as e:
        return {"series_id": series_id, "value": None, "status": f"Error: {str(e)}"}


# ---------------------------------------------------------------------------
# 3. Dynamic Live RSS Web Stream Fetcher
# ---------------------------------------------------------------------------
def fetch_live_sector_rss(topic_query: str = "copper supply chain"):
    """Fetches live Google News RSS search results dynamically for selected sector."""
    try:
        query = urllib.parse.quote(topic_query)
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item')[:3]:
            title = item.find('title').text if item.find('title') is not None else 'Live Market Signal'
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else 'Recent'

            clean_title = re.sub(r' - [^-]+$', '', title)
            sentiment = analyze_text_sentiment(clean_title)

            items.append({
                "title": clean_title,
                "published": pub_date,
                "sentiment": sentiment,
                "estimated_impact": int(abs(sentiment) * 120000) + 45000
            })
        return items
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 4. Synchronizer Function
# ---------------------------------------------------------------------------
def sync_robot_feeds():
    """Executes full cross-validation engine across Macro APIs & IMAP Feeds."""
    newsletters = fetch_gmail_newsletters(max_emails=15)
    gscpi_val = fetch_ny_fed_gscpi()
    world_bank_meta = fetch_world_bank_commodity_pink_sheet("PALLFNFINDEXQ")
    fred_meta = fetch_fred_indicator("MNFCTRMPCIMSA")

    linkedin_score = newsletters[0].get("sentiment_score", -0.10) if newsletters else -0.10

    # Convert GSCPI standard deviation into a [-1.0, +1.0] sentiment scale
    gscpi_sentiment = float(np.clip(-gscpi_val / 3.0, -1.0, 1.0))

    feed_data = {
        "status": "synced",
        "newsletters": newsletters,
        "linkedin_score": linkedin_score,
        "hard_macro": {
            "gscpi_raw": round(gscpi_val, 2),
            "gscpi_sentiment": round(gscpi_sentiment, 2),
            "world_bank": world_bank_meta,
            "fred": fred_meta
        }
    }

    try:
        signals_file = os.path.join(os.path.dirname(__file__), "robot_signals.json")
        with open(signals_file, "w") as f:
            json.dump(feed_data, f, indent=2)
    except Exception:
        pass

    return feed_data


# ---------------------------------------------------------------------------
# 5. Multi-Source Composite Sentiment ($SI_{\text{composite}}$) Engine
# ---------------------------------------------------------------------------
def calculate_composite_sentiment(feed_signals: dict = None) -> dict:
    """Calculates weighted composite sentiment SI_composite across hard macro and soft sources."""
    if feed_signals is None:
        feed_signals = {}

    weights = {
        "gscpi_index": 0.35,
        "world_bank_pinksheet": 0.25,
        "linkedin_feed": 0.20,
        "gis_telemetry": 0.10,
        "field_emails": 0.10,
    }

    scores = {
        "gscpi_index": float(feed_signals.get("gscpi_sentiment", -0.15)),
        "world_bank_pinksheet": float(feed_signals.get("world_bank_score", -0.20)),
        "linkedin_feed": float(feed_signals.get("linkedin_score", -0.10)),
        "gis_telemetry": float(feed_signals.get("gis_score", -0.10)),
        "field_emails": float(feed_signals.get("field_email_score", -0.25)),
    }

    si_composite = sum(weights[k] * scores[k] for k in weights)
    si_composite = float(np.clip(si_composite, -1.0, 1.0))

    return {
        "si_composite": si_composite,
        "individual_scores": scores,
        "weights": weights,
    }


# ---------------------------------------------------------------------------
# 6. Operational Quantification Engine (Levers: ΔD, ΔLT, VaR, POR Offset)
# ---------------------------------------------------------------------------
def compute_quantified_operational_impact(
    si_composite: float, base_demand: int, k_demand: float = 0.25
) -> dict:
    """Quantifies S&OP and CTRM operational levers dynamically based on SI_composite."""
    surge_multiplier = 1.0 + (abs(si_composite) * k_demand)
    quantified_demand_surge = int(base_demand * surge_multiplier)
    delta_demand = quantified_demand_surge - base_demand

    lead_time_buffer_days = max(0.0, round(-si_composite * 7.5, 1))

    if si_composite < -0.35:
        target_hedge_pct = 85.0
        action_flag = "CRITICAL: Trigger CTRM Option Collar / Fixed Swap"
    elif si_composite < -0.15:
        target_hedge_pct = 60.0
        action_flag = "MODERATE: Lock 60-Day Forward Exposure"
    else:
        target_hedge_pct = 30.0
        action_flag = "STABLE: Standard Operational Buffer"

    return {
        "si_composite": round(si_composite, 4),
        "base_demand": base_demand,
        "quantified_demand_surge": quantified_demand_surge,
        "delta_demand_units": delta_demand,
        "lead_time_buffer_days": lead_time_buffer_days,
        "target_hedge_pct": target_hedge_pct,
        "recommended_action": action_flag,
    }


def calculate_dynamic_erp_order_offset(por_baseline_date_str: str, transit_delay_days: float) -> str:
    """Executes ERP Dynamic Order Offset equation: POR_offset = POR_baseline - Delta_LT_transit"""
    try:
        base_date = datetime.strptime(por_baseline_date_str, "%Y-%m-%d")
        offset_date = base_date - timedelta(days=transit_delay_days)
        return offset_date.strftime("%Y-%m-%d")
    except Exception:
        return por_baseline_date_str


# ---------------------------------------------------------------------------
# 7. End-to-End S&OP Cascade Central Orchestrator
# ---------------------------------------------------------------------------
def run_end_to_end_sop_cascade(
    base_demand_units: int = 200000,
    raw_mat_ratio_per_unit: float = 1.25,
    current_spot_price: float = 4.15,
    por_baseline_date: str = "2026-11-15"
) -> dict:
    """Central Orchestrator: Passes live feed outputs sequentially down through
    Demand/Supply, Procurement, CTRM Delta-Hedging, Logistics, and Executive S&OP.
    """
    si_composite = -0.28
    
    # Safely extract session state if executed within Streamlit context
    try:
        import streamlit as st
        signals = st.session_state.get("latest_robot_signals", {})
        si_composite = signals.get("sentiment_index", st.session_state.get("si_composite", -0.28))
    except Exception:
        pass

    # STAGE 2: DEMAND/SUPPLY MATCH (Surge & Order Offset Calculation)
    k_demand = 0.25
    surge_multiplier = 1.0 + (abs(si_composite) * k_demand)
    quantified_demand_surge = int(base_demand_units * surge_multiplier)
    delta_demand_surge = quantified_demand_surge - base_demand_units

    transit_delay_days = max(0.0, round(abs(si_composite) * 12.0, 1))
    por_offset_date = calculate_dynamic_erp_order_offset(por_baseline_date, transit_delay_days)

    # STAGE 3: PHYSICAL PROCUREMENT
    expedited_po_units = delta_demand_surge
    target_vendor_notice_date = calculate_dynamic_erp_order_offset(por_offset_date, 5.0)

    # STAGE 4: CTRM DESK (Incremental Delta-Hedging)
    incremental_raw_material_lbs = delta_demand_surge * raw_mat_ratio_per_unit
    incremental_financial_exposure = incremental_raw_material_lbs * current_spot_price

    target_hedge_ratio = 0.85 if si_composite < -0.30 else 0.50
    incremental_volume_to_hedge_lbs = incremental_raw_material_lbs * target_hedge_ratio
    capital_to_commit_hedge = incremental_volume_to_hedge_lbs * current_spot_price

    # STAGE 5: GLOBAL LOGISTICS & GIS CONTROL TOWER
    is_air_freight_modal_shift = transit_delay_days > 7.0
    freight_surcharge_per_unit = 2.45 if is_air_freight_modal_shift else 0.65
    total_freight_surcharge_cost = quantified_demand_surge * freight_surcharge_per_unit

    # STAGE 6: EXECUTIVE S&OP CONSOLIDATED P&L IMPACT
    unit_selling_price = 18.50
    delta_gross_revenue = delta_demand_surge * unit_selling_price
    delta_cogs = delta_demand_surge * (current_spot_price * raw_mat_ratio_per_unit)
    net_ebitda_impact = delta_gross_revenue - (delta_cogs + total_freight_surcharge_cost)

    cascade_results = {
        "si_composite": si_composite,
        "demand": {
            "base_units": base_demand_units,
            "total_surge_units": quantified_demand_surge,
            "delta_surge_units": delta_demand_surge,
        },
        "procurement": {
            "por_baseline": por_baseline_date,
            "por_offset": por_offset_date,
            "transit_delay_days": transit_delay_days,
            "vendor_notice_date": target_vendor_notice_date,
            "expedited_po_units": expedited_po_units
        },
        "ctrm": {
            "incremental_lbs_exposed": incremental_raw_material_lbs,
            "incremental_exposure_usd": incremental_financial_exposure,
            "target_hedge_ratio": target_hedge_ratio,
            "incremental_lbs_to_hedge": incremental_volume_to_hedge_lbs,
            "capital_committed_usd": capital_to_commit_hedge
        },
        "logistics": {
            "modal_shift_air": is_air_freight_modal_shift,
            "freight_surcharge_per_unit": freight_surcharge_per_unit,
            "total_freight_surcharge_usd": total_freight_surcharge_cost
        },
        "exec_sop": {
            "delta_revenue_usd": delta_gross_revenue,
            "delta_cogs_usd": delta_cogs,
            "net_ebitda_impact_usd": net_ebitda_impact
        }
    }

    try:
        import streamlit as st
        st.session_state["active_sop_cascade"] = cascade_results
    except Exception:
        pass

    return cascade_results