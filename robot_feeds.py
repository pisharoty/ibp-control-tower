import json
import os
import re
import bs4
import feedparser
import requests

# 1. Option 1: Direct Web Scraper Target (Zero Email Required)
GEP_URL = (
    "https://www.gep.com/knowledge-bank/global-supply-chain-volatility-index"
)

# 2. Step 1: Kill-the-Newsletter RSS Bridge Feed URL
# Set KTN_FEED_URL as an Environment Variable in Render, or paste your generated XML link here
KTN_FEED_URL = os.getenv(
    "KTN_FEED_URL", "https://kill-the-newsletter.com/feeds/YOUR_FEED_ID.xml"
)


def fetch_gep_index():
  """Scrapes GEP Volatility Index directly from source webpage."""
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
  try:
    res = requests.get(GEP_URL, headers=headers, timeout=10)
    if res.status_code != 200:
      return {
          "source": "GEP Index",
          "status": "Error",
          "details": f"HTTP {res.status_code}",
      }

    soup = bs4.BeautifulSoup(res.text, "html.parser")
    paragraphs = [
        p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()
    ]
    full_text = " ".join(paragraphs)

    # Extract score using regex float matching
    found_floats = re.findall(r"[-+]?\d+\.\d+", full_text)
    index_score = float(found_floats[0]) if found_floats else 0.45

    # Map index score to operational supply chain metrics
    leadtime_delay = round(max(2.0, index_score * 7.5), 1)
    surge_units = int(65000 + (index_score * 10000))

    return {
        "source": "GEP Supply Chain Volatility Index",
        "volatility_score": index_score,
        "leadtime_delay_days": leadtime_delay,
        "demand_surge_units": surge_units,
        "summary": full_text[:250] + "...",
    }
  except Exception as e:
    return {"source": "GEP Index", "status": "Error", "details": str(e)}


def fetch_ktn_feed(feed_url=KTN_FEED_URL):
  """Parses emails forwarded from Kill-the-Newsletter Atom/RSS feed."""
  if "YOUR_FEED_ID" in feed_url:
    return [{
        "source": "LinkedIn Newsletters",
        "status": "Pending KTN_FEED_URL Configuration",
    }]

  try:
    parsed = feedparser.parse(feed_url)
    newsletter_signals = []

    for entry in parsed.entries[:5]:  # Fetch up to 5 recent emails
      # Strip HTML markup out of email body text
      clean_body = bs4.BeautifulSoup(
          entry.get("summary", ""), "html.parser"
      ).get_text()

      newsletter_signals.append({
          "title": entry.get("title", "Untitled Newsletter"),
          "published": entry.get("published", "Recent"),
          "summary": clean_body[:200].strip() + "...",
          "link": entry.get("link", feed_url),
      })
    return newsletter_signals
  except Exception as e:
    return [
        {
            "source": "LinkedIn Newsletters",
            "status": "Error",
            "details": str(e),
        }
    ]


def sync_robot_feeds():
  """Orchestrates both scrapers into a unified JSON cache for Streamlit."""
  combined_payload = {
      "gep_index": fetch_gep_index(),
      "newsletter_feeds": fetch_ktn_feed(),
  }

  with open("robot_signals.json", "w") as f:
    json.dump(combined_payload, f, indent=2)

  return combined_payload


if __name__ == "__main__":
  data = sync_robot_feeds()
  print(json.dumps(data, indent=2))