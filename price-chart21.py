import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import re
from datetime import datetime, timedelta

# --- Load Config and Labels ---
with open("global_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

default_language = config.get("default_language", "English")
lang_map = {"English": "en", "Tamil": "ta", "Hindi": "hi", "Japanese": "ja"}
lang_key = lang_map.get(default_language, "en")

with open("labels.json", "r", encoding="utf-8") as f:
    labels = json.load(f)

L = labels.get(lang_key, labels["en"])

# --- Column Mapping ---
def normalize_col(col):
    col = str(col).strip()
    col = re.sub(r'\.+', '', col)
    col = re.sub(r'\s+', '_', col)
    return col.upper()

def match_columns(df_cols, alias_map):
    matched = {}
    for std, aliases in alias_map.items():
        for col in df_cols:
            if col.upper() in [a.upper() for a in aliases]:
                matched[std] = col
                break
    return matched

alias_map = {
    'DATE': ['DATE'],
    'OPEN': ['OPEN', 'OPEN_PRICE'],
    'HIGH': ['HIGH', 'HIGH_PRICE'],
    'LOW': ['LOW', 'LOW_PRICE'],
    'CLOSE': ['CLOSE', 'CLOSE_PRICE']
}

def load_csv(file, fallback):
    if file:
        return pd.read_csv(file)
    try:
        return pd.read_csv(fallback)
    except:
        return None

def prepare_df(df):
    if df is None:
        return None
    df.columns = [normalize_col(c) for c in df.columns]
    df = df.dropna()
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['DATE'])

# --- Streamlit Layout ---
st.set_page_config(layout="wide")
st.title(L["page_title"])

st.sidebar.header("🧩 " + L["page_title"])
nifty_file = st.sidebar.file_uploader("📈 " + L["upload_nifty"], type=["csv"])
user_file = st.sidebar.file_uploader("📉 " + L["upload_stock"], type=["csv"])
#notes_file = st.sidebar.file_uploader("🗒️ " + L["upload_notes"], type=["csv"])
notes_file = st.sidebar.file_uploader("🗒️ " + L["upload_notes"], type=["csv"]) or "REMARKS.csv"
show_notes = st.sidebar.checkbox("📌 " + L["show_notes"], value=True)

chart_title = st.sidebar.text_input(L["chart_title"], L["chart_title"])
chart_subtitle = st.sidebar.text_input(L["chart_subtitle"], L["chart_subtitle"])
nifty_label = st.sidebar.text_input(L["legend_nifty"], L["legend_nifty"])
user_label = st.sidebar.text_input(L["legend_stock"], L["legend_stock"])
chart_type = st.sidebar.radio("📊 Chart Style", ["Line", "Candlestick", "OHLC"])

# --- Load Data with Fallbacks ---
df_nifty = prepare_df(load_csv(nifty_file, "NIFTYBANK.csv"))
df_user = prepare_df(load_csv(user_file, "STOCK.csv"))


# --- Time Range Setup ---
combined_dates = pd.concat([df['DATE'] for df in [df_user, df_nifty] if df is not None])
if not combined_dates.empty:
    min_date = combined_dates.min().date()
    max_date = combined_dates.max().date()

    st.sidebar.markdown("---")
    st.sidebar.header("⏳ " + L["preset"])
    preset = st.sidebar.selectbox("📆 " + L["preset"], ["Full Range", "Last 3 Months", "Year to Date"])

    today = max_date
    start = min_date
    if preset == "Last 3 Months":
        start = today - timedelta(days=90)
    elif preset == "Year to Date":
        start = datetime(today.year, 1, 1).date()

    date_range = st.slider(L["slider_label"], min_date, max_date, (start, today), format="YYYY-MM-DD")

    if df_user is not None:
        df_user = df_user[(df_user['DATE'].dt.date >= date_range[0]) & (df_user['DATE'].dt.date <= date_range[1])]
    if df_nifty is not None:
        df_nifty = df_nifty[(df_nifty['DATE'].dt.date >= date_range[0]) & (df_nifty['DATE'].dt.date <= date_range[1])]

# --- Plot Setup ---
fig = go.Figure()
has_data = False

def plot_series(df, label, axis, style):
    global has_data
    if df is None or df.empty:
        return
    matched = match_columns(df.columns.tolist(), alias_map)
    if all(k in matched for k in ['DATE', 'CLOSE']):
        df.rename(columns={matched['CLOSE']: 'CLOSE'}, inplace=True)
        if style == "Line":
            fig.add_trace(go.Scatter(x=df['DATE'], y=df['CLOSE'], mode='lines+markers', name=label, yaxis=axis))
        elif style == "Candlestick" and all(k in matched for k in ['OPEN', 'HIGH', 'LOW']):
            fig.add_trace(go.Candlestick(
                x=df['DATE'],
                open=df[matched['OPEN']], high=df[matched['HIGH']],
                low=df[matched['LOW']], close=df['CLOSE'],
                name=label,
                yaxis=axis
            ))
        elif style == "OHLC" and all(k in matched for k in ['OPEN', 'HIGH', 'LOW']):
            fig.add_trace(go.Ohlc(
                x=df['DATE'],
                open=df[matched['OPEN']], high=df[matched['HIGH']],
                low=df[matched['LOW']], close=df['CLOSE'],
                name=label,
                yaxis=axis
            ))
        has_data = True

plot_series(df_user, user_label, 'y1', chart_type)
plot_series(df_nifty, nifty_label, 'y2', chart_type)

# --- Notes File Integration ---
notes_list = []
if notes_file:
    try:
        notes_df = pd.read_csv(notes_file)
        notes_df.columns = [normalize_col(c) for c in notes_df.columns]
        if 'DATE' in notes_df.columns and 'COMMENT' in notes_df.columns:
            notes_df['DATE'] = pd.to_datetime(notes_df['DATE'], errors='coerce')
            notes_df = notes_df.dropna(subset=['DATE'])
            notes_df = notes_df[(notes_df['DATE'].dt.date >= date_range[0]) & (notes_df['DATE'].dt.date <= date_range[1])]

            if show_notes:
                for _, row in notes_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row['DATE']], y=[None],
                        mode='markers',
                        marker=dict(size=10, color='orange', symbol='circle'),
                        name='Note',
                        hoverinfo='text',
                        hovertext=row['COMMENT']
                    ))

            notes_list = [f"{d.date()}: {c}" for d, c in zip(notes_df['DATE'], notes_df['COMMENT'])]
        else:
            st.warning("⚠️ Notes file must contain 'Date' and 'Comment' columns.")
    except Exception as e:
        st.error(f"Error reading notes file: {e}")

# --- Chart Rendering ---
if has_data:
    fig.update_layout(
        title={'text': f"<b>{chart_title}</b><br><sub>{chart_subtitle}</sub>", 'x': 0.5},
        xaxis=dict(title="Date"),
        yaxis=dict(title=f"{user_label} (₹)", side="left"),
        yaxis2=dict(title=f"{nifty_label} (₹)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.2),
        height=750
    )
    st.plotly_chart(fig, use_container_width=True)

    if show_notes:
        st.markdown("### 📝 " + L["notes_summary"])
        st.text_area(
            L["annotation_text"],
            value="\n".join(notes_list) if notes_list else f"({L['annotation_text']}...)",
            height=160,
            disabled=True
        )
else:
    st.info("📤 Upload valid CSVs or place default files (NIFTYBANK.csv, STOCK.csv) to get started.")
