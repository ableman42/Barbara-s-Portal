#!/usr/bin/env python3
"""
Barbara's Portal — Daily Content Generator
Runs every morning at 8am Pacific via GitHub Actions.
Calls Claude API to generate fresh content, saves as content.json.
"""

import anthropic
import json
import datetime
import os
import sys

# ── DATE ──────────────────────────────────────────────────────────────────────
pacific_offset = datetime.timezone(datetime.timedelta(hours=-7))  # PDT (UTC-7)
today = datetime.datetime.now(pacific_offset)
weekday   = today.strftime("%A")
month_day = today.strftime("%B %-d")
date_str  = today.strftime("%Y-%m-%d")
day_of_year = today.timetuple().tm_yday

# ── LAUNDRY SUNDAYS ────────────────────────────────────────────────────────────
laundry_start = datetime.date(2026, 5, 31)
today_date    = today.date()
is_laundry_day = (
    today_date.weekday() == 6 and
    (today_date - laundry_start).days >= 0 and
    (today_date - laundry_start).days % 14 == 0
)

# ── ARTICLES QUEUE ─────────────────────────────────────────────────────────────
QUEUED_ARTICLES_FILE = "queued_articles.json"
queued = []
if os.path.exists(QUEUED_ARTICLES_FILE):
    with open(QUEUED_ARTICLES_FILE) as f:
        queued = json.load(f)

queued_note = ""
if queued:
    queued_note = f"\n\nSean has queued these specific articles for today or upcoming days — use one or more if appropriate:\n{json.dumps(queued[:3], indent=2)}"

# ── PROMPT ────────────────────────────────────────────────────────────────────
PROMPT = f"""You are generating the daily content for a warm, personal web portal built for Barbara, an 80+ year old woman living at Park View Villas independent living in Port Angeles, Washington.

Today is {weekday}, {month_day}, {date_str}.

About Barbara:
- Hungarian-American, born in Hungary, her Hungarian name is Ildiko
- Loves nature, animals, history, travel, culture, gardening, reading
- Enjoys learning new things but nothing too heavy or political
- Has a cognitive deficit so content should be warm, gentle, and clear
- Lives in Port Angeles WA — loves the Olympic Peninsula, the Strait of Juan de Fuca, local wildlife
- Family: son Sean in Alexandria VA, daughter Suzy

Generate today's portal content as a JSON object with EXACTLY this structure. Return ONLY valid JSON, no markdown, no backticks, no explanation:

{{
  "date_display": "{weekday}, {month_day}",
  "quote": {{
    "text": "A short uplifting quote (under 20 words)",
    "author": "Author name"
  }},
  "fun_fact": {{
    "text": "An interesting fun fact Barbara would enjoy — nature, animals, Hungarian culture, history, food, science, language. 2-3 sentences.",
    "tag": "Short topic tag e.g. 'Hungarian culture' or 'Ocean life'"
  }},
  "short_read": {{
    "meta": "5 min · [Topic]",
    "title": "Article title",
    "teaser": "2 sentence teaser that makes her want to read it",
    "url": "Real URL to a reputable article (BBC, Smithsonian, NPR, National Geographic, NPS, etc.)"
  }},
  "medium_read": {{
    "meta": "15 min · [Topic]",
    "title": "Article title",
    "teaser": "2 sentence teaser",
    "url": "Real URL to a reputable article"
  }},
  "long_read": {{
    "meta": "35 min · [Topic]",
    "title": "Article title",
    "teaser": "2 sentence teaser",
    "url": "Real URL to a reputable article"
  }},
  "port_angeles": {{
    "icon": "One relevant emoji",
    "title": "Title of today's local fact or outing idea",
    "description": "2-3 sentences about something interesting in or around Port Angeles.",
    "link_text": "Short link label",
    "link_url": "Real URL to learn more"
  }},
  "puzzle_1": {{
    "question": "Fill in the blank sentence with ___ for the answer",
    "answer": 15,
    "answer_is_number": true,
    "close_range": 2,
    "correct_response": "Warm encouraging response when correct",
    "close_response": "Warm response when close",
    "wrong_response": "Gentle response revealing the answer",
    "learn_more_text": "1-2 sentences of interesting context about the answer",
    "learn_more_url": "Real URL to learn more",
    "learn_more_label": "Link label — Source name"
  }},
  "puzzle_2": {{
    "question": "Which word means '...'?",
    "options": ["Wrong option", "Correct option", "Wrong option", "Wrong option"],
    "correct_index": 1,
    "correct_response": "Warm encouraging response",
    "wrong_response": "Gentle response revealing the answer",
    "learn_more_text": "1-2 sentences of interesting context about the word",
    "learn_more_url": "Real URL to learn more",
    "learn_more_label": "Link label — Source name"
  }},
  "puzzle_3": {{
    "question": "Trivia question",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 1,
    "correct_response": "Warm encouraging response with a fun fact",
    "wrong_response": "Gentle response revealing the answer with context",
    "learn_more_text": "1-2 sentences of interesting context",
    "learn_more_url": "Real URL to learn more",
    "learn_more_label": "Link label — Source name"
  }},
  "game": {{
    "icon": "🫧",
    "title": "Bubble Shooter",
    "description": "A relaxing bubble puzzle game — aim and pop matching colored bubbles. Easy to pick up, fun to play!",
    "url": "https://www.bubbleshooter.net"
  }}
}}{queued_note}

Rules:
- All article URLs must be real, working links to reputable sources
- Puzzles should be gentle — never trick questions, always warm responses
- Vary topics day to day (use day {day_of_year} of the year as a seed for variety)
- Keep everything uplifting, curious, and warm
- For puzzle_1, answer can be a number OR a word — if a word, set answer_is_number to false and answer to the word string
- The correct_index for puzzles 2 and 3 should be randomized (don't always put the correct answer in position 1)
"""

