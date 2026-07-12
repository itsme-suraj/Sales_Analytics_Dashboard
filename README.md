# 📊 Retail Sales Analytics Dashboard

An interactive sales analytics dashboard that accepts **your own CSV or Excel
sales data** (auto-detects columns) or falls back to a realistic synthetic
demo dataset. Built to demonstrate the full data analyst workflow: data
cleaning, KPI design, interactive filtering, segment analysis, and forecasting.

**🔗 Live demo:** _add your Streamlit Cloud link here after deploying_

---

## What this project demonstrates

| Skill | Where |
|---|---|
| Data ingestion from real files | CSV/Excel upload with `pd.read_csv` / `pd.read_excel` |
| Data cleaning at scale | Currency-symbol stripping, mixed date-format parsing, missing-value handling |
| Schema flexibility | Auto-detects columns by name (e.g. "Total Amount" → Sales) so it works on *any* sales file, not just one dataset |
| KPI design | Total Sales, Profit, Orders, AOV, Margin % — computed conditionally based on what's available |
| Interactive filtering | Date range, Region, Category, Segment — all cross-filter every chart |
| Business storytelling | Written insights under each chart, not just raw numbers |
| Time series analysis | Monthly trend + weekday×category seasonality heatmap |
| Basic forecasting | 3-month linear trend projection |
| Dashboard engineering | Streamlit + Plotly, cached data loading, clean dark UI |

## How the upload feature works

1. Upload a `.csv` or `.xlsx` file with sales data (any column names)
2. The app guesses which of your columns are Date, Sales, Profit, Category,
   Region, Customer, etc. by matching common naming patterns
3. You confirm or correct the mapping in the sidebar, then click **"Apply
   mapping & analyze"**
4. Only **Date** and **Sales** are required — every other field (Profit,
   Category, Region, Customer, Segment, Payment Mode...) is optional, and the
   dashboard automatically shows/hides charts based on what's actually present
   in your file

If you don't upload anything, the dashboard shows a **demo dataset**: 11,000
synthetic but realistically-modeled Indian retail transactions (2023–2025)
with festive seasonality (Diwali, Republic Day sale, EOSS) baked in — see
`sample_data.py` for exactly how it's generated, fully in-memory (no CSV file
on disk, so there's nothing that can go missing on deploy).

## Run it locally

```bash
git clone https://github.com/YOUR_USERNAME/sales-dashboard.git
cd sales-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub — **keep the flat structure below**, don't nest
   files in extra folders
2. Go to https://share.streamlit.io → **New app** → pick the repo, branch
   `main`, file `app.py`
3. Deploy — no secrets/API keys needed
4. Copy the live `*.streamlit.app` URL into this README and your resume/portfolio

## Project structure

```
sales-dashboard/
├── app.py                  # the dashboard (upload + auto-analyze + charts)
├── sample_data.py          # in-memory demo data generator (no file path needed)
├── requirements.txt
├── .streamlit/config.toml  # dark theme
└── README.md
```

## Ideas to extend further

- Swap the linear-trend forecast for Prophet or SARIMA with proper seasonality decomposition
- Add a customer RFM (Recency/Frequency/Monetary) segmentation tab
- Add a cohort retention analysis (repeat purchase rate by signup month)
- Persist uploaded data to a database instead of re-uploading each session
- Add anomaly detection on daily sales (flag unusual spikes/drops automatically)

---

### Talking points for interviews

- **"How does it handle real-world messy data?"** → walk through the column
  auto-detection, currency-symbol stripping, and the mixed-date-format bug I
  specifically had to fix (pandas infers one date format per column and
  silently drops rows that don't match — parsing row-by-row fixes it).
- **"Why these charts?"** → line chart for trend (time-series), heatmap for
  two categorical dimensions (weekday × category), pie only for share-of-whole
  with few categories (region), bar for ranked comparisons (top products).
- **"What would you do with more time?"** → see "Ideas to extend" above.
