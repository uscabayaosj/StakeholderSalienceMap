# Stakeholder Salience Map

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://stakeholdersaliencemap.streamlit.app)

A **Streamlit** web application for mapping and analysing stakeholders using Mitchell's salience framework (Power, Legitimacy, Urgency). Now with optional **AI-powered insights** via [OpenRouter](https://openrouter.ai/).

## Features

- **Add & manage stakeholders** — score Power, Legitimacy, and Urgency (1–5)
- **Automatic categorisation** — Definitive, Dominant, Dangerous, Dependent, Dormant, Discretionary, Demanding, or Non-salient
- **Interactive bubble map** — visually explore the salience landscape
- **Spider chart** — compare any subset of stakeholders side-by-side
- **Export** — download your data as CSV or Excel
- **AI Insights** — get a quick scan, deep analysis, or strategy suggestions powered by any OpenRouter model

## Quickstart

```bash
# 1. Clone
git clone https://github.com/uscabayaosj/StakeholderSalienceMap.git
cd StakeholderSalienceMap

# 2. Optional: virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies (much leaner than before — only 6 packages)
pip install -r requirements.txt

# 4. (Optional) Set up OpenRouter for AI insights
cp .env.example .env
# Edit .env with your key: https://openrouter.ai/keys

# 5. Run
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

## AI Insights (OpenRouter)

The app can analyse your stakeholder landscape using any model available on OpenRouter. To enable:

1. Get a free API key at https://openrouter.ai/keys
2. Copy `.env.example` → `.env` and paste your key
3. Three modes:
   - **Quick Scan** — 3-paragraph snapshot of risks and attention gaps
   - **Deep Analysis** — 5–6 paragraph theoretical analysis
   - **Strategy Suggestions** — 4–6 actionable recommendations

The default model is `deepseek/deepseek-chat` (fast and free). Change it in `.env` via `OPENROUTER_MODEL` — any OpenRouter model works.

## How It Works

Scores **≥ 3** count as "high". Categories follow Mitchell, Agle & Wood (1997):

| Category | High Attributes | Colour |
|---|---|---|
| **Definitive** | Power + Legitimacy + Urgency | 🔴 Red |
| **Dominant** | Power + Legitimacy | 🟠 Orange |
| **Dangerous** | Power + Urgency | 🟣 Purple |
| **Dependent** | Legitimacy + Urgency | 🟣 Violet |
| **Dormant** | Power only | 🔵 Blue |
| **Discretionary** | Legitimacy only | 🟢 Green |
| **Demanding** | Urgency only | 🟡 Yellow |
| **Non-salient** | None | ⚪ Grey |

## What Changed (v2)

- **OpenRouter AI** replaces any previous OpenAI dependency — zero vendor lock-in
- **60 % fewer dependencies** — from 49 pinned packages down to 6
- **SQLite WAL mode** — faster concurrent reads
- **Smarter caching** — `st.cache_data` with TTL on DB queries and category computation
- **Cleaner UI** — inline delete buttons, toast notifications, consistent spider-chart colours
- **Secure by default** — `.gitignore` covers `.env`, `*.db`, `__pycache__`; credentials removed from repo
- **Dead code removed** — orphaned Express/MongoDB auth files deleted

## Citation

Cabayao, U. (2024). *StakeholderSalienceMap* [Web App]. GitHub. https://github.com/uscabayaosj/StakeholderSalienceMap/

## License

MIT