# ── CALL CLAUDE ───────────────────────────────────────────────────────────────
print(f"Generating content for {date_str}...")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[{"role": "user", "content": PROMPT}]
)

raw = message.content[0].text.strip()

if raw.startswith("```"):
    raw = raw.split("\n", 1)[1]
    raw = raw.rsplit("```", 1)[0]

content = json.loads(raw)

content["generated_at"] = today.isoformat()
content["date"] = date_str
content["is_laundry_day"] = is_laundry_day

# ── SAVE content.json ─────────────────────────────────────────────────────────
with open("content.json", "w") as f:
    json.dump(content, f, indent=2, ensure_ascii=False)

print(f"✓ content.json written for {date_str}")
print(f"  Quote: {content['quote']['text'][:60]}...")
print(f"  Fun fact tag: {content['fun_fact']['tag']}")
print(f"  Laundry day: {is_laundry_day}")

# ── GOOGLE DRIVE PHOTO SCAN ───────────────────────────────────────────────────
# Scans the Memory Lane Drive folder and writes photos.json
# Requires GOOGLE_SERVICE_ACCOUNT_JSON secret in GitHub Actions
import base64, urllib.request, urllib.parse

def get_drive_photos():
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json:
        print("  ⚠ No GOOGLE_SERVICE_ACCOUNT_JSON secret — skipping photo scan")
        return None

    try:
        import json as _json
        # Parse service account credentials
        sa = _json.loads(sa_json)

        # Build JWT for Google OAuth2
        import time, hmac, hashlib
        now = int(time.time())
        header = base64.urlsafe_b64encode(b'{"alg":"RS256","typ":"JWT"}').rstrip(b'=').decode()
        payload = base64.urlsafe_b64encode(_json.dumps({
            "iss": sa["client_email"],
            "scope": "https://www.googleapis.com/auth/drive.readonly",
            "aud": "https://oauth2.googleapis.com/token",
            "exp": now + 3600,
            "iat": now
        }).encode()).rstrip(b'=').decode()

        # Sign with RSA private key (requires cryptography package)
        try:
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.backends import default_backend

            private_key = serialization.load_pem_private_key(
                sa["private_key"].encode(), password=None, backend=default_backend()
            )
            to_sign = f"{header}.{payload}".encode()
            signature = private_key.sign(to_sign, padding.PKCS1v15(), hashes.SHA256())
            sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
            jwt = f"{header}.{payload}.{sig_b64}"
        except ImportError:
            print("  ⚠ cryptography package not installed — skipping photo scan")
            return None

        # Exchange JWT for access token
        token_data = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt
        }).encode()
        token_req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(token_req) as r:
            token_resp = _json.loads(r.read())
        access_token = token_resp["access_token"]

        # List image files in the Memory Lane folder
        FOLDER_ID = "1il6d_CgDAAlmArTcRqxZkT-34g5l4Gz1"
        query = urllib.parse.urlencode({
            "q": f"'{FOLDER_ID}' in parents and mimeType contains 'image/' and trashed=false",
            "fields": "files(id,name)",
            "pageSize": "200"
        })
        list_req = urllib.request.Request(
            f"https://www.googleapis.com/drive/v3/files?{query}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        with urllib.request.urlopen(list_req) as r:
            files = _json.loads(r.read())["files"]

        # Filter out HEIC (not browser-displayable)
        photos = [
            {"id": f["id"], "name": f["name"], "caption": ""}
            for f in files
            if not f["name"].lower().endswith(".heic")
        ]
        print(f"  📸 Found {len(photos)} photos in Drive folder")
        return photos

    except Exception as e:
        print(f"  ⚠ Drive photo scan failed: {e}")
        return None

photos = get_drive_photos()
if photos is not None:
    with open("photos.json", "w") as f:
        json.dump(photos, f, indent=2)
    print(f"  ✓ photos.json written with {len(photos)} photos")

# ── DAILY EMAIL TO BARBARA ────────────────────────────────────────────────────
import urllib.request, urllib.parse, json as _json

EMAILJS_SERVICE_ID  = "service_7rdoaxm"
EMAILJS_TEMPLATE_ID = "template_daily_digest"   # new template — see setup instructions
EMAILJS_PUBLIC_KEY  = "To5e32R6X29PvLHUN"

def send_daily_email(content):
    """Send Barbara's daily digest email via EmailJS REST API."""
    try:
        # Build a clean digest of today's content
        quote_text  = content.get("quote", {}).get("text", "")
        quote_attr  = content.get("quote", {}).get("author", "")
        fact_text   = content.get("fun_fact", {}).get("text", "")
        fact_tag    = content.get("fun_fact", {}).get("tag", "")
        short_title = content.get("short_read",  {}).get("title", "")
        short_meta  = content.get("short_read",  {}).get("meta",  "")
        med_title   = content.get("medium_read", {}).get("title", "")
        med_meta    = content.get("medium_read", {}).get("meta",  "")
        long_title  = content.get("long_read",   {}).get("title", "")
        long_meta   = content.get("long_read",   {}).get("meta",  "")
        p1_q = content.get("puzzle_1", {}).get("question", "")
        p2_q = content.get("puzzle_2", {}).get("question", "")
        p3_q = content.get("puzzle_3", {}).get("question", "")
        date_display = content.get("date_display", date_str)

        payload = {
            "service_id":  EMAILJS_SERVICE_ID,
            "template_id": EMAILJS_TEMPLATE_ID,
            "user_id":     EMAILJS_PUBLIC_KEY,
            "template_params": {
                "date_display": date_display,
                "quote_text":   quote_text,
                "quote_attr":   quote_attr,
                "fact_text":    fact_text,
                "fact_tag":     fact_tag,
                "short_title":  short_title,
                "short_meta":   short_meta,
                "med_title":    med_title,
                "med_meta":     med_meta,
                "long_title":   long_title,
                "long_meta":    long_meta,
                "p1_question":  p1_q,
                "p2_question":  p2_q,
                "p3_question":  p3_q,
                "portal_url":   "https://barbaraildiko.com",
                "to_email":     "barb.barrett@comcast.net",
                "cc_email":     "ableman42@gmail.com",
            }
        }

        data = _json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.emailjs.com/api/v1.0/email/send",
            data=data,
            headers={
                "Content-Type": "application/json",
                "origin": "https://barbaraildiko.com"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = resp.read().decode()
            print(f"  ✓ Daily email sent to Barbara ({result})")

    except Exception as e:
        print(f"  ⚠ Email send failed (non-fatal): {e}")

send_daily_email(content)
print("✓ All done!")
