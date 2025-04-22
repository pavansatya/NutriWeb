import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import faiss
import re
import os
import gdown

# Import our risk analysis functions.
from nutriweb.assess_risk import classify_product, assess_product_risks
# Import product lookup function (barcode search using the 'code' column).
#from nutriweb.data_loader import get_product_by_code, get_category_slice
from nutriweb.data_loader import load_cleaned_data, get_product_by_code, get_category_slice
# Import personalization functions.
from nutriweb.personalization import get_user_profile, personalize_recommendations
# Import recommendation functions (FAISS-based ingredient similarity) from modules.
from modules.recommendations import recommend_by_ingredients, recommend_products
# Import radar_chart funtions from modules.
from modules.radar_chart import preprocess_data, create_radar_chart_with_dropdown


# ------------------------------------------------------------------
# DATA & FAISS SETUP

@st.cache_data(show_spinner="Loading data and embeddings...")
def load_data(name_weight=0.2):
    """Download, unzip, and load .npy and .csv files from Google Drive."""

    emb_dir = "my_embeddings"
    data_dir = "useful_data"
    os.makedirs(emb_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    zip_files = {
        "ingredient_embeddings.npy.zip": {
            "drive_id": "1ox_YsYg0H6tQAIKaY-O-WJ6jF9zhBq_e", "target_dir": emb_dir, "expected_file": "ingredient_embeddings.npy"
        },
        "product_name_embeddings.npy.zip": {
            "drive_id": "1tXTZA5WfjNNsqBayXjqtENoO4Jd7UI88", "target_dir": emb_dir, "expected_file": "product_name_embeddings.npy"
        },
        "cleaned_data.csv.zip": {
            "drive_id": "1cjfePkFN7G9nH_u0tHEOyz6891tIWn2P", "target_dir": data_dir, "expected_file": "cleaned_data.csv"
        },
    }

    for zip_name, meta in zip_files.items():
        zip_path = os.path.join(meta["target_dir"], zip_name)
        extract_path = os.path.join(meta["target_dir"], meta["expected_file"])

        # Download from Google Drive if not already present
        if not os.path.exists(extract_path):
            url = f"https://drive.google.com/uc?id={meta['drive_id']}"
            gdown.download(url, zip_path, quiet=False)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(meta["target_dir"])

    # Load after extraction
    ingredient_emb = np.load(os.path.join(emb_dir, "ingredient_embeddings.npy"))
    product_name_emb = np.load(os.path.join(emb_dir, "product_name_embeddings.npy"))
    df = pd.read_csv(os.path.join(data_dir, "cleaned_data.csv"), dtype={"code": str})
    df.reset_index(drop=True, inplace=True)

    # Combine embeddings
    combined_emb = (1 - name_weight) * ingredient_emb + name_weight * product_name_emb
    return df, combined_emb

#df, combined_embeddings = load_data(name_weight=0.2)
st.title("NutriWeb")

# Session state
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# Load button
if not st.session_state.data_loaded:
    if st.button("Load data"):
        with st.spinner("Loading..."):
            from nutriweb.data_loader import load_data
            df, combined_embeddings = load_data()
            st.session_state.df = df
            st.session_state.combined_embeddings = combined_embeddings
            st.session_state.data_loaded = True
            st.success("Data loaded!")
else:
    df = st.session_state.df
    combined_embeddings = st.session_state.combined_embeddings
    st.write("🎉 Ready to go!")

@st.cache_resource
def create_faiss_index(embeddings: np.ndarray):
    """Build and return a FAISS index for the provided embeddings using L2 distance."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

faiss_index = create_faiss_index(combined_embeddings)

# ------------------------------------------------------------------
# SIDEBAR: USER PROFILE INPUT
st.sidebar.header("User Health Profile")
age = st.sidebar.number_input("Age", min_value=0, max_value=120, value=30)
gender = st.sidebar.selectbox("Gender", options=["Male", "Female", "Other"])
height = st.sidebar.number_input("Height (cm)", min_value=0, max_value=300, value=170)
weight = st.sidebar.number_input("Weight (kg)", min_value=0, max_value=500, value=70)
dietary_restrictions = st.sidebar.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan"])
allergen_options = ["Gluten", "Peanuts", "Soy", "Dairy", "Eggs", "Shellfish", "Fish", "Tree Nuts"]
allergens = st.sidebar.multiselect("Allergens (food allergies)", allergen_options)
high_bp = st.sidebar.checkbox("High Blood Pressure")     # if checked, user has high BP
high_chol = st.sidebar.checkbox("High Cholesterol")      # if checked, user has high cholesterol

# Save user profile in session state.
if "user_profile" not in st.session_state:
    st.session_state.user_profile = get_user_profile(
        age=age,
        gender=gender,
        height=height,
        weight=weight,
        cholesterol="High" if high_chol else "Normal",
        blood_pressure="High" if high_bp else "Normal",
        allergens=",".join(allergens),
        diet_type=",".join(dietary_restrictions)
    )

# ------------------------------------------------------------------
# MAIN: PRODUCT SEARCH
st.title("NutriWeb: Personalized Food Products Recommendation System")
search_mode = st.radio("Search for a product by:", ["Product Name", "Barcode"])
query = st.text_input("Enter product {}:".format("name" if search_mode=="Product Name" else "barcode"))

selected_product = None
if query:
    if search_mode == "Product Name":
        matches = df[df['product_name'].str.contains(query, case=False, na=False)]
        if matches.empty:
            st.warning("No products found with that name. Please try a different query.")
        elif len(matches) > 1:
            product_choice = st.selectbox("Select a product", matches['product_name'].unique())
            if product_choice:
                selected_product = df[df['product_name'] == product_choice].iloc[0]
        else:
            selected_product = matches.iloc[0]
    else:  # Barcode search
        matches = df[df['code'].astype(str) == str(query).strip()]
        if matches.empty:
            st.warning("No product found with that barcode. Please try a different code.")
        else:
            selected_product = matches.iloc[0]
            st.write(f"**Product found:** {selected_product['product_name']}")

# ------------------------------------------------------------------
# FUNCTION FOR VISUAL ENHANCEMENTS
def format_risk_level(risk):
    if risk == "Avoid":
        return "🔥 Avoid"
    elif risk == "Caution":
        return "⚠️ Caution"
    return "✅ Safe"
# ------------------------------------------------------------------
# IF PRODUCT IS SELECTED, DISPLAY ANALYSIS & RECOMMENDATIONS
if selected_product is not None:
    # Display product header (name and brand, if available)
    product_name = selected_product.get("product_name", "Unknown Product")
    product_brand = selected_product.get("brands") if "brands" in selected_product else None
    if pd.notna(product_brand) and product_brand not in [None, "", np.nan]:
        st.header(f"{product_brand} – {product_name}")
    else:
        st.header(product_name)
    
    # --- RISK ASSESSMENT (Single Block) ---
    classification, ing_risks, add_risks = classify_product(
        selected_product.get("ingredients_text", ""),
        selected_product.get("additives_en", "")
    )
    risk_details = assess_product_risks(
        selected_product.get("ingredients_text", ""),
        selected_product.get("additives_en", "")
    )
    # PERSONALIZED ALLERGEN OVERRIDE:
    # Convert the allergens stored in the user profile to a list.
    user_allergens_data = st.session_state.user_profile.get("allergens", "")
    if isinstance(user_allergens_data, str):
        user_allergens_list = [a.strip().lower() for a in user_allergens_data.split(",") if a.strip()]
    else:
        user_allergens_list = [a.strip().lower() for a in user_allergens_data]
    
    cleaned_ingredients = str(selected_product.get("ingredients_text", "")).lower()
    if user_allergens_list and any(allergen in cleaned_ingredients for allergen in user_allergens_list):
        classification = "Avoid"
        risk_details["warning"] = "This product contains allergens you are sensitive to."
    
    st.subheader("General Risk Assessment")
    st.write(f"**Classification:** {classification}")
    if risk_details.get("warning"):
        st.error(risk_details.get("warning"))
    st.subheader("Ingredient Risk Analysis")
    if ing_risks:
        formatted_ing_risks = pd.DataFrame([(k, format_risk_level(v)) for k, v in ing_risks.items()], columns=["Ingredient", "Risk"])
        st.dataframe(formatted_ing_risks, use_container_width=True)
    else:
        st.write("No ingredient-level risks identified.")
    st.subheader("Additive Risk Analysis")
    if add_risks:
        formatted_add_risks = pd.DataFrame([(k, format_risk_level(v)) for k, v in add_risks.items()], columns=["Additive", "Risk"])
        st.dataframe(formatted_add_risks, use_container_width=True)
    else:
        st.write("No additive-level risks identified.")
    
    # --- PERSONALIZED INGREDIENT-BASED ALTERNATIVES ---
    st.subheader("Personalized Ingredient-Based Alternatives")
    user_profile = st.session_state.user_profile
    # If the user has provided allergens, use category-level allergen substitution.
    if user_profile.get("allergens"):
        # Traverse category hierarchy from level 6 down to level 1.
        found_category = False
        allergen_category_level = None
        matched_allergen = None
        for lvl in range(6, 0, -1):
            cat_value = selected_product.get(f"category_level_{lvl}", "")
            if cat_value and any(allergen in cat_value.lower() for allergen in user_allergens_list):
                found_category = True
                allergen_category_level = lvl
                for allergen in user_allergens_list:
                    if allergen in cat_value.lower():
                        matched_allergen = allergen
                        break
                break
        if found_category and allergen_category_level:
            st.write(f"**Allergen-Friendly Alternatives:** (Products in '{selected_product.get(f'category_level_{allergen_category_level}', '')}' without '{matched_allergen}')")
            alt_df = get_category_slice(selected_product, allergen_category_level)
            # Exclude products containing any user allergens in ingredients_text.
            pattern = "|".join([re.escape(a) for a in user_allergens_list])
            if pattern:
                alt_df = alt_df[~alt_df["ingredients_text"].str.lower().str.contains(pattern, na=False)]
            alt_df = alt_df[alt_df["code"] != selected_product["code"]]
            if not alt_df.empty:
                st.table(alt_df[["product_name", "brands", "ingredients_text"]].head(5))
            else:
                st.write("No allergen-friendly alternatives found in this category.")
        else:
            # Fall back to FAISS-based recommendations.
            cur_index_list = df.index[df["code"] == selected_product["code"]].tolist()
            if cur_index_list:
                cur_index = cur_index_list[0]
                query_vector = combined_embeddings[cur_index:cur_index+1]
                k = 20  # retrieve extra candidates.
                distances, indices = faiss_index.search(query_vector, k)
                indices_list = indices[0].tolist() if indices.size > 0 else []
                if cur_index in indices_list:
                    indices_list.remove(cur_index)
                candidates = df.iloc[indices_list].copy()
                # Filter candidates based on user's allergens.
                avoid_list = set([a.strip().lower() for a in user_allergens_list])
                def candidate_filter(row):
                    ing_txt = str(row.get("ingredients_text", "")).lower()
                    for allergen in avoid_list:
                        if allergen in ing_txt:
                            return False
                    return True
                filtered_candidates = candidates[candidates.apply(candidate_filter, axis=1)]
                if not filtered_candidates.empty:
                    st.table(filtered_candidates[["product_name", "brands"]].head(5))
                else:
                    st.write("No suitable personalized alternatives were found for this product.")
            else:
                st.write("Error: Could not determine product index for recommendations.")
    else:
        # If no allergens specified, use FAISS-based recommendations directly.
        cur_index_list = df.index[df["code"] == selected_product["code"]].tolist()
        if cur_index_list:
            cur_index = cur_index_list[0]
            query_vector = combined_embeddings[cur_index:cur_index+1]
            k = 20
            distances, indices = faiss_index.search(query_vector, k)
            indices_list = indices[0].tolist() if indices.size > 0 else []
            if cur_index in indices_list:
                indices_list.remove(cur_index)
            candidates = df.iloc[indices_list].copy()
            st.table(candidates[["product_name", "brands"]].head(5))
        else:
            st.write("Error: Could not determine product index for recommendations.")

# --- RADAR CHART: Nutritional Overview by Category ---
st.subheader("Nutritional Overview of Top Food Categories")

# You can limit the dataset to top categories for performance
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
    
st.write("----")
st.write("Developed with NutriWeb – Personalized Food Recommendations")
