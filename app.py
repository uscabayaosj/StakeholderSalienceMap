"""
Stakeholder Salience Map App
─────────────────────────────
Streamlit-powered visualisation of Mitchell's stakeholder salience framework
(Power, Legitimacy, Urgency) with optional AI insights via OpenRouter.
"""

from __future__ import annotations

import os
import sqlite3
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()  # only reads .env; never overrides existing env vars

st.set_page_config(
    page_title="Stakeholder Salience Map",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Stakeholder Salience Map")
st.markdown(
    "Map and analyse your stakeholders by **Power**, **Legitimacy**, and **Urgency** "
    "(Mitchell, Agle & Wood 1997)."
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "stakeholders.db"
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")

SALIENCE_CATEGORIES = {
    "Definitive": {"color": "#e74c3c", "desc": "High Power + Legitimacy + Urgency"},
    "Dominant": {"color": "#e67e22", "desc": "High Power + Legitimacy"},
    "Dangerous": {"color": "#8e44ad", "desc": "High Power + Urgency"},
    "Dependent": {"color": "#9b59b6", "desc": "High Legitimacy + Urgency"},
    "Dormant": {"color": "#3498db", "desc": "High Power only"},
    "Discretionary": {"color": "#2ecc71", "desc": "High Legitimacy only"},
    "Demanding": {"color": "#f1c40f", "desc": "High Urgency only"},
    "Non-salient": {"color": "#95a5a6", "desc": "None high"},
}

THRESHOLD = 3  # score >= 3  → "high"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """Return a singleton connection with WAL mode for concurrent-read speed."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power INTEGER NOT NULL CHECK(power BETWEEN 1 AND 5),
            legitimacy INTEGER NOT NULL CHECK(legitimacy BETWEEN 1 AND 5),
            urgency INTEGER NOT NULL CHECK(urgency BETWEEN 1 AND 5)
        )"""
    )
    conn.commit()


@st.cache_data(ttl=2)  # short TTL so new entries appear quickly
def load_stakeholders() -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query(
        "SELECT id, name, power, legitimacy, urgency FROM stakeholders ORDER BY id",
        conn,
    )


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------

def categorize_salience(row: pd.Series) -> str:
    """Classify a stakeholder per Mitchell's framework."""
    high = {"power": row["power"] >= THRESHOLD,
            "legitimacy": row["legitimacy"] >= THRESHOLD,
            "urgency": row["urgency"] >= THRESHOLD}
    h = sum(high.values())
    if h == 3:
        return "Definitive"
    if h == 2:
        if high["power"] and high["legitimacy"]:
            return "Dominant"
        if high["power"] and high["urgency"]:
            return "Dangerous"
        return "Dependent"
    if h == 1:
        if high["power"]:
            return "Dormant"
        if high["legitimacy"]:
            return "Discretionary"
        return "Demanding"
    return "Non-salient"


@st.cache_data(ttl=2)
def enrich_with_salience(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Ensure numeric types for plotly compatibility
    for col in ["power", "legitimacy", "urgency"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(1).astype(int)
    df["Salience"] = df.apply(categorize_salience, axis=1)
    df["Color"] = df["Salience"].map(
        {k: v["color"] for k, v in SALIENCE_CATEGORIES.items()}
    )
    return df


# ---------------------------------------------------------------------------
# Alert helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    st.toast(f"✅ {msg}", icon="✅")


def _err(msg: str) -> None:
    st.error(f"⚠️ {msg}")


# ---------------------------------------------------------------------------
# Sidebar — add stakeholder
# ---------------------------------------------------------------------------

st.sidebar.header("➕ Add a Stakeholder")
with st.sidebar.form("add_stakeholder_form", clear_on_submit=True):
    name_input = st.text_input("Stakeholder Name")
    power = st.slider("Power", 1, 5, 3, help="Ability to influence outcomes")
    legitimacy = st.slider("Legitimacy", 1, 5, 3, help="Perceived validity of claim")
    urgency = st.slider("Urgency", 1, 5, 3, help="Time-sensitivity of claim")
    if st.form_submit_button("Add Stakeholder", width="stretch"):
        name = name_input.strip()
        if not name:
            _err("Please enter a valid stakeholder name.")
        else:
            conn = get_connection()
            conn.execute(
                "INSERT INTO stakeholders (name, power, legitimacy, urgency) VALUES (?, ?, ?, ?)",
                (name, power, legitimacy, urgency),
            )
            conn.commit()
            st.cache_data.clear()
            _ok(f"**{name}** added!")
            st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.header("📋 Stakeholders")

df = load_stakeholders()

if df.empty:
    st.info("ℹ️ No stakeholders yet. Add some from the sidebar.")
    st.stop()

# ── List with inline deletion ──────────────────────────────────────────────
st.markdown("""<style>.stakeholder-card{padding:0.6rem 1rem;margin-bottom:0.5rem;
border-radius:10px;background:#f0f2f6;display:flex;align-items:center;gap:1.5rem;}
.stakeholder-card strong{font-size:1.05rem;}</style>""",
            unsafe_allow_html=True,)

for _, row in df.iterrows():
    cols = st.columns([3, 3, 1])
    cols[0].markdown(
        f"<div class='stakeholder-card'><strong>{row['name']}</strong> "
        f"⚡{row['power']}  🏛️{row['legitimacy']}  ⏱{row['urgency']}</div>",
        unsafe_allow_html=True,
    )
    if cols[2].button("🗑️", key=f"del_{row['id']}", help="Delete stakeholder"):
        conn = get_connection()
        conn.execute("DELETE FROM stakeholders WHERE id = ?", (int(row["id"]),))
        conn.commit()
        st.cache_data.clear()
        st.rerun()

# ── Enrich ─────────────────────────────────────────────────────────────────
df = enrich_with_salience(df)

# ── Export  ─────────────────────────────────────────────────────────────────
st.markdown("### 📥 Export")
ec1, ec2 = st.columns(2)
ec1.download_button("📄 CSV", df.to_csv(index=False).encode("utf-8"),
                     "stakeholders.csv", "text/csv", width="stretch")
buf = BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="Stakeholders")
ec2.download_button("📑 Excel", buf.getvalue(), "stakeholders.xlsx",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     width="stretch")

# ── Category table ──────────────────────────────────────────────────────────
st.header("🗂️ Salience Categories")
st.dataframe(
    df[["name", "power", "legitimacy", "urgency", "Salience"]],
    width="stretch",
    hide_index=True,
)

# ── Bubble map  ─────────────────────────────────────────────────────────────
st.header("📈 Salience Map")
color_map = {k: v["color"] for k, v in SALIENCE_CATEGORIES.items()}

fig = px.scatter(
    df,
    x="power",
    y="legitimacy",
    size="urgency",
    color="Salience",
    hover_name="name",
    hover_data={"power": True, "legitimacy": True, "urgency": True, "Salience": False},
    size_max=30,
    color_discrete_map=color_map,
    labels={"power": "Power", "legitimacy": "Legitimacy"},
    title="🗺️ Stakeholder Salience Map",
)
fig.update_layout(
    xaxis=dict(tickmode="linear", dtick=1, range=[0.5, 5.5]),
    yaxis=dict(tickmode="linear", dtick=1, range=[0.5, 5.5]),
    legend_title="Salience",
    margin=dict(l=20, r=20, t=40, b=20),
)
st.plotly_chart(fig, width="stretch")

# ── Spider chart  ───────────────────────────────────────────────────────────
st.header("🕸️ Compare Stakeholders")
selected = st.multiselect(
    "Select stakeholders to compare:",
    options=df["name"].tolist(),
    default=df["name"].tolist()[: min(5, len(df))],
)

if selected:
    sdf = df[df["name"].isin(selected)]
    fig2 = go.Figure()
    for _, row in sdf.iterrows():
        fig2.add_trace(go.Scatterpolar(
            r=[row["power"], row["legitimacy"], row["urgency"], row["power"]],
            theta=["Power", "Legitimacy", "Urgency", "Power"],
            fill="toself",
            name=row["name"],
            line_color=row["Color"],
        ))
    fig2.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=True,
        title="Stakeholder Comparison",
        margin=dict(l=60, r=60, t=40, b=40),
    )
    st.plotly_chart(fig2, width="stretch")
else:
    st.info("Select at least one stakeholder to see the spider chart.")

# ---------------------------------------------------------------------------
# ✨ AI-Powered Insights (OpenRouter)
# ---------------------------------------------------------------------------

st.markdown("---")
st.header("🤖 AI-Powered Insights")

if not OPENROUTER_API_KEY:
    st.warning(
        "Set `OPENROUTER_API_KEY` in `.env` to unlock AI analysis of your "
        "stakeholder landscape."
    )
else:
    col_left, col_right = st.columns([1, 3])
    insight_mode = col_left.radio(
        "Analysis type",
        ["Quick Scan", "Deep Analysis", "Strategy Suggestions"],
        label_visibility="collapsed",
    )

    # Analyse only when the user clicks the button (avoids wasting API calls)
    st.session_state.setdefault("insight_run", False)

    if col_right.button("🔍 Generate Insights", type="primary", width="stretch"):
        st.session_state.insight_run = True

    if st.session_state.insight_run:
        _total = len(df)
        _definitive = (df["Salience"] == "Definitive").sum()
        _dominant = (df["Salience"] == "Dominant").sum()
        _dangerous = (df["Salience"] == "Dangerous").sum()
        _dependent = (df["Salience"] == "Dependent").sum()
        _non_salient = (df["Salience"] == "Non-salient").sum()

        prompt_context = f"""
We have {_total} stakeholders with the following salience distribution:
- Definitive (high P+L+U): {_definitive}
- Dominant (high P+L): {_dominant}
- Dangerous (high P+U): {_dangerous}
- Dependent (high L+U): {_dependent}
- Non-salient (low all): {_non_salient}
- Others: {_total - _definitive - _dominant - _dangerous - _dependent - _non_salient}

Stakeholder data (name | power | legitimacy | urgency | category):
"""
        for _, r in df.iterrows():
            prompt_context += f"- {r['name']} | {r['power']} | {r['legitimacy']} | {r['urgency']} | {r['Salience']}\n"

        if insight_mode == "Quick Scan":
            prompt = f"""You are a project-management analyst. Based on this stakeholder data{prompt_context}
Provide a concise 3-4 paragraph scan: (1) overall risk of stakeholder fragmentation, (2) which stakeholders need the most attention, (3) any imbalance between Power, Legitimacy, and Urgency scores."""
        elif insight_mode == "Deep Analysis":
            prompt = f"""You are an expert in stakeholder theory (Mitchell, Agle & Wood). Based on this data{prompt_context}
Provide a thorough 5-6 paragraph analysis covering: (1) overall salience profile and what it reveals about the project environment, (2) potential coalitions and conflicting stakeholders, (3) stakeholders at risk of disengagement, (4) legitimacy gaps, (5) urgency-driven risks."""
        else:  # Strategy Suggestions
            prompt = f"""You are a senior project strategist. Based on this stakeholder data{prompt_context}
Provide 4-6 actionable strategy recommendations: (1) top priority stakeholders to engage, (2) communication approach for each category, (3) risk mitigation for dangerous/dependent stakeholders, (4) how to increase legitimacy for marginalised groups, (5) quick wins."""

        with st.spinner("Thinking …"):
            try:
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=OPENROUTER_API_KEY,
                )
                response = client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful project-management analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                )
                insight = response.choices[0].message.content

                st.success("Analysis complete")
                for para in insight.strip().split("\n\n"):
                    st.markdown(para)

                # Show model used
                model_used = getattr(response, "model", OPENROUTER_MODEL)
                st.caption(f"Model: `{model_used}`")

            except Exception as e:
                _err(f"AI analysis failed: {e}")
                st.session_state.insight_run = False

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    "© 2024 AnthroInsight.  "
    "Cabayao, U. (2024). *StakeholderSalienceMap* [Web App]. "
    "GitHub. https://github.com/uscabayaosj/StakeholderSalienceMap/",
    unsafe_allow_html=True,
)