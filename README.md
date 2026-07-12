# 📊 Retail Sales Analytics Dashboard

An interactive sales analytics dashboard for a (synthetic) Indian retail business —
built to demonstrate the full data analyst workflow: data generation/cleaning, KPI
design, interactive filtering, segment/cohort analysis, and a lightweight forecast.

**🔗 Live demo:** _add your Streamlit Cloud link here after deploying_

---

## What this project demonstrates

| Skill | Where |
|---|---|
| Data modeling / cleaning | `data/generate_data.py` — realistic transaction structure with seasonality |
| KPI design | Total Sales, Profit, Orders, AOV, Margin % cards |
| Interactive filtering | Date range, Region, Category, Segment — all cross-filter every chart |
| Business storytelling | Written insights under each chart, not just raw numbers |
| Segment/cohort analysis | Customer segment, payment mode, top-customer breakdowns |
| Time series analysis | Monthly trend + weekday×category seasonality heatmap |
| Basic forecasting | 3-month linear trend projection (Forecast tab) |
| Dashboard engineering | Streamlit + Plotly, cached data loading, clean dark UI |

## About the dataset

The data is **synthetic but realistically modeled** — 11,000 transactions spanning
2023–2025 across 4 Indian regions, 5 product categories, and 5 payment modes
(UPI, Cards, Net Banking, COD), with real-world seasonality baked in: spikes around
Diwali, the Republic Day sale, and End-of-Season Sale periods, plus a deliberate
"heavy discounts erode margin" pattern for the Products tab to surface. This was a
deliberate choice over reusing the generic Kaggle Superstore dataset that appears in
thousands of portfolios — see `data/generate_data.py` for exactly how it's built,
which is worth walking an interviewer through directly.

## Run it locally

```bash
git clone https://github.com/YOUR_USERNAME/sales-dashboard.git
cd sales-dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dataset (`data/sales_data.csv`) is already generated and committed, so the app
works immediately. To regenerate it (e.g. with a different random seed or bigger
size), run `python data/generate_data.py`.

## Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub
2. Go to https://share.streamlit.io → **New app** → pick the repo, branch `main`,
   file `app.py`
3. Deploy — no secrets/API keys needed, this project is fully self-contained
4. Copy the live `*.streamlit.app` URL into this README and your resume/portfolio

## Project structure

```
sales-dashboard/
├── app.py                  # the dashboard
├── data/
│   ├── generate_data.py    # dataset generation logic (talk through this in interviews)
│   └── sales_data.csv      # the generated dataset (committed)
├── requirements.txt
├── .streamlit/config.toml  # dark theme
└── README.md
```

## Ideas to extend further

- Swap the linear-trend forecast for Prophet or SARIMA with proper seasonality decomposition
- Add a customer RFM (Recency/Frequency/Monetary) segmentation tab
- Add a cohort retention analysis (repeat purchase rate by signup month)
- Connect to a real database (Postgres/BigQuery) instead of a static CSV, and add
  `st.cache_data(ttl=...)` for live-refreshing data
- Add anomaly detection on daily sales (flag unusual spikes/drops automatically)

---

### Talking points for interviews

- **"Walk me through your process"** → data generation → cleaning/typing → KPI
  definition → chart selection reasoning → insight writing.
- **"Why these charts?"** → line chart for trend (time-series), heatmap for two
  categorical dimensions (weekday × category), pie only for share-of-whole with few
  categories (region), bar for ranked comparisons (top products).
- **"What would you do with more time?"** → point to the "Ideas to extend" section
  above — shows you know the limits of what you built and where real production
  work would go next.
