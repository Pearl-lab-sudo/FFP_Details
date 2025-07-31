import streamlit as st
import pandas as pd
import json
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# ------------------------
# Load Environment Variables
# ------------------------
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# ------------------------
# Connect to PostgreSQL
# ------------------------
def load_data():
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM financial_simulator_v2", engine)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

# ------------------------
# Parse Metadata (Name + Q&A)
# ------------------------
def parse_metadata(metadata_value):
    try:
        if isinstance(metadata_value, str):
            data = json.loads(metadata_value)
        elif isinstance(metadata_value, dict):
            data = metadata_value
        else:
            return "N/A", []

        plan = data.get("plan", [])
        qa_pairs = [(item.get("question", "N/A"), item.get("answer", "N/A")) for item in plan if isinstance(item, dict)]
        name = next((item.get("answer") for item in plan if item.get("question") == "What's your full name"), "N/A")
        return name, qa_pairs
    except Exception:
        return "N/A", []

# ------------------------
# Streamlit Page Config
# ------------------------
st.set_page_config(page_title="FFP Responses", layout="wide")
st.title("📋 FFP Responses Viewer")
st.markdown("Browse submitted Free Financial Plan responses with filters and exports.")

# ------------------------
# Load & Process Data
# ------------------------
df = load_data()
df["name"], df["qa_pairs"] = zip(*df["metadata"].map(parse_metadata))

# ------------------------
# Date Range Filter
# ------------------------
st.sidebar.header("📅 Filter by Date")
min_date = df["created_at"].min().date()
max_date = df["created_at"].max().date()
start_date, end_date = st.sidebar.date_input("Select date range:", [min_date, max_date])

filtered_df = df[(df["created_at"].dt.date >= start_date) & (df["created_at"].dt.date <= end_date)]

# ------------------------
# Search Filter
# ------------------------
search_term = st.sidebar.text_input("🔍 Search by name or ID")
if search_term:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search_term, case=False, na=False) |
        filtered_df["id"].astype(str).str.contains(search_term)
    ]

# ------------------------
# Summary Info
# ------------------------
st.markdown(f"### Total Respondents: **{len(filtered_df)}**")
st.download_button("⬇ Download CSV", data=filtered_df.to_csv(index=False), file_name="ffp_responses.csv", mime="text/csv")

# ------------------------
# Display Results
# ------------------------
st.subheader("👥 Respondents")

for idx, row in filtered_df.iterrows():
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        with st.expander(f"{row['name']} — ID: {row['id']}"):
            st.markdown(f"**User ID:** `{row['id']}`")
            st.markdown(f"**Date Submitted:** {row['created_at'].strftime('%Y-%m-%d %H:%M')}")
            st.markdown("### Responses:")
            for q, a in row["qa_pairs"]:
                st.markdown(f"**Q:** {q}\n\n- **A:** {a if a else 'N/A'}")
    with col2:
        st.markdown(" ")
        st.markdown(" ")
        ffp_link = f"http://ladder.africa/ffp/results?id={row['id']}"
        st.markdown(
            f'<a href="{ffp_link}" target="_blank"><button style="background-color:#4CAF50;color:white;border:none;padding:10px;border-radius:5px;">View Page</button></a>',
            unsafe_allow_html=True
        )
