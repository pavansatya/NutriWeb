import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import pandas as pd
import os
from nutriweb.data_loader import load_cleaned_data
from modules.radar_chart import preprocess_data, create_radar_chart_with_dropdown

st.title("📊 Nutritional Overview of Top 10 food categories - Radar Chart")

# Load data
df = st.session_state.get("df")
if df is None:
    st.error("Data not loaded yet. Please start from the homepage first.")
    st.stop()

# Radar chart settings
category_col = 'category_level_1'
nutrient_cols = ['proteins_100g', 'carbohydrates_100g', 'fiber_100g', 'fat_100g', 'salt_100g']

try:
    top_category_nutrition = preprocess_data(df, category_col, nutrient_cols, top_n=10)
    categories = top_category_nutrition[category_col]
    values = top_category_nutrition[nutrient_cols]

    fig = create_radar_chart_with_dropdown(categories, values, title='Top 10 Primary Categories by Nutritional Facts')
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error displaying radar chart: {e}")




st.title("Categorical Hierarchy Analysis")

# --- Show HTML treemap ---
st.subheader("📌 Interactive Treemap (HTML)")
try:
    with open(os.path.join("results", "category_hierarchy_treemap.html"), "r") as f:
        html_data = f.read()
    components.html(html_data, height=1200, width=None, scrolling=True)
except FileNotFoundError:
    st.warning("Treemap HTML file not found. Please add html file to results/.")