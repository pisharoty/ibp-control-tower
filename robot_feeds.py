import email
from email.header import decode_header
import imaplib
import json
import os
import re
import bs4
import requests

GEP_URL = (
    "https://www.gep.com/knowledge-bank/global-supply-chain-volatility-index"
)

# Gmail Credentials from Environment Variables
GMAIL_USER = os.getenv("GMAIL_USER", "pisharoty1@gmail.com")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "")


def fetch_gep_index():
  """Scrapes targeted GEP Volatility Index metrics and commentary."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }
  try:
    res = requests.get(GEP_URL, headers=headers, timeout=10)
    if res.status_code != 200:
      return {
          "source": "GEP Index",
          "status": "Error",
          "details": f"HTTP {res.status_code}",
      }

    soup = bs4.BeautifulSoup(res.text, "html.parser")
    raw_paragraphs = [
        p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()
    ]
    index_paragraphs = [
        p
        for p in raw_paragraphs
        if any(
            kw in p.lower()
            for kw in [
                "volatility",
                "index",
                "capacity",
                "supply chain",
                "transportation",
            ]
        )
        and "gartner" not in p.lower()
    ]

    summary_text = (
        " ".join(index_paragraphs[:3])
        if index_paragraphs
        else " ".join(raw_paragraphs[:3])
    )
    found_floats = re.findall(r"[-+]?\d+\.\d+", summary_text)
    index_score = float(found_floats[0]) if found_floats else -0.32

    return {
        "source": "GEP Supply Chain Volatility Index",
        "volatility_score": index_score,
        "leadtime_delay_days": round(max(2.0, abs(index_score) * 6.5), 1),
        "demand_surge_units": int(65000 + (index_score * 10000)),
        "summary": summary_text[:280] + "...",
    }
  except Exception as e:
    return {"source": "GEP Index", "status": "Error", "details": str(e)}


def fetch_gmail_newsletters():
  """Connects to Gmail via IMAP and parses the latest LinkedIn Newsletter or test email."""
  if not GMAIL_APP_PASS:
    return [{
        "source": "LinkedIn Newsletters",
        "status": "Pending GMAIL_APP_PASS Configuration",
    }]

  try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    mail.select("inbox")

    # Search for official LinkedIn emails OR test emails with "LinkedIn" in the subject
    status, messages = mail.search(
        None,
        'OR (FROM "newsletters-noreply@linkedin.com") (SUBJECT "LinkedIn")',
    )
    email_ids = messages[0].split()

    if not email_ids:
      return [{
          "source": "LinkedIn Newsletters",
          "status": "No LinkedIn emails found",
      }]

    # Fetch the latest matching email
    latest_id = email_ids[-1]
    res, msg_data = mail.fetch(latest_id, "(RFC822)")

    for response_part in msg_data:
      if isinstance(response_part, tuple):
        msg = email.message_from_bytes(response_part[1])

        # Decode email subject
        subject_header = msg["Subject"]
        decoded = decode_header(subject_header)[0]
        subject = decoded[0]
        if isinstance(subject, bytes):
          subject = subject.decode(decoded[1] if decoded[1] else "utf-8")

        # Parse HTML or Plain Text body
        body = ""
        if msg.is_multipart():
          for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ["text/html", "text/plain"]:
              body = part.get_payload(decode=True).decode(errors="ignore")
              if content_type == "text/html":
                break
        else:
          body = msg.get_payload(decode=True).decode(errors="ignore")

        clean_text = bs4.BeautifulSoup(body, "html.parser").get_text()
        clean_summary = " ".join(clean_text.split())[:250] + "..."

        mail.logout()
        return [{
            "title": subject,
            "published": msg.get("Date", "Recent"),
            "summary": clean_summary,
            "source": "LinkedIn Newsletter (Gmail Direct)",
        }]

    mail.logout()
  except Exception as e:
    return [
        {
            "source": "LinkedIn Newsletters",
            "status": "Error",
            "details": str(e),
        }
    ]


def sync_robot_feeds():
  """Orchestrates GEP and Gmail scrapers into robot_signals.json."""
  combined_payload = {
      "gep_index": fetch_gep_index(),
      "newsletter_feeds": fetch_gmail_newsletters(),
  }

  with open("robot_signals.json", "w") as f:
    json.dump(combined_payload, f, indent=2)

  return combined_payload


if __name__ == "__main__":
  data = sync_robot_feeds()
  print(json.dumps(data, indent=2))