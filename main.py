import os
import pandas as pd
import numpy as np
import random
from faker import Faker
import streamlit as st
import plotly.express as px

# -------------------------
# CONFIGURATION
# -------------------------
st.set_page_config(page_title="Fashion Intelligence Dashboard", layout="wide")
st.title("🛍️ Fashion E-Commerce Intelligence Dashboard")

fake = Faker()

# -------------------------
# CONSTANTS
# -------------------------
BRANDS = ["Zara", "H&M", "Uniqlo", "Nike", "Adidas", "Levi's", "Gucci", "Prada", "Forever21", "Puma"]
CATEGORIES = ["T-Shirts", "Jeans", "Dresses", "Jackets", "Shoes", "Accessories", "Skirts", "Sweaters", "Shorts", "Bags"]
GENDERS = ["Men", "Women", "Unisex", "Kids"]
COLORS = ["Red", "Blue", "Black", "White", "Green", "Yellow", "Pink", "Purple", "Gray", "Brown"]
SIZES = ["XS", "S", "M", "L", "XL", "XXL"]

# -------------------------
# CACHED DATA
# -------------------------
@st.cache_data
def generate_dummy_ecommerce_data(n_rows=100000):
    data = []
    for i in range(n_rows):
        data.append({
            "product_id": f"P{i+1:05d}",
            "brand": random.choice(BRANDS),
            "category": random.choice(CATEGORIES),
            "gender": random.choice(GENDERS),
            "color": random.choice(COLORS),
            "size": random.choice(SIZES),
            "price": round(random.uniform(10, 500), 2),
            "stock": random.randint(0, 100),
            "rating": round(random.uniform(1, 5), 1),
            "date_added": fake.date_between(start_date='-2y', end_date='today')
        })
    return pd.DataFrame(data)

@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "ecommerce_data.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)
    df = generate_dummy_ecommerce_data(100000)
    df.to_parquet(path, index=False, compression="snappy")
    return df

df = load_data()
df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")

# -------------------------
# SIDEBAR FILTERS
# -------------------------
st.sidebar.header("🔎 Filters")
brand_filter = st.sidebar.multiselect("Brand", df["brand"].unique(), default=df["brand"].unique())
category_filter = st.sidebar.multiselect("Category", df["category"].unique(), default=df["category"].unique())
gender_filter = st.sidebar.multiselect("Gender", df["gender"].unique(), default=df["gender"].unique())
color_filter = st.sidebar.multiselect("Color", df["color"].unique(), default=df["color"].unique())

df_filtered = df[
    (df["brand"].isin(brand_filter)) &
    (df["category"].isin(category_filter)) &
    (df["gender"].isin(gender_filter)) &
    (df["color"].isin(color_filter))
]

# -------------------------
# SUMMARY METRICS
# -------------------------
st.subheader("📊 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Products", len(df_filtered))
col2.metric("Average Price", f"${df_filtered['price'].mean():.2f}")
col3.metric("Average Rating", f"{df_filtered['rating'].mean():.1f}/5")
col4.metric("Out of Stock", int((df_filtered["stock"] == 0).sum()))

# -------------------------
# VISUALIZATIONS (SAFE FOR LIVE)
# -------------------------
# Category Distribution
st.subheader("📦 Products by Category")
cat_counts = df_filtered["category"].value_counts().reset_index()
cat_counts.columns = ["Category", "Count"]
fig_cat = px.bar(cat_counts.head(15), x="Category", y="Count", color="Category", title="Top Categories")
st.plotly_chart(fig_cat, use_container_width=True, config={"staticPlot": False})

# Brand Distribution
st.subheader("🏷️ Products by Brand")
brand_counts = df_filtered["brand"].value_counts().reset_index()
brand_counts.columns = ["Brand", "Count"]
fig_brand = px.bar(brand_counts.head(10), x="Brand", y="Count", color="Brand", title="Top Brands")
st.plotly_chart(fig_brand, use_container_width=True, config={"staticPlot": False})

# Price Distribution (sample)
st.subheader("💰 Price Distribution")
df_sample = df_filtered.sample(n=min(5000, len(df_filtered)), random_state=42)
fig_price = px.histogram(df_sample, x="price", nbins=50, title="Price Distribution", color_discrete_sequence=["#2E86AB"])
st.plotly_chart(fig_price, use_container_width=True, config={"staticPlot": False})

# Rating Distribution (sample)
st.subheader("⭐ Rating Distribution")
fig_rating = px.histogram(df_sample, x="rating", nbins=10, title="Rating Distribution", color_discrete_sequence=["#F4A261"])
st.plotly_chart(fig_rating, use_container_width=True, config={"staticPlot": False})

# Time Trend (aggregated)
st.subheader("📅 Products Added Over Time")
df_time = df_filtered.groupby(df_filtered["date_added"].dt.to_period("M")).size().reset_index(name="Count")
df_time["date_added"] = df_time["date_added"].dt.to_timestamp()
fig_time = px.line(df_time, x="date_added", y="Count", title="New Products Added Monthly")
st.plotly_chart(fig_time, use_container_width=True, config={"staticPlot": False})

# -------------------------
# RAW DATA VIEW
# -------------------------
with st.expander("🧾 Show Raw Data"):
    st.dataframe(df_filtered.head(1000))  # show limited rows for performance
