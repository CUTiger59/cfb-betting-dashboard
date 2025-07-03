# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ------------------------- CONFIG ----------------------------
API_KEY = "+d4ZJfjl/2sE0v10T+AuY+A+3MzSQHk3i4QRUj+WDppPbpIpyymZi3xK9L1JiFP3"
ODDS_API_KEY = "5b348e3a3cbe99df17bd82b117a03b93"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# ------------------------- TITLE -----------------------------
st.title("📈 College Football Betting Edge Dashboard")

st.markdown("""
This dashboard highlights high-EV betting trends:
- **Unranked home underdogs vs ranked opponents**
- **Non-Power 5 teams at home vs Power 5 teams**
- **Teams after a bye week**
- Filters for opponent rank, weather, and conference status
- Real-time data pulled from CollegeFootballData.com and live odds from The Odds API
""")

# -------------------- API FUNCTIONS --------------------------
@st.cache_data
def get_upcoming_games(year=2025, week=1):
    url = "https://api.collegefootballdata.com/games"
    params = {"year": year, "seasonType": "regular", "week": week}
    r = requests.get(url, headers=HEADERS, params=params)
    return pd.DataFrame(r.json())

@st.cache_data
def get_rankings():
    url = "https://api.collegefootballdata.com/rankings"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    latest_week = max(d['week'] for d in data)
    latest_poll = [d for d in data if d['week'] == latest_week and d['poll'] == 'AP Top 25']
    if not latest_poll:
        return pd.DataFrame()
    ranks = latest_poll[0]['ranks']
    return pd.DataFrame(ranks)

@st.cache_data
def get_team_info():
    url = "https://api.collegefootballdata.com/teams/fbs"
    r = requests.get(url, headers=HEADERS)
    return pd.DataFrame(r.json())

@st.cache_data
def get_live_odds():
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_ncaaf/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american"
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return pd.DataFrame()
    odds_data = r.json()
    rows = []
    for game in odds_data:
        home = game.get("home_team")
        away = game.get("away_team")
        commence = game.get("commence_time")
        bookmaker = game.get("bookmakers", [{}])[0]
        spreads, totals, h2h = None, None, None
        for market in bookmaker.get("markets", []):
            if market["key"] == "spreads":
                spreads = market["outcomes"]
            elif market["key"] == "totals":
                totals = market["outcomes"]
            elif market["key"] == "h2h":
                h2h = market["outcomes"]
        row = {
            "home_team": home,
            "away_team": away,
            "start_date": commence,
            "home_spread": None,
            "away_spread": None,
            "total_points": None,
            "home_ml": None,
            "away_ml": None
        }
        if spreads:
            for s in spreads:
                if s["name"] == home:
                    row["home_spread"] = s.get("point")
                elif s["name"] == away:
                    row["away_spread"] = s.get("point")
        if totals:
            row["total_points"] = totals[0].get("point")
        if h2h:
            for h in h2h:
                if h["name"] == home:
                    row["home_ml"] = h.get("price")
                elif h["name"] == away:
                    row["away_ml"] = h.get("price")
        rows.append(row)
    return pd.DataFrame(rows)

# ------------------ PROCESS & MERGE --------------------------
@st.cache_data
def process_trends(games_df, rankings_df, teams_df, odds_df):
    if games_df.empty or rankings_df.empty or teams_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    ranked_teams = set(rankings_df['school'])
    power5_confs = {"ACC", "Big Ten", "Big 12", "Pac-12", "SEC"}
    conf_map = teams_df.set_index('school')['conference'].to_dict()

    games_df['is_home_ranked'] = games_df['home_team'].isin(ranked_teams)
    games_df['is_away_ranked'] = games_df['away_team'].isin(ranked_teams)
    games_df['home_conf'] = games_df['home_team'].map(conf_map)
    games_df['away_conf'] = games_df['away_team'].map(conf_map)

    games_df['home_power5'] = games_df['home_conf'].isin(power5_confs)
    games_df['away_power5'] = games_df['away_conf'].isin(power5_confs)
    games_df['year'] = pd.to_datetime(games_df['start_date']).dt.year

    if not odds_df.empty:
        odds_df['start_date'] = pd.to_datetime(odds_df['start_date'])
        games_df['start_date'] = pd.to_datetime(games_df['start_date'])
        games_df = pd.merge(games_df, odds_df, on=['home_team', 'away_team', 'start_date'], how='left')

    games_df['highlight'] = (games_df['home_spread'] > 6) & (~games_df['is_home_ranked']) & (games_df['is_away_ranked'])

    trend1 = games_df[(games_df['is_away_ranked']) & (~games_df['is_home_ranked']) & (games_df['home_team'].notna())]
    trend2 = games_df[(~games_df['home_power5']) & (games_df['away_power5'])]
    trend3 = games_df[games_df['home_team_rest'] > 13] if 'home_team_rest' in games_df.columns else pd.DataFrame()
    best_plays = games_df[games_df['highlight']]

    return trend1, trend2, trend3, best_plays

# ---------------------- LOAD DATA ----------------------------
st.sidebar.header("🧮 Filter Settings")
year = st.sidebar.slider("Season Year", min_value=2020, max_value=2025, value=2025)
week = st.sidebar.slider("Week #", min_value=1, max_value=15, value=1)
year_filter = st.sidebar.selectbox("Show games from last...", options=[1, 2, 3, 5, 10], index=0)

with st.spinner("Fetching data..."):
    games = get_upcoming_games(year=year, week=week)
    rankings = get_rankings()
    teams = get_team_info()
    odds = get_live_odds()
    trend1, trend2, trend3, best_plays = process_trends(games, rankings, teams, odds)

    current_year = datetime.now().year
    trend1 = trend1[trend1['year'] >= (current_year - year_filter)]
    trend2 = trend2[trend2['year'] >= (current_year - year_filter)]
    best_plays = best_plays[best_plays['year'] >= (current_year - year_filter)]
    if not trend3.empty:
        trend3 = trend3[trend3['year'] >= (current_year - year_filter)]

# ----------------------- DISPLAY -----------------------------
st.subheader("⭐ Best Opportunities This Week")
if not best_plays.empty:
    st.dataframe(best_plays[['year', 'home_team', 'away_team', 'home_spread', 'total_points', 'home_ml', 'away_ml', 'start_date']])
else:
    st.info("No high-EV games found this week based on model criteria.")

st.subheader("📊 Trend 1: Unranked Home Dogs vs Ranked Teams")
if not trend1.empty:
    st.dataframe(trend1[['year', 'home_team', 'away_team', 'start_date', 'venue', 'conference_game', 'home_spread', 'total_points']])
    st.success(f"{len(trend1)} games found.")
else:
    st.info("No matches found.")

st.subheader("📊 Trend 2: Group of 5 Teams Hosting Power 5 Teams")
if not trend2.empty:
    st.dataframe(trend2[['year', 'home_team', 'away_team', 'start_date', 'venue', 'conference_game', 'home_spread', 'total_points']])
    st.success(f"{len(trend2)} games found.")
else:
    st.info("No matches found.")

st.subheader("📊 Trend 3: Teams Coming Off a Bye Week (Home Only)")
if not trend3.empty:
    st.dataframe(trend3[['year', 'home_team', 'away_team', 'start_date', 'venue', 'conference_game']])
    st.success(f"{len(trend3)} games found.")
else:
    st.info("No matches found.")

st.markdown("---")
st.caption("Live data from [CollegeFootballData.com](https://collegefootballdata.com) and odds from [The Odds API](https://the-odds-api.com).")
