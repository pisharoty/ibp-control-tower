import warnings
# Mute macOS LibreSSL and non-critical system warnings
warnings.filterwarnings("ignore")

import time
import requests
import yfinance as yf
from textblob import TextBlob
import feedparser

class BulletproofDataEngine:
    """
    Enterprise Data Engine for S&OP Control Towers.
    Fetches real-time market, news sentiment, and express parcel telemetry 
    with instant fallback to structured canned mock data upon network failures.
    """
    
    # -------------------------------------------------------------------
    # Static "Canned" Data Fallbacks (Guarantees zero-downtime during demos)
    # -------------------------------------------------------------------
    CANNED_VOLATILITY = {
        "symbol": "NVDA", 
        "spot": 125.40, 
        "implied_vol": 48.5, 
        "source": "🟡 CANNED MOCK"
    }
    
    CANNED_NLP = {
        "headline": "Port Congestion Moderates in West Coast Hubs", 
        "sentiment": 0.15, 
        "risk": "🟢 STABLE", 
        "source": "🟡 CANNED MOCK"
    }
    
    CANNED_PARCEL = {
        "tracking_code": "TRACK_FEDEX_9982", 
        "carrier": "FedEx Express (Air)", 
        "status": "In Transit - Flight On Schedule", 
        "origin": "Memphis, TN (MEM Hub)",
        "destination": "Austin, TX (Fab Plant)",
        "delay_hours": 0,
        "source": "🟡 CANNED MOCK"
    }

    # -------------------------------------------------------------------
    # 1. Market Volatility & Options Surface Engine (yfinance)
    # -------------------------------------------------------------------
    @classmethod
    def get_market_volatility(cls, symbol="NVDA", timeout=3.0) -> dict:
        """Fetch live spot price & implied volatility (IV) with instant fallback."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", timeout=timeout)
            if hist.empty:
                raise ValueError("No live data returned from yfinance")
            
            spot = float(hist['Close'].iloc[-1])
            iv = 45.0  # Default fallback IV baseline if options chain lookup fails
            
            expirations = ticker.expirations
            if expirations:
                opt = ticker.option_chain(expirations[0])
                if not opt.calls.empty:
                    iv = float(opt.calls['impliedVolatility'].iloc[0] * 100)

            return {
                "symbol": symbol,
                "spot": round(spot, 2),
                "implied_vol": round(iv, 1),
                "source": "🟢 LIVE YFINANCE"
            }
        except Exception:
            return cls.CANNED_VOLATILITY

    # -------------------------------------------------------------------
    # 2. Commercial NLP Sensing Engine (Google News RSS + TextBlob)
    # -------------------------------------------------------------------
    @classmethod
    def get_nlp_news_signal(cls, query="semiconductor supply chain", timeout=3.0) -> dict:
        """Fetch live RSS news headline, run NLP sentiment scoring, and output risk."""
        try:
            rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(rss_url, timeout=timeout)
            feed = feedparser.parse(resp.content)

            if not feed.entries:
                raise ValueError("No RSS stories found")

            latest_story = feed.entries[0]
            sentiment = TextBlob(latest_story.title).sentiment.polarity

            return {
                "headline": latest_story.title,
                "sentiment": round(sentiment, 2),
                "risk": "🔴 HIGH RISK" if sentiment < -0.15 else "🟢 STABLE",
                "source": "🟢 LIVE NEWS RSS"
            }
        except Exception:
            return cls.CANNED_NLP

    # -------------------------------------------------------------------
    # 3. High-Value Express Parcel Tracking (FedEx / UPS / Air Cargo)
    # -------------------------------------------------------------------
    @classmethod
    def get_parcel_telemetry(cls, tracking_code="1Z9999999999999999", carrier="UPS", api_key=None, timeout=3.0) -> dict:
        """Fetch high-tech express parcel telemetry with EasyPost API or graceful fallback."""
        try:
            if not api_key:
                raise ValueError("No API key provided - using high-reliability fallback")
                
            import easypost
            easypost.api_key = api_key
            tracker = easypost.Tracker.create(tracking_code=tracking_code, carrier=carrier)
            
            return {
                "tracking_code": tracker.tracking_code,
                "carrier": carrier,
                "status": tracker.status,
                "origin": tracker.tracking_details[0].get("location", "N/A"),
                "destination": tracker.tracking_details[-1].get("location", "N/A"),
                "delay_hours": 0 if tracker.status != "delayed" else 12,
                "source": "🟢 LIVE EASYPOST API"
            }
        except Exception:
            return cls.CANNED_PARCEL


# =======================================================================
# Execution Demonstration Block
# =======================================================================
if __name__ == "__main__":
    engine = BulletproofDataEngine()
    
    print("\n" + "="*70)
    print(" 🚀 CONTROL TOWER LIVE DATA INTEGRATION DASHBOARD ")
    print("="*70)
    
    # 1. Test Financial Volatility Feed
    market_feed = engine.get_market_volatility("NVDA")
    print(f"\n[1] FINANCIAL MARKET VOLATILITY FEED")
    print(f"    • Symbol:      {market_feed['symbol']}")
    print(f"    • Spot Price:  ${market_feed['spot']}")
    print(f"    • Implied Vol: {market_feed['implied_vol']}%")
    print(f"    • Data Source: {market_feed['source']}")

    # 2. Test Commercial Sensing NLP
    nlp_feed = engine.get_nlp_news_signal("semiconductor shortage")
    print(f"\n[2] COMMERCIAL NLP NEWS SENSING SIGNAL")
    print(f"    • Headline:   '{nlp_feed['headline']}'")
    print(f"    • Sentiment:  {nlp_feed['sentiment']} (-1.0 Negative to +1.0 Positive)")
    print(f"    • Risk Level: {nlp_feed['risk']}")
    print(f"    • Data Source: {nlp_feed['source']}")

    # 3. Test High-Value Electronics Express Logistics
    parcel_feed = engine.get_parcel_telemetry("TRACK_FEDEX_9982", "FedEx")
    print(f"\n[3] EXPRESS PARCEL TELEMETRY (CHIPS & ELECTRONICS)")
    print(f"    • Tracking:   {parcel_feed['tracking_code']} ({parcel_feed['carrier']})")
    print(f"    • Route:      {parcel_feed['origin']}  ➔  {parcel_feed['destination']}")
    print(f"    • Status:     {parcel_feed['status']}")
    print(f"    • Data Source: {parcel_feed['source']}")
    
    print("\n" + "="*70 + "\n")
