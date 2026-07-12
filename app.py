"""
Indian Retail Sales Analytics Dashboard
A portfolio project demonstrating: data cleaning, KPI design, interactive filtering,
cohort/segment analysis, and lightweight forecasting — built with Streamlit + Plotly.

Data: synthetic but realistically structured (3 years, regional seasonality,
category-specific margins) — see data/generate_data.py for how it was built.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
# DATA LOADING
# ----------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/sales_data.csv", parse_dates=["Order Date", "Ship Date"])
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    df["Month Name"] = df["Order Date"].dt.strftime("%b")
    df["Weekday"] = df["Order Date"].dt.day_name()
    df["Margin %"] = np.where(df["Sales"] != 0, (df["Profit"] / df["Sales"]) * 100, 0)
    return df

df = load_data()

# ----------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 Filters")

    min_date, max_date = df["Order Date"].min().date(), df["Order Date"].max().date()
    date_range = st.date_input("Order date range", value=(min_date, max_date),
                                min_value=min_date, max_value=max_date)

    regions = st.multiselect("Region", sorted(df["Region"].unique()),
                              default=sorted(df["Region"].unique()))
    categories = st.multiselect("Category", sorted(df["Category"].unique()),
                                 default=sorted(df["Category"].unique()))
    segments = st.multiselect("Segment", sorted(df["Segment"].unique()),
                               default=sorted(df["Segment"].unique()))

    st.markdown("---")
    st.caption(
        "**Dataset:** 11,000 synthetic but realistically-modeled Indian retail "
        "transactions (2023–2025) with festive seasonality (Diwali, Republic Day "
        "sale, EOSS) baked in. See `data/generate_data.py` for the generation logic."
    )

# apply filters
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    mask = (
        (df["Order Date"] >= start) & (df["Order Date"] <= end)
        & (df["Region"].isin(regions)) & (df["Category"].isin(categories))
        & (df["Segment"].isin(segments))
    )
    fdf = df[mask]
else:
    fdf = df[df["Region"].isin(regions) & df["Category"].isin(categories) & df["Segment"].isin(segments)]

if fdf.empty:
    st.warning("No data matches the current filters — widen your selection.")
    st.stop()

# ----------------------------------------------------------------------
# HEADER + KPIs
# ----------------------------------------------------------------------
st.title("📊 Retail Sales Analytics Dashboard")
st.caption("Indian retail sales performance — 2023 to 2025 · Built with Streamlit + Plotly")

total_sales = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()
total_orders = fdf["Order ID"].nunique()
avg_order_value = total_sales / total_orders if total_orders else 0
margin_pct = (total_profit / total_sales * 100) if total_sales else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"₹{total_sales/1e7:,.2f} Cr")
k2.metric("Total Profit", f"₹{total_profit/1e7:,.2f} Cr")
k3.metric("Total Orders", f"{total_orders:,}")
k4.metric("Avg Order Value", f"₹{avg_order_value:,.0f}")
k5.metric("Profit Margin", f"{margin_pct:.1f}%")

st.markdown("---")

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab_overview, tab_products, tab_customers, tab_forecast, tab_data = st.tabs(
    ["📈 Overview", "🏷️ Products", "👥 Customers", "🔮 Forecast", "📄 Raw Data"]
)

# ---------------- OVERVIEW ----------------
with tab_overview:
    c1, c2 = st.columns([2, 1])

    with c1:
        monthly = fdf.groupby("Month", as_index=False).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Sales"], name="Sales",
                                  mode="lines+markers", line=dict(color="#38bdf8", width=3)))
        fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit"], name="Profit",
                                  mode="lines+markers", line=dict(color="#f472b6", width=3)))
        fig.update_layout(title="Monthly Sales & Profit Trend", template="plotly_dark",
                           height=380, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        by_region = fdf.groupby("Region", as_index=False)["Sales"].sum()
        fig = px.pie(by_region, names="Region", values="Sales", hole=0.55, template="plotly_dark",
                     title="Sales Share by Region",
                     color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        by_cat = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales")
        fig = px.bar(by_cat, x="Sales", y="Category", orientation="h", template="plotly_dark",
                     title="Sales by Category", color="Sales", color_continuous_scale="Blues")
        fig.update_layout(height=360, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        heat = fdf.groupby(["Weekday", "Category"])["Sales"].sum().reset_index()
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat["Weekday"] = pd.Categorical(heat["Weekday"], categories=weekday_order, ordered=True)
        pivot = heat.pivot(index="Weekday", columns="Category", values="Sales").sort_index()
        fig = px.imshow(pivot, template="plotly_dark", aspect="auto",
                         title="Sales Intensity: Weekday vs Category", color_continuous_scale="Magma")
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        f"💡 **Insight:** Festive months (Oct–Nov, Diwali season) and January "
        f"(Republic Day sale) show the strongest spikes — a real seasonality pattern "
        f"baked into this dataset, useful for staffing and inventory planning discussions."
    )

# ---------------- PRODUCTS ----------------
with tab_products:
    c1, c2 = st.columns(2)
    with c1:
        top_products = (
            fdf.groupby("Product Name", as_index=False)["Sales"].sum()
            .sort_values("Sales", ascending=False).head(10)
        )
        fig = px.bar(top_products, x="Sales", y="Product Name", orientation="h",
                     template="plotly_dark", title="Top 10 Products by Sales",
                     color="Sales", color_continuous_scale="Purples")
        fig.update_layout(height=420, yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        disc_profit = fdf.groupby("Discount %", as_index=False)["Margin %"].mean()
        fig = px.line(disc_profit, x="Discount %", y="Margin %", markers=True,
                       template="plotly_dark", title="Discount % vs Avg Profit Margin")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.warning(
        "⚠️ **Insight:** Profit margin trends toward zero (and below) once discounts "
        "cross ~25–30% — a classic 'discount is eating our margin' finding you can "
        "walk an interviewer through."
    )

    cat_choice = st.selectbox("Drill into a category", sorted(fdf["Category"].unique()))
    sub = fdf[fdf["Category"] == cat_choice]
    fig = px.scatter(sub, x="Discount %", y="Profit", color="Payment Mode", size="Sales",
                      template="plotly_dark", title=f"{cat_choice}: Discount vs Profit by Payment Mode",
                      hover_data=["Product Name"])
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- CUSTOMERS ----------------
with tab_customers:
    c1, c2 = st.columns(2)
    with c1:
        by_segment = fdf.groupby("Segment", as_index=False).agg(
            Sales=("Sales", "sum"), Orders=("Order ID", "nunique")
        )
        fig = px.bar(by_segment, x="Segment", y="Sales", template="plotly_dark",
                     title="Sales by Customer Segment", color="Segment")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        pay = fdf.groupby("Payment Mode", as_index=False)["Sales"].sum()
        fig = px.pie(pay, names="Payment Mode", values="Sales", template="plotly_dark",
                     title="Sales by Payment Mode", hole=0.4)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🏆 Top 15 Customers by Total Spend")
    top_customers = (
        fdf.groupby(["Customer ID", "Customer Name"], as_index=False)
        .agg(Total_Spend=("Sales", "sum"), Orders=("Order ID", "nunique"))
        .sort_values("Total_Spend", ascending=False).head(15)
    )
    top_customers["Total_Spend"] = top_customers["Total_Spend"].round(0)
    st.dataframe(top_customers, use_container_width=True, hide_index=True)

# ---------------- FORECAST ----------------
with tab_forecast:
    st.markdown("#### 🔮 3-Month Sales Forecast (simple trend projection)")
    st.caption(
        "A lightweight linear-trend forecast — enough to demonstrate the concept in an "
        "interview. For production use you'd reach for Prophet/ARIMA with proper "
        "seasonality decomposition."
    )

    monthly_all = df.groupby("Month", as_index=False)["Sales"].sum()
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

    fc1, fc2, fc3 = st.columns(3)
    for col, month, val in zip([fc1, fc2, fc3], future_months, future_sales):
        col.metric(f"Forecast: {month}", f"₹{val/1e7:,.2f} Cr")

# ---------------- RAW DATA ----------------
with tab_data:
    st.markdown(f"#### Filtered dataset — {len(fdf):,} rows")
    st.dataframe(fdf, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download filtered data as CSV",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )
