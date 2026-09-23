import email
from email.header import decode_header
import imaplib
import json
import os
import re
import bs4
import numpy as np

# ---------------------------------------------------------------------------
# Helper: Lazy Runtime Credential Resolution (Prevents Import Deadlocks)
# ---------------------------------------------------------------------------


def _get_gmail_credentials():
  """Safely retrieves credentials at runtime without importing Streamlit at top-level."""
  user = os.getenv("GMAIL_USER", "pisharoty1@gmail.com")
  app_pass = os.getenv("GMAIL_APP_PASS", "")

  # Fallback to Streamlit secrets dynamically only when called at runtime
  if not app_pass:
    try:
      import streamlit as st

      user = st.secrets.get("GMAIL_USER", user)
      app_pass = st.secrets.get("GMAIL_APP_PASS", app_pass)
    except Exception:
      pass

  return user, app_pass


# ---------------------------------------------------------------------------
# 1. Dynamic Text Sentiment Parser (Polarity Score s_i)
# ---------------------------------------------------------------------------


def analyze_text_sentiment(text: str) -> float:
  """Parses raw text and computes a normalized polarity score s_i in [-1.0, +1.0]."""
  if not text:
    return 0.0

  bearish_words = [
      "outage",
      "curtailment",
      "strike",
      "delay",
      "bottleneck",
      "surge",
      "shortage",
      "deficit",
      "sanction",
      "force majeure",
      "disruption",
      "spike",
      "tightness",
      "shutdown",
  ]
  bullish_words = [
      "recovery",
      "surplus",
      "expansion",
      "easing",
      "resolution",
      "steady",
      "capacity expansion",
      "rebate",
      "normalization",
      "growth",
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
# 2. IMAP Live Email Ingestion Engine (Multi-Tier Search + Multi-Email Support)
# ---------------------------------------------------------------------------


def fetch_gmail_newsletters(max_emails: int = 5):
  """Connects to Gmail via IMAP, searches for newsletters across history,

  and returns parsed signals.
  """
  gmail_user, gmail_pass = _get_gmail_credentials()

  if not gmail_pass:
    return [{
        "source": "LinkedIn Newsletters",
        "status": (
            "GMAIL_APP_PASS is missing. Please set it in secrets or environment"
            " variables."
        ),
        "is_live": False,
        "sentiment_score": 0.0,
    }]

  try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(gmail_user, gmail_pass)
    mail.select("inbox")

    email_ids = []

    # Search Tier 1: Gmail raw search query across history (LinkedIn, newsletters, market updates)
    try:
      status, messages = mail.search(
          None, 'X-GM-RAW', 'linkedin OR newsletter OR supply OR market'
      )
      if status == 'OK' and messages[0]:
        email_ids = messages[0].split()
    except Exception:
      pass

    # Search Tier 2: Standard IMAP text search
    if not email_ids:
      status, messages = mail.search(None, 'TEXT "linkedin"')
      if status == 'OK' and messages[0]:
        email_ids = messages[0].split()

    # Search Tier 3: Search ALL inbox emails if specific queries returned nothing
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

    # Reverse to process the most recent emails first
    target_ids = list(reversed(email_ids))[:max_emails]
    parsed_newsletters = []

    for email_id in target_ids:
      res, msg_data = mail.fetch(email_id, '(RFC822)')
      for response_part in msg_data:
        if isinstance(response_part, tuple):
          msg = email.message_from_bytes(response_part[1])

          # Safely decode Subject Header
          subject_header = msg.get('Subject', 'LinkedIn Signal Update')
          decoded_header = decode_header(subject_header)[0]
          subject = decoded_header[0]
          if isinstance(subject, bytes):
            encoding = decoded_header[1] if decoded_header[1] else 'utf-8'
            subject = subject.decode(encoding, errors='ignore')

          # Parse Body Text
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
          clean_summary = (
              ' '.join(clean_text.split())[:300] + '...'
              if clean_text
              else 'No text summary available.'
          )

          full_content = f'{subject} {clean_text}'
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

    mail.logout()
    return (
        parsed_newsletters
        if parsed_newsletters
        else [{
            'source': 'LinkedIn Newsletters',
            'status': 'Could not parse email body content.',
            'is_live': True,
            'sentiment_score': 0.0,
        }]
    )

  except Exception as e:
    return [{
        'source': 'LinkedIn Newsletters',
        'status': f'IMAP Connection Error: {str(e)}',
        'is_live': False,
        'sentiment_score': 0.0,
    }]


# ---------------------------------------------------------------------------
# 3. Synchronizer Function
# ---------------------------------------------------------------------------


def sync_robot_feeds():
  """Fetches Gmail IMAP feeds and persists results to JSON."""
  newsletters = fetch_gmail_newsletters(max_emails=5)

  linkedin_score = -0.10
  if newsletters and "sentiment_score" in newsletters[0]:
    linkedin_score = newsletters[0]["sentiment_score"]

  feed_data = {
      "status": "synced",
      "newsletters": newsletters,
      "linkedin_score": linkedin_score,
  }

  try:
    signals_file = os.path.join(
        os.path.dirname(__file__), "robot_signals.json"
    )
    with open(signals_file, "w") as f:
      json.dump(feed_data, f, indent=2)
  except Exception:
    pass

  return feed_data


# ---------------------------------------------------------------------------
# 4. Multi-Source Composite Sentiment ($SI_{\text{composite}}$) Engine
# ---------------------------------------------------------------------------


def calculate_composite_sentiment(feed_signals: dict = None) -> dict:
  """Calculates weighted composite sentiment SI_composite across sources."""
  if feed_signals is None:
    feed_signals = {}

  weights = {
      "gep_index": 0.35,
      "bloomberg_rss": 0.25,
      "linkedin_feed": 0.20,
      "gis_telemetry": 0.10,
      "field_emails": 0.10,
  }

  scores = {
      "gep_index": float(feed_signals.get("gep_score", -0.20)),
      "bloomberg_rss": float(feed_signals.get("bloomberg_score", -0.40)),
      "linkedin_feed": float(feed_signals.get("linkedin_score", -0.50)),
      "gis_telemetry": float(feed_signals.get("gis_score", -0.10)),
      "field_emails": float(feed_signals.get("field_email_score", -0.30)),
  }

  si_composite = sum(weights[k] * scores[k] for k in weights)
  si_composite = float(np.clip(si_composite, -1.0, 1.0))

  return {
      "si_composite": si_composite,
      "individual_scores": scores,
      "weights": weights,
  }


# ---------------------------------------------------------------------------
# 5. Operational Quantification Engine (Levers: ΔD, ΔLT, VaR)
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