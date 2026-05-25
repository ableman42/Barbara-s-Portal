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
# Every other Sunday starting May 31, 2026
laundry_start = datetime.date(2026, 5, 31)
today_date    = today.date()
is_laundry_day = (
    today_date.weekday() == 6 and  # Sunday
    (today_date - laundry_start).days >= 0 and
    (today_date - laundry_start).days % 14 == 0
)

# ── ARTICLES QUEUE ─────────────────────────────────────────────────────────────
# Sean can add articles here by editing this file or via a separate queue file.
# Format: {"title": "...", "url": "...", "teaser": "...", "length": "5 min", "topic": "Nature"}
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
    "description": "2-3 sentences about something interesting in or around Port Angeles — local wildlife, Olympic National Park, the Strait, Elwha River, local history, seasonal events, ferry to Victoria, farmers markets, tide pools, Hurricane Ridge, etc.",
    "link_text": "Short link label",
    "link_url": "Real URL to learn more (NPS, local tourism, Wikipedia, etc.)"
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
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    messages=[{"role": "user", "content": PROMPT}]
)

raw = message.content[0].text.strip()

# Strip markdown fences if present
if raw.startswith("```"):
    raw = raw.split("\n", 1)[1]
    raw = raw.rsplit("```", 1)[0]

content = json.loads(raw)

# Add metadata
content["generated_at"] = today.isoformat()
content["date"] = date_str
content["is_laundry_day"] = is_laundry_day

# ── SAVE ──────────────────────────────────────────────────────────────────────
with open("content.json", "w") as f:
    json.dump(content, f, indent=2, ensure_ascii=False)

print(f"✓ content.json written successfully for {date_str}")
print(f"  Quote: {content['quote']['text'][:60]}...")
print(f"  Fun fact tag: {content['fun_fact']['tag']}")
print(f"  Laundry day: {is_laundry_day}")
