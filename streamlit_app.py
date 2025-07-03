import streamlit as st
import pandas as pd
import requests

# API keys
API_KEY = "+d4ZJfjl/2sE0v10T+AuY+A+3MzSQHk3i4QRUj+WDppPbpIpyymZi3xK9L1JiFP3"
ODDS_API_KEY = "5b348e3a3cbe99df17bd82b117a03b93"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

st.title("📈 College Football Betting Dashboard Test")

# ---- Step 1: Get upcoming games ----
st.write("⏳ Fetching upcoming games...")

try:
    url = "https://api.collegefootballdata.com/games"
    params = {"year": 2025, "seasonType": "regular", "week": 1}
    r = requests.get(url, headers=HEADERS, params=params)
    games = pd.DataFrame(r.json())
    st.success(f"✅ Loaded {len(games)} games")
    st.dataframe(games[['home_team', 'away_team', 'start_date']].head())
except Exception as e:
    st.error(f"❌ Failed to load CFBD games: {e}")

# ---- Step 2: Get betting odds ----
st.write("⏳ Fetching odds data...")

try:
    odds_url = "https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds"
    odds_params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american"
    }
    r2 = requests.get(odds_url, params=odds_params)
    odds = pd.DataFrame(r2.json())
    st.success(f"✅ Loaded odds for {len(odds)} games")
    st.dataframe(odds.head())
except Exception as e:
    st.error(f"❌ Failed to load odds: {e}")
