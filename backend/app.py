import os
import re
import logging
import json
from datetime import datetime, timezone

import httpx
import google.generativeai as genai
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from selectolax.parser import HTMLParser
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("VITE_GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
else:
    logger.warning("VITE_GEMINI_API_KEY not found in environment")

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

SEASON = "2026"
CRICBUZZ_SERIES_ID = "9241"
CREX_SERIES_SLUG = "indian-premier-league-2026-1PW"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
HTTP_TIMEOUT = 15.0

WINNERS = {
    "2024": "Kolkata Knight Riders",
    "2023": "Chennai Super Kings",
    "2022": "Gujarat Titans",
    "2021": "Chennai Super Kings",
    "2020": "Mumbai Indians",
    "2019": "Mumbai Indians",
    "2018": "Chennai Super Kings",
    "2017": "Mumbai Indians",
    "2016": "Sunrisers Hyderabad",
    "2015": "Mumbai Indians",
    "2014": "Kolkata Knight Riders",
    "2013": "Mumbai Indians",
    "2012": "Kolkata Knight Riders",
    "2011": "Chennai Super Kings",
    "2010": "Chennai Super Kings",
    "2009": "Deccan Chargers",
    "2008": "Rajasthan Royals"
}

TEAM_MAP = {
    "mi": "mumbai-indians", "csk": "chennai-super-kings", "rcb": "royal-challengers-bangalore",
    "kkr": "kolkata-knight-riders", "srh": "sunrisers-hyderabad", "dc": "delhi-capitals",
    "pbks": "punjab-kings", "rr": "rajasthan-royals", "gt": "gujarat-titans", "lsg": "lucknow-super-giants"
}

def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def safe_text(node, default: str = "") -> str:
    if node is None:
        return default
    try:
        return node.text(strip=True) or default
    except Exception:
        return default

def http_get(url: str, headers: dict = None) -> httpx.Response:
    merged = {**HEADERS, **(headers or {})}
    with httpx.Client(timeout=HTTP_TIMEOUT, headers=merged, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp

def error_payload(title: str, message: str, resolution: str, code: int = 500) -> tuple:
    return (
        jsonify({
            "status_code": code,
            "title": title,
            "message": message,
            "resolution": resolution,
        }),
        code,
    )

@app.route("/")
def home():
    return render_template("home.html", season=SEASON)

# --- Schedule ---
@app.route(f"/ipl-{SEASON}-schedule")
@app.route("/ipl-schedule")
def ipl_schedule():
    url = "https://www.sportskeeda.com/go/ipl/schedule"
    try:
        response = http_get(url)
        tree = HTMLParser(response.text)
        match_cards = tree.css("div.cricket-match-card-container")
        if not match_cards:
            return error_payload("No Schedule Data", "No match cards found.", "Try again later.")
        
        schedule = {}
        for i, card in enumerate(match_cards, 1):
            teams = [safe_text(t.css_first("div.cricket-match-card-team-name")) for t in card.css("div.cricket-match-card-team-info")]
            teams = [t for t in teams if t]
            venue = " ".join(safe_text(span) for span in (card.css_first("header.cricket-match-card-header").css("span.cricket-match-card--match-venue") if card.css_first("header.cricket-match-card-header") else [])).strip()
            date = safe_text(card.css_first("div.cricket-match-card-timer--date"), "TBD")
            time_ = safe_text(card.css_first("div.cricket-match-card-timer--time"), "TBD")
            schedule[f"Match {i}"] = {"Rival": f"{teams[0]} vs {teams[1]}" if len(teams) >= 2 else "TBD", "Location": venue or "Unknown", "Date": date, "Time": time_}
        return jsonify({"status_code": 200, "season": SEASON, "schedule": schedule})
    except Exception as e:
        logger.error(f"Schedule error: {e}")
        return error_payload("Server Error", str(e), "Try again later.")

# --- Points Table ---
@app.route(f"/ipl-{SEASON}-points-table")
@app.route("/ipl-points-table")
def ipl_points_table():
    url = "https://cf-gotham.sportskeeda.com/cricket/ipl/points-table"
    try:
        response = http_get(url)
        data = response.json()
        teams = data["table"][0]["table"][0]["group"]
        points_table = {}
        for i, team in enumerate(teams, 1):
            points_table[f"Team {i}"] = {
                "Name": team.get("team_name", "Unknown"),
                "Played": int(team.get("played", 0) or 0),
                "Won": int(team.get("won", 0) or 0),
                "Loss": int(team.get("lost", 0) or 0),
                "No Result": int(team.get("no_result", 0) or 0),
                "Net Run Rate": float(team.get("nrr", 0) or 0),
                "Points": int(team.get("points", 0) or 0),
            }
        return jsonify({"status_code": 200, "season": SEASON, "points_table": points_table})
    except Exception as e:
        logger.error(f"Points Table error: {e}")
        return error_payload("Server Error", str(e), "Try again later.")

# --- Live Scores ---
def _sportskeeda_match(card) -> dict:
    status = (card.attributes.get("data-match-status") or "").lower()
    teams = []
    for t in card.css("div.keeda_widget_team"):
        name_node = t.css_first("span.keeda_widget_team_name")
        score_node = t.css_first("span.keeda_widget_score")
        if name_node or score_node:
            teams.append({"name": safe_text(name_node, "TBD"), "score": safe_text(score_node, "")})
    if len(teams) < 2: return None
    result_node = card.css_first("div.marquee-strip")
    result = re.sub(r"\s+", " ", result_node.text(deep=True, separator=" ", strip=True)).strip() if result_node else ""
    return {
        "status": {"live": "Live", "post": "Completed", "pre": "Upcoming"}.get(status, status or "Unknown"),
        "team_1": teams[0]["name"], "score_1": teams[0]["score"] or "N.A",
        "team_2": teams[1]["name"], "score_2": teams[1]["score"] or "N.A",
        "result": result
    }

@app.route(f"/ipl-{SEASON}-live-score")
@app.route("/ipl-live-score")
def ipl_live_score():
    url = "https://www.sportskeeda.com/go/ipl?ref=carousel"
    try:
        response = http_get(url)
        tree = HTMLParser(response.text)
        cards = tree.css("div.keeda_cricket_match_list")
        matches = {}
        for i, card in enumerate(cards, 1):
            entry = _sportskeeda_match(card)
            if entry: matches[f"Match {i}"] = entry
        return jsonify({"status_code": 200, "season": SEASON, "matches": matches, "date_checked": today_iso()})
    except Exception as e:
        logger.error(f"Live Score error: {e}")
        return error_payload("Server Error", str(e), "Try again later.")

# --- Crex (S2) ---
def _crex_match(card) -> dict:
    try:
        team_nodes = card.css("div.team-name")
        score_nodes = card.css("div.team-score")
        if len(team_nodes) < 2: return None
        status = safe_text(card.css_first("div.match-status"), "Upcoming")
        return {
            "status": status,
            "team_1": safe_text(team_nodes[0]), "score_1": safe_text(score_nodes[0]) if len(score_nodes) > 0 else "N.A",
            "team_2": safe_text(team_nodes[1]), "score_2": safe_text(score_nodes[1]) if len(score_nodes) > 1 else "N.A",
            "result": safe_text(card.css_first("div.match-result"))
        }
    except: return None

@app.route(f"/ipl-{SEASON}-live-score-s2")
@app.route("/ipl-live-score-s2")
def ipl_live_score_s2():
    url = f"https://crex.live/fixtures/match-list/{CREX_SERIES_SLUG}"
    try:
        response = http_get(url)
        tree = HTMLParser(response.text)
        cards = tree.css("li.match-card")
        matches = {}
        for i, card in enumerate(cards, 1):
            entry = _crex_match(card)
            if entry: matches[f"Match {i}"] = entry
        return jsonify({"status_code": 200, "source": "crex", "matches": matches})
    except Exception as e:
        return error_payload("Crex Error", str(e), "Source unavailable.")

# --- Cricbuzz (S3) ---
def _cricbuzz_match(card) -> dict:
    try:
        teams = card.css("div.cb-lv-scrs-col")
        if len(teams) < 1: return None
        # Simplified parser for demonstration
        text = card.text(deep=True, separator=" ")
        return {"status": "Live", "info": text.strip()}
    except: return None

@app.route(f"/ipl-{SEASON}-live-score-s3")
@app.route("/ipl-live-score-s3")
def ipl_live_score_s3():
    url = "https://www.cricbuzz.com/cricket-series/9241/indian-premier-league-2026/matches"
    try:
        response = http_get(url)
        tree = HTMLParser(response.text)
        cards = tree.css("div.cb-mtch-lst")
        matches = {}
        for i, card in enumerate(cards, 1):
            matches[f"Match {i}"] = {"info": card.text(strip=True)}
        return jsonify({"status_code": 200, "source": "cricbuzz", "matches": matches})
    except Exception as e:
        return error_payload("Cricbuzz Error", str(e), "Source unavailable.")

# --- Squads ---
@app.route("/squad/<team_code>")
def get_squad(team_code):
    team_slug = TEAM_MAP.get(team_code.lower())
    if not team_slug:
        return error_payload("Invalid Team", "Code not found.", "Use mi, csk, rcb, etc.")
    url = f"https://www.sportskeeda.com/go/ipl/squads/{team_slug}"
    try:
        response = http_get(url)
        tree = HTMLParser(response.text)
        players = tree.css("div.squad-player-name")
        squad = {f"Player {i}": p.text(strip=True) for i, p in enumerate(players, 1)}
        return jsonify({"status_code": 200, "team": team_slug, "squad": squad})
    except Exception as e:
        return error_payload("Squad Error", str(e), "Try again later.")

# --- Winners ---
@app.route("/ipl-winners")
def ipl_winners():
    return jsonify({"status_code": 200, "winners": WINNERS})

# --- AI Agents ---
def extract_json(text):
    try:
        # Match content between ```json and ``` or between { and }
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        return json.loads(text.strip())
    except Exception:
        raise ValueError("Failed to extract valid JSON from Gemini response")

    except Exception as e:
        logger.error(f"Strategy Error: {e}")
        print(f"DEBUG AI ERROR (Strategy): {e}")
        return jsonify({"strategy": "Stick to basics, keep the pressure!"})

@app.route("/api/commentary", methods=["POST"])
def get_ai_commentary():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify({"commentary": "Agent warming up..."})
    try:
        prompt = f"IPL Live Match Context: {data.get('team_1')} vs {data.get('team_2')}. Score: {data.get('score_1')}. Provide a 2-line witty tactical commentary and a MANIFESTING ticker. Be specific to the match situation."
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        return jsonify({"commentary": response.text.strip()})
    except Exception as e:
        logger.error(f"Commentary Error: {e}")
        print(f"DEBUG AI ERROR (Commentary): {e}")
        return jsonify({"commentary": "The stadium vibe is intense!"})

@app.route("/api/win-probability", methods=["POST"])
def get_win_probability():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify({"team_1_prob": 50, "team_2_prob": 50})
    try:
        prompt = f"Analyze Win Probability: {data.get('team_1')} ({data.get('score_1')}) vs {data.get('team_2')} ({data.get('score_2')}). Return ONLY a JSON object: {{\"team_1_prob\": X, \"team_2_prob\": Y}}"
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        return jsonify(extract_json(response.text))
    except Exception as e:
        logger.error(f"Win Prob Error: {e}")
        print(f"DEBUG AI ERROR (WinProb): {e}")
        return jsonify({"team_1_prob": 50, "team_2_prob": 50})

@app.route("/api/strategy", methods=["POST"])
def get_strategy():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify({"strategy": "Analyzing tactics..."})
    try:
        prompt = f"Match Context: {data.get('team_1')} vs {data.get('team_2')}. Score: {data.get('score_1')}. Give 2 concise bowling tactical suggestions."
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        return jsonify({"strategy": response.text.strip()})
    except Exception as e:
        logger.error(f"Strategy Error: {e}")
        print(f"DEBUG AI ERROR (Strategy): {e}")
        return jsonify({"strategy": "Stick to basics, keep the pressure!"})

@app.route("/api/gamification", methods=["POST"])
def get_gamification():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify({"xp": 100, "level": 1, "badge": "Rookie"})
    try:
        prompt = f"User has {data.get('actions', 0)} actions. Return JSON: {{\"xp\": X, \"level\": Y, \"badge\": \"...\", \"next_milestone\": \"...\"}}"
        response = model.generate_content(prompt)
        return jsonify(extract_json(response.text))
    except Exception as e:
        logger.error(f"Gamification Error: {e}")
        return jsonify({"xp": 100, "level": 1, "badge": "Match Starter"})

@app.route("/api/squad-xi", methods=["POST"])
def get_squad_xi():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify(["MS Dhoni", "Virat Kohli", "Jasprit Bumrah"])
    try:
        prompt = f"Generate Playing XI for {data.get('team_1')}. Max 4 overseas. Return JSON list of strings."
        response = model.generate_content(prompt)
        return jsonify(extract_json(response.text))
    except Exception as e:
        logger.error(f"Squad XI Error: {e}")
        return jsonify(["Virat Kohli (C)", "MS Dhoni (WK)", "Ravindra Jadeja"])

@app.route("/api/team-insights", methods=["POST"])
def get_team_insights():
    data = request.json
    if not data or not GEMINI_API_KEY:
        return jsonify({"insights": "Loading...", "key_player": "Captain"})
    try:
        prompt = f"Analyst for {data.get('team_name')}. 2-line strategic insight and key player. Return JSON."
        response = model.generate_content(prompt)
        return jsonify(extract_json(response.text))
    except Exception as e:
        logger.error(f"Team Insight Error: {e}")
        return jsonify({"insights": "Showing great promise.", "key_player": "Captain"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "season": SEASON})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
