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
# DUMMY DATA GENERATION (CACHED)
# -------------------------
@st.cache_data
def generate_dummy_ecommerce_data(n_rows=10000):
    data = []
    for i in range(n_rows):
        brand = random.choice(BRANDS)
        category = random.choice(CATEGORIES)
        gender = random.choice(GENDERS)
        color = random.choice(COLORS)
        size = random.choice(SIZES)
        price = round(random.uniform(10, 500), 2)
        stock = random.randint(0, 100)
        rating = round(random.uniform(1, 5), 1)
        date_added = fake.date_between(start_date='-2y', end_date='today')
        product_name = f"{brand} {category} {random.choice(['Classic','Limited','Premium','Casual','Sport'])}"
        data.append({
            "product_id": f"P{i+1:05d}",
            "name": product_name,
            "brand": brand,
            "category": category,
            "gender": gender,
            "color": color,
            "size": size,
            "price": price,
            "stock": stock,
            "rating": rating,
            "date_added": date_added
        })
    return pd.DataFrame(data)

# -------------------------
# PARQUET FILE HANDLING
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARQUET_PATH = os.path.join(BASE_DIR, "ecommerce_data.parquet")

@st.cache_data
def load_data():
    if os.path.exists(PARQUET_PATH):
        df = pd.read_parquet(PARQUET_PATH)
    else:
        st.sidebar.warning("⚠️ No Parquet file found — generating dummy data...")
        df = generate_dummy_ecommerce_data(10000)
        df.to_parquet(PARQUET_PATH, index=False, compression='snappy')
        st.sidebar.info("💾 Dummy data saved as Parquet for next run.")
    return df

df = load_data()
df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')

# -------------------------
# SIDEBAR FILTERS
# -------------------------
st.sidebar.header("🔎 Filters")
brand_filter = st.sidebar.multiselect("Brand", options=df['brand'].unique(), default=df['brand'].unique())
category_filter = st.sidebar.multiselect("Category", options=df['category'].unique(), default=df['category'].unique())
gender_filter = st.sidebar.multiselect("Gender", options=df['gender'].unique(), default=df['gender'].unique())
color_filter = st.sidebar.multiselect("Color", options=df['color'].unique(), default=df['color'].unique())

df_filtered = df[
    (df['brand'].isin(brand_filter)) &
    (df['category'].isin(category_filter)) &
    (df['gender'].isin(gender_filter)) &
    (df['color'].isin(color_filter))
]

# -------------------------
# SUMMARY METRICS
# -------------------------
st.subheader("📊 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Products", len(df_filtered))
col2.metric("Average Price", f"${df_filtered['price'].mean():.2f}")
col3.metric("Average Rating", f"{df_filtered['rating'].mean():.1f}/5")
col4.metric("Out of Stock", (df_filtered['stock'] == 0).sum())

# -------------------------
# VISUALIZATIONS (OPTIMIZED)
# -------------------------
st.subheader("📦 Products by Category")
df_cat = df_filtered['category'].value_counts().reset_index()
df_cat.columns = ['Category', 'Count']
df_cat = df_cat.head(20)  # Limit to top 20
fig_cat = px.bar(df_cat, x='Category', y='Count', color='Category', text='Count', title="Product Distribution by Category")
st.plotly_chart(fig_cat, use_container_width=True, theme="streamlit")

st.subheader("🏷️ Products by Brand")
df_brand = df_filtered['brand'].value_counts().reset_index()
df_brand.columns = ['Brand', 'Count']
df_brand = df_brand.head(20)
fig_brand = px.bar(df_brand, x='Brand', y='Count', color='Brand', text='Count', title="Product Distribution by Brand")
st.plotly_chart(fig_brand, use_container_width=True, theme="streamlit")

st.subheader("💰 Price Distribution (Sampled)")
df_price_sample = df_filtered.sample(n=min(10000, len(df_filtered)), random_state=42)
fig_price = px.histogram(df_price_sample, x='price', nbins=50, color='category', marginal='box', title="Price Distribution by Category")
st.plotly_chart(fig_price, use_container_width=True, theme="streamlit")

st.subheader("⭐ Rating Distribution (Sampled)")
df_rating_sample = df_filtered.sample(n=min(10000, len(df_filtered)), random_state=42)
fig_rating = px.histogram(df_rating_sample, x='rating', nbins=10, color='category', marginal='box', title="Rating Distribution by Category")
st.plotly_chart(fig_rating, use_container_width=True, theme="streamlit")

st.subheader("📅 Products Added Over Time (Monthly Aggregated)")
df_time = df_filtered.groupby(df_filtered['date_added'].dt.to_period("M")).size().reset_index(name='Count')
df_time['date_added'] = df_time['date_added'].dt.to_timestamp()
fig_time = px.line(df_time, x='date_added', y='Count', title="New Products Over Time")
st.plotly_chart(fig_time, use_container_width=True, theme="streamlit")

# -------------------------
# RAW DATA VIEW
# -------------------------
with st.expander("🧾 Show Raw Data"):
    st.dataframe(df_filtered)
