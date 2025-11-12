import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import chardet

# -----------------------------
# 1. CONFIG
# -----------------------------
st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")
CSV_PATH = "data.csv"

# -----------------------------
# 2. LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        st.error(f"❌ CSV file not found at: {CSV_PATH}")
        st.stop()

    # Detect file encoding automatically
    with open(CSV_PATH, "rb") as f:
        result = chardet.detect(f.read(100000))
        encoding = result["encoding"] or "utf-8"

    st.sidebar.write(f"📄 Detected file encoding: `{encoding}`")

    try:
        df = pd.read_csv(CSV_PATH, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding="latin-1")

    # Clean and normalize columns
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    # Parse dates
    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    # Compute total sales
    if "Quantity" in df.columns and "UnitPrice" in df.columns:
        df["TotalSales"] = df["Quantity"] * df["UnitPrice"]

    return df

df = load_data()

# -----------------------------
# 3. SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Filters")

# Country Filter
if "Country" in df.columns:
    countries = sorted(df["Country"].dropna().unique())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries[:5])
    df = df[df["Country"].isin(selected_countries)]

# Date Filter
if "InvoiceDate" in df.columns:
    min_date, max_date = df["InvoiceDate"].min(), df["InvoiceDate"].max()
    start_date, end_date = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    if start_date and end_date:
        df = df[(df["InvoiceDate"] >= pd.to_datetime(start_date)) & (df["InvoiceDate"] <= pd.to_datetime(end_date))]

# Price Filter
if "TotalSales" in df.columns:
    min_price, max_price = float(df["TotalSales"].min()), float(df["TotalSales"].max())
    price_range = st.sidebar.slider("Select Sales Range", min_price, max_price, (min_price, max_price))
    df = df[(df["TotalSales"] >= price_range[0]) & (df["TotalSales"] <= price_range[1])]

# -----------------------------
# 4. KPI METRICS
# -----------------------------
st.title("📊 E-Commerce Sales Dashboard")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Sales", f"${df['TotalSales'].sum():,.2f}")
col2.metric("📦 Total Orders", f"{df['InvoiceNo'].nunique():,}")
col3.metric("🏷️ Avg Unit Price", f"${df['UnitPrice'].mean():,.2f}")
col4.metric("👥 Unique Customers", f"{df['CustomerID'].nunique():,}")

# -----------------------------
# 5. VISUALIZATIONS
# -----------------------------
st.subheader("📅 Sales Over Time")
if "InvoiceDate" in df.columns:
    time_df = df.groupby(df["InvoiceDate"].dt.to_period("M"))["TotalSales"].sum().reset_index()
    time_df["InvoiceDate"] = time_df["InvoiceDate"].astype(str)
    fig1 = px.line(time_df, x="InvoiceDate", y="TotalSales", title="Sales Trend Over Time", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("🌍 Sales by Country")
if "Country" in df.columns:
    country_sales = df.groupby("Country")["TotalSales"].sum().reset_index().sort_values("TotalSales", ascending=False)
    fig2 = px.bar(country_sales, x="Country", y="TotalSales", color="Country", title="Total Sales by Country")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("🏆 Top 10 Products by Sales")
if "Description" in df.columns:
    top_products = df.groupby("Description")["TotalSales"].sum().reset_index().sort_values("TotalSales", ascending=False).head(10)
    fig3 = px.bar(top_products, x="TotalSales", y="Description", orientation="h", title="Top Products", color="TotalSales")
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("📊 Quantity vs Sales Distribution")
fig4 = px.scatter(df, x="Quantity", y="TotalSales", color="Country", title="Quantity vs Total Sales")
st.plotly_chart(fig4, use_container_width=True)

st.subheader("📈 Sales Distribution")
fig5 = px.histogram(df, x="TotalSales", nbins=50, title="Sales Value Distribution", color_discrete_sequence=["indianred"])
st.plotly_chart(fig5, use_container_width=True)

# -----------------------------
# 6. CORRELATION HEATMAP
# -----------------------------
st.subheader("🔢 Correlation Heatmap")
numeric_df = df.select_dtypes(include=["float64", "int64"])
corr = numeric_df.corr()

fig6 = go.Figure(data=go.Heatmap(
    z=corr.values,
    x=corr.columns,
    y=corr.columns,
    colorscale="Viridis"
))
fig6.update_layout(title="Correlation Heatmap")
st.plotly_chart(fig6, use_container_width=True)

# -----------------------------
# 7. RAW DATA
# -----------------------------
st.subheader("🧾 Raw Data Preview")
st.dataframe(df.head(50))
