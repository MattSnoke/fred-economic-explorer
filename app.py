import streamlit as st
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go

st.markdown(
    "<style>.block-container { padding-top: 1.5rem; }</style>",
    unsafe_allow_html=True,
)
st.subheader("FRED Economic Data Explorer")

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
fig.add_trace(go.Scatter(x=data_b.index, y=data_b.values, name=series_b_label, yaxis="y2", line=dict(color="#FF8C00")))

fig.update_layout(
    yaxis=dict(title=series_a_name),
    yaxis2=dict(title=series_b_name, overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)
