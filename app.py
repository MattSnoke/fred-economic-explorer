import streamlit as st
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go

st.title("FRED Economic Data Explorer")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

SERIES = {
    "Unemployment Rate": "UNRATE",
    "Inflation (CPI)": "CPIAUCSL",
    "Federal Funds Rate": "FEDFUNDS",
    "10-Year Treasury Yield": "GS10",
    "GDP": "GDP",
    "Nonfarm Payrolls": "PAYEMS",
    "Consumer Sentiment": "UMCSENT",
    "Personal Savings Rate": "PSAVERT",
}

ELECTIONS = [
    ("1952-11-04", "R"), ("1956-11-06", "R"), ("1960-11-08", "D"),
    ("1964-11-03", "D"), ("1968-11-05", "R"), ("1972-11-07", "R"),
    ("1976-11-02", "D"), ("1980-11-04", "R"), ("1984-11-06", "R"),
    ("1988-11-08", "R"), ("1992-11-03", "D"), ("1996-11-05", "D"),
    ("2000-11-07", "R"), ("2004-11-02", "R"), ("2008-11-04", "D"),
    ("2012-11-06", "D"), ("2016-11-08", "R"), ("2020-11-03", "D"),
    ("2024-11-05", "R"),
]
PARTY_COLOR = {"R": "red", "D": "blue"}
PARTY_LABEL = {"R": "Republican win", "D": "Democrat win"}

col1, col2 = st.columns(2)
with col1:
    series_a_name = st.selectbox("First series", list(SERIES.keys()), index=0)
with col2:
    series_b_name = st.selectbox("Second series", list(SERIES.keys()), index=2)

shift_months = st.number_input(
    f"Shift '{series_b_name}' by this many months",
    min_value=-60,
    max_value=60,
    value=0,
    step=1,
    help="Positive shifts the series later in time (e.g. +3 tests whether it lags the first series by 3 months). Negative shifts it earlier.",
)

ten_years_ago = pd.Timestamp.today() - pd.DateOffset(years=10)
start_date, end_date = st.slider(
    "Date range",
    min_value=pd.Timestamp("1950-01-01").to_pydatetime(),
    max_value=pd.Timestamp.today().to_pydatetime(),
    value=(ten_years_ago.to_pydatetime(), pd.Timestamp.today().to_pydatetime()),
)

show_elections = st.checkbox("Overlay presidential elections")

data_a = fred.get_series(SERIES[series_a_name], start_date, end_date)

# Fetch a wider window for series B so shifting it doesn't leave empty gaps at the edges
buffer = pd.DateOffset(months=abs(shift_months))
data_b = fred.get_series(SERIES[series_b_name], start_date - buffer, end_date + buffer)
data_b.index = data_b.index + pd.DateOffset(months=shift_months)
data_b = data_b[(data_b.index >= start_date) & (data_b.index <= end_date)]

series_b_label = series_b_name
if shift_months != 0:
    direction = "later" if shift_months > 0 else "earlier"
    series_b_label = f"{series_b_name} (shifted {abs(shift_months)} mo. {direction})"

fig = go.Figure()
fig.add_trace(go.Scatter(x=data_a.index, y=data_a.values, name=series_a_name, yaxis="y1"))
fig.add_trace(go.Scatter(x=data_b.index, y=data_b.values, name=series_b_label, yaxis="y2"))

fig.update_layout(
    yaxis=dict(title=series_a_name),
    yaxis2=dict(title=series_b_name, overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

if show_elections:
    shown_parties = set()
    for date_str, party in ELECTIONS:
        election_date = pd.Timestamp(date_str)
        if start_date <= election_date <= end_date:
            fig.add_vline(
                x=election_date,
                line_color=PARTY_COLOR[party],
                line_width=2,
                opacity=0.5,
            )
            shown_parties.add(party)
    # Dummy traces so the election colors get a legend entry (vlines don't have one natively)
    for party in shown_parties:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            line=dict(color=PARTY_COLOR[party], width=2),
            name=PARTY_LABEL[party],
        ))

st.plotly_chart(fig, use_container_width=True)
