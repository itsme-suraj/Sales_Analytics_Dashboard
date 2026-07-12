"""
Retail Sales Analytics Dashboard — with CSV/Excel upload + auto column detection.

Users can upload their own sales data (CSV or Excel). The app guesses which
columns are Date, Sales, Profit, Category, etc., lets the user confirm/adjust
the mapping, then runs the full analysis. If nothing is uploaded, it falls back
to an in-memory generated demo dataset — no file on disk is ever required, so
there's no fixed file path to break.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sample_data import generate_sample_data

st.set_page_config(page_title="Retail Sales Analytics", page_icon="📊", layout="wide")

CUSTOM_CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
h1 {
    background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-weight: 800;
}
div[data-testid="stMetric"] {
    background: #181920; border: 1px solid #262730; border-radius: 12px;
    padding: 14px 16px;
}
div[data-testid="stMetricLabel"] { opacity: 0.75; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------
# COLUMN AUTO-DETECTION
# ----------------------------------------------------------------------
FIELD_ALIASES = {
    "Date":         ["order date", "date", "purchase date", "transaction date"],
    "Sales":        ["sales", "revenue", "total amount", "amount", "total sales", "total"],
    "Profit":       ["profit", "net profit", "margin amount"],
    "Category":     ["category", "product category", "type"],
    "Product Name": ["product name", "product", "item name", "item"],
    "Region":       ["region", "zone"],
    "Segment":      ["segment", "customer type", "customer segment"],
    "Customer":     ["customer name", "customer", "client", "buyer name"],
    "Payment Mode": ["payment mode", "payment method", "payment"],
    "Quantity":     ["quantity", "qty", "units", "units sold"],
    "Discount %":   ["discount %", "discount", "discount pct"],
    "Order ID":     ["order id", "invoice no", "invoice", "transaction id", "order no"],
}
REQUIRED_FIELDS = ["Date", "Sales"]
OPTIONAL_FIELDS = [f for f in FIELD_ALIASES if f not in REQUIRED_FIELDS]


def guess_column(columns, keywords):
    cols_lower = {c: c.lower().strip() for c in columns}
    for kw in keywords:
        for c, lc in cols_lower.items():
            if kw == lc:
                return c
    for kw in keywords:
        for c, lc in cols_lower.items():
            if kw in lc:
                return c
    return None


def clean_numeric(series: pd.Series) -> pd.Series:
    """Strips currency symbols/commas/spaces and converts to numeric."""
    cleaned = series.astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def clean_dates(series: pd.Series) -> pd.Series:
    """Parses each value individually (trying standard then day-first format) rather than
    inferring one format for the whole column — real-world files often mix date formats,
    and pandas' bulk parser silently fails on rows that don't match the inferred format."""
    def parse_one(val):
        d = pd.to_datetime(val, errors="coerce")
        if pd.isna(d):
            d = pd.to_datetime(val, errors="coerce", dayfirst=True)
        return d
    return series.apply(parse_one)


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    return generate_sample_data()


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file type — please upload a .csv or .xlsx file.")

# ----------------------------------------------------------------------
# SIDEBAR — DATA SOURCE
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📁 Data Source")
    uploaded_file = st.file_uploader("Upload sales data (CSV or Excel)", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("_file_key") != file_key:
            # new file — reset any previous mapping so we re-guess fresh
            st.session_state._file_key = file_key
            st.session_state.pop("mapping_confirmed", None)
        try:
            raw_df = read_uploaded_file(uploaded_file)
            using_demo = False
        except Exception as e:
            st.error(f"Couldn't read that file: {e}")
            raw_df = load_demo_data()
            using_demo = True
    else:
        raw_df = load_demo_data()
        using_demo = True
        st.session_state.pop("mapping_confirmed", None)

    if using_demo:
        st.info("📊 Showing **demo data** (11,000 synthetic Indian retail transactions). "
                "Upload your own CSV/Excel above to analyze real data.")

# ----------------------------------------------------------------------
# COLUMN MAPPING (only needed for uploaded files)
# ----------------------------------------------------------------------
if using_demo:
    # Demo data's own columns (e.g. "Order Date", "Customer Name") don't match the
    # standard field names 1:1, so run it through the same auto-detection as uploads.
    mapping = {f: guess_column(raw_df.columns, FIELD_ALIASES[f]) for f in FIELD_ALIASES}
else:
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔧 Map your columns")
        st.caption("We guessed these from your file — adjust if anything looks wrong.")

        with st.form("mapping_form"):
            mapping = {}
            none_option = "— None —"
            for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
                guess = guess_column(raw_df.columns, FIELD_ALIASES[field])
                options = [none_option] + list(raw_df.columns)
                default_idx = options.index(guess) if guess in options else 0
                label = f"{field} {'(required)' if field in REQUIRED_FIELDS else ''}"
                mapping[field] = st.selectbox(label, options, index=default_idx, key=f"map_{field}")
            submitted = st.form_submit_button("✅ Apply mapping & analyze")

        if submitted:
            st.session_state.mapping_confirmed = mapping

    mapping = st.session_state.get("mapping_confirmed")
    if mapping is None:
        st.title("📊 Retail Sales Analytics Dashboard")
        st.info(
            "👈 File uploaded! Confirm the column mapping in the sidebar and click "
            "**'Apply mapping & analyze'** to run the dashboard."
        )
        st.markdown("#### Preview of your uploaded data")
        st.dataframe(raw_df.head(20), use_container_width=True)
        st.stop()

    if mapping[REQUIRED_FIELDS[0]] == "— None —" or mapping[REQUIRED_FIELDS[1]] == "— None —":
        st.error("⚠️ **Date** and **Sales** columns are required — please map both and re-submit.")
        st.stop()

# ----------------------------------------------------------------------
# STANDARDIZE INTO INTERNAL SCHEMA
# ----------------------------------------------------------------------
df = pd.DataFrame()
none_option = "— None —"
for field, source_col in mapping.items():
    if source_col and source_col != none_option and source_col in raw_df.columns:
        df[field] = raw_df[source_col]

df["Date"] = clean_dates(df["Date"])
df["Sales"] = clean_numeric(df["Sales"])
if "Profit" in df.columns:
    df["Profit"] = clean_numeric(df["Profit"])
if "Quantity" in df.columns:
    df["Quantity"] = clean_numeric(df["Quantity"])
if "Discount %" in df.columns:
    df["Discount %"] = clean_numeric(df["Discount %"])
if "Order ID" not in df.columns:
    df["Order ID"] = df.index.astype(str)

before = len(df)
df = df.dropna(subset=["Date", "Sales"])
dropped = before - len(df)
if dropped > 0 and not using_demo:
    st.sidebar.warning(f"⚠️ Dropped {dropped:,} row(s) with unreadable Date/Sales values.")

if df.empty:
    st.error("No usable rows after cleaning — check that your Date and Sales columns are correct.")
    st.stop()

HAS = {f: (f in df.columns and df[f].notna().any()) for f in OPTIONAL_FIELDS}

df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.to_period("M").astype(str)
df["Weekday"] = df["Date"].dt.day_name()
if HAS["Profit"]:
    df["Margin %"] = np.where(df["Sales"] != 0, (df["Profit"] / df["Sales"]) * 100, 0)

# ----------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    min_date, max_date = df["Date"].min().date(), df["Date"].max().date()
    date_range = st.date_input("Date range", value=(min_date, max_date),
                                min_value=min_date, max_value=max_date)

    active_filters = {}
    for field in ["Region", "Category", "Segment"]:
        if HAS[field]:
            opts = sorted(df[field].dropna().unique())
            active_filters[field] = st.multiselect(field, opts, default=opts)

# apply filters
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask = (df["Date"] >= start) & (df["Date"] <= end)
else:
    mask = pd.Series(True, index=df.index)
for field, selected in active_filters.items():
    mask &= df[field].isin(selected)
fdf = df[mask]

if fdf.empty:
    st.warning("No data matches the current filters — widen your selection.")
    st.stop()

# ----------------------------------------------------------------------
# HEADER + KPIs
# ----------------------------------------------------------------------
st.title("📊 Retail Sales Analytics Dashboard")
st.caption(
    "Analyzing " + ("demo data" if using_demo else f"**{uploaded_file.name}**")
    + f" · {len(fdf):,} transactions · Built with Streamlit + Plotly"
)

total_sales = fdf["Sales"].sum()
total_orders = fdf["Order ID"].nunique()
avg_order_value = total_sales / total_orders if total_orders else 0

kpi_cols = st.columns(5 if HAS["Profit"] else 3)
kpi_cols[0].metric("Total Sales", f"₹{total_sales/1e7:,.2f} Cr" if total_sales >= 1e7 else f"₹{total_sales:,.0f}")
kpi_cols[1].metric("Total Orders", f"{total_orders:,}")
kpi_cols[2].metric("Avg Order Value", f"₹{avg_order_value:,.0f}")
if HAS["Profit"]:
    total_profit = fdf["Profit"].sum()
    margin_pct = (total_profit / total_sales * 100) if total_sales else 0
    kpi_cols[3].metric("Total Profit", f"₹{total_profit/1e7:,.2f} Cr" if total_profit >= 1e7 else f"₹{total_profit:,.0f}")
    kpi_cols[4].metric("Profit Margin", f"{margin_pct:.1f}%")

st.markdown("---")

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab_names = ["📈 Overview"]
if HAS["Product Name"] or HAS["Category"]:
    tab_names.append("🏷️ Products")
if HAS["Customer"]:
    tab_names.append("👥 Customers")
tab_names += ["🔮 Forecast", "📄 Raw Data"]
tabs = st.tabs(tab_names)
tab_map = dict(zip(tab_names, tabs))

# ---------------- OVERVIEW ----------------
with tab_map["📈 Overview"]:
    c1, c2 = st.columns([2, 1]) if HAS["Region"] else (st.container(), None)

    with c1:
        monthly = fdf.groupby("Month", as_index=False)["Sales"].sum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Sales"], name="Sales",
                                  mode="lines+markers", line=dict(color="#38bdf8", width=3)))
        if HAS["Profit"]:
            monthly_p = fdf.groupby("Month", as_index=False)["Profit"].sum()
            fig.add_trace(go.Scatter(x=monthly_p["Month"], y=monthly_p["Profit"], name="Profit",
                                      mode="lines+markers", line=dict(color="#f472b6", width=3)))
        fig.update_layout(title="Monthly Sales Trend", template="plotly_dark",
                           height=380, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    if HAS["Region"] and c2 is not None:
        with c2:
            by_region = fdf.groupby("Region", as_index=False)["Sales"].sum()
            fig = px.pie(by_region, names="Region", values="Sales", hole=0.55, template="plotly_dark",
                         title="Sales Share by Region",
                         color_discrete_sequence=px.colors.sequential.Tealgrn)
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    if HAS["Category"]:
        with c3:
            by_cat = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales")
            fig = px.bar(by_cat, x="Sales", y="Category", orientation="h", template="plotly_dark",
                         title="Sales by Category", color="Sales", color_continuous_scale="Blues")
            fig.update_layout(height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    if HAS["Category"]:
        with c4:
            heat = fdf.groupby(["Weekday", "Category"])["Sales"].sum().reset_index()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heat["Weekday"] = pd.Categorical(heat["Weekday"], categories=weekday_order, ordered=True)
            pivot = heat.pivot(index="Weekday", columns="Category", values="Sales").sort_index()
            fig = px.imshow(pivot, template="plotly_dark", aspect="auto",
                             title="Sales Intensity: Weekday vs Category", color_continuous_scale="Magma")
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)
    elif not HAS["Category"]:
        with c3:
            by_weekday = fdf.groupby("Weekday", as_index=False)["Sales"].sum()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            by_weekday["Weekday"] = pd.Categorical(by_weekday["Weekday"], categories=weekday_order, ordered=True)
            by_weekday = by_weekday.sort_values("Weekday")
            fig = px.bar(by_weekday, x="Weekday", y="Sales", template="plotly_dark", title="Sales by Weekday")
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

# ---------------- PRODUCTS ----------------
if "🏷️ Products" in tab_map:
    with tab_map["🏷️ Products"]:
        group_field = "Product Name" if HAS["Product Name"] else "Category"
        c1, c2 = st.columns(2)
        with c1:
            top_products = (
                fdf.groupby(group_field, as_index=False)["Sales"].sum()
                .sort_values("Sales", ascending=False).head(10)
            )
            fig = px.bar(top_products, x="Sales", y=group_field, orientation="h",
                         template="plotly_dark", title=f"Top 10 by Sales ({group_field})",
                         color="Sales", color_continuous_scale="Purples")
            fig.update_layout(height=420, yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        if HAS["Discount %"] and HAS["Profit"]:
            with c2:
                disc_profit = fdf.groupby("Discount %", as_index=False)["Margin %"].mean()
                fig = px.line(disc_profit, x="Discount %", y="Margin %", markers=True,
                               template="plotly_dark", title="Discount % vs Avg Profit Margin")
                fig.add_hline(y=0, line_dash="dash", line_color="red")
                fig.update_layout(height=420)
                st.plotly_chart(fig, use_container_width=True)
                st.warning(
                    "⚠️ **Insight:** Watch where this line crosses zero — that's the discount "
                    "level where you start losing money on each sale."
                )

# ---------------- CUSTOMERS ----------------
if "👥 Customers" in tab_map:
    with tab_map["👥 Customers"]:
        c1, c2 = st.columns(2)
        if HAS["Segment"]:
            with c1:
                by_segment = fdf.groupby("Segment", as_index=False)["Sales"].sum()
                fig = px.bar(by_segment, x="Segment", y="Sales", template="plotly_dark",
                             title="Sales by Customer Segment", color="Segment")
                fig.update_layout(height=380)
                st.plotly_chart(fig, use_container_width=True)

        if HAS["Payment Mode"]:
            with c2:
                pay = fdf.groupby("Payment Mode", as_index=False)["Sales"].sum()
                fig = px.pie(pay, names="Payment Mode", values="Sales", template="plotly_dark",
                             title="Sales by Payment Mode", hole=0.4)
                fig.update_layout(height=380)
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 🏆 Top 15 Customers by Total Spend")
        top_customers = (
            fdf.groupby("Customer", as_index=False)
            .agg(Total_Spend=("Sales", "sum"), Orders=("Order ID", "nunique"))
            .sort_values("Total_Spend", ascending=False).head(15)
        )
        top_customers["Total_Spend"] = top_customers["Total_Spend"].round(0)
        st.dataframe(top_customers, use_container_width=True, hide_index=True)

# ---------------- FORECAST ----------------
with tab_map["🔮 Forecast"]:
    st.markdown("#### 3-Month Sales Forecast (simple trend projection)")
    st.caption(
        "A lightweight linear-trend forecast — enough to demonstrate the concept in an "
        "interview. For production use you'd reach for Prophet/ARIMA with proper "
        "seasonality decomposition."
    )

    monthly_all = df.groupby("Month", as_index=False)["Sales"].sum()
    if len(monthly_all) < 3:
        st.info("Need at least 3 months of data to project a forecast.")
    else:
        monthly_all["idx"] = range(len(monthly_all))
        coeffs = np.polyfit(monthly_all["idx"], monthly_all["Sales"], deg=1)
        future_idx = range(len(monthly_all), len(monthly_all) + 3)
        future_sales = np.polyval(coeffs, list(future_idx))
        future_months = pd.date_range(
            pd.Period(monthly_all["Month"].iloc[-1]).to_timestamp() + pd.DateOffset(months=1),
            periods=3, freq="MS"
        ).strftime("%Y-%m")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_all["Month"], y=monthly_all["Sales"],
                                  name="Actual", mode="lines+markers", line=dict(color="#38bdf8")))
        fig.add_trace(go.Scatter(x=list(future_months), y=future_sales, name="Forecast",
                                  mode="lines+markers", line=dict(color="#facc15", dash="dash")))
        fig.update_layout(template="plotly_dark", height=420, title="Sales Trend with 3-Month Forecast")
        st.plotly_chart(fig, use_container_width=True)

        fc_cols = st.columns(3)
        for col, month, val in zip(fc_cols, future_months, future_sales):
            col.metric(f"Forecast: {month}", f"₹{val/1e7:,.2f} Cr" if val >= 1e7 else f"₹{val:,.0f}")

# ---------------- RAW DATA ----------------
with tab_map["📄 Raw Data"]:
    st.markdown(f"#### Filtered dataset — {len(fdf):,} rows")
    st.dataframe(fdf, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download filtered data as CSV",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )
