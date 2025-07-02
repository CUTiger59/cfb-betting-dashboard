# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np

st.title("📈 College Football Betting Edge")

st.markdown("""
This dashboard highlights one historically profitable trend:
- **Unranked home underdogs vs ranked teams**
- Filters: opponent rank tier, weather, conference game
""")

@st.cache_data
def load_data():
    np.random.seed(42)
    df = pd.DataFrame({
        "Opp_Rank": np.random.randint(1, 25, size=300),
        "Conference_Game": np.random.choice([True, False], size=300),
        "Weather": np.random.choice(["Clear", "Rain", "Snow", "Wind"], size=300),
        "Result_ATS": np.random.choice(["Win", "Loss", "Push"], size=300, p=[0.58, 0.38, 0.04]),
        "Spread": np.random.normal(loc=7.5, scale=2.5, size=300)
    })
    df['ATS_Win'] = df['Result_ATS'].map({"Win": 1, "Loss": 0, "Push": 0.5})
    df['Opp_Rank_Tier'] = pd.cut(df['Opp_Rank'], bins=[0, 5, 10, 15, 20, 25],
                                 labels=["Top 5", "Top 10", "Top 15", "Top 20", "Top 25"])
    return df

df = load_data()

# Sidebar filters
rank_filter = st.sidebar.multiselect("Opponent Rank Tier", df['Opp_Rank_Tier'].unique(), default=df['Opp_Rank_Tier'].unique())
conf_filter = st.sidebar.radio("Conference Game?", ["All", True, False])
weather_filter = st.sidebar.multiselect("Weather", df['Weather'].unique(), default=df['Weather'].unique())

# Apply filters
filtered = df[df['Opp_Rank_Tier'].isin(rank_filter)]
if conf_filter != "All":
    filtered = filtered[filtered['Conference_Game'] == conf_filter]
filtered = filtered[filtered['Weather'].isin(weather_filter)]

# Metrics
win_rate = filtered['ATS_Win'].mean()
net_units = filtered['ATS_Win'].sum() * 0.91 - (1 - filtered['ATS_Win']).sum()

st.metric("Filtered ATS Win %", f"{win_rate:.1%}")
st.metric("Estimated Net Units", f"{net_units:.2f}")
st.metric("Sample Size", len(filtered))

st.dataframe(filtered)
