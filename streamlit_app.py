import os
os.environ.setdefault("USE_TF", "0")  # prevent Keras 3 / tf-keras conflict

import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import faiss
import re
import gdown
from huggingface_hub import hf_hub_download
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# ────────────────────────────────────────────────────
# 1) SESSION STATE INITIALIZATION
# ────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "auth"                # auth → search → recommendations → product_detail/profile
if "selected_product_code" not in st.session_state:
    st.session_state.selected_product_code = None



# ——————————————————————————————————————————
# 2) MongoDB Atlas setup for auth & history
# ——————————————————————————————————————————
@st.cache_resource
def get_db():
    uri = st.secrets["MONGODB_URI"]
    client = MongoClient(uri)
    name = st.secrets.get("MONGO_DB_NAME", "nutriweb_db")
    return client[name]

db = get_db()
users_col   = db["users"]
history_col = db["history"]

def save_profile(uid, profile, pw):
    try:
        users_col.insert_one({ "_id": uid, "password": pw, **profile })
        return True
    except DuplicateKeyError:
        return False

def load_profile(uid):
    return users_col.find_one({"_id": uid})

def append_history(uid, entry):
    history_col.insert_one({"user_id": uid, **entry})


# ─────────────────────────────────
# LOGOUT HELPER
# ─────────────────────────────────
def logout():
    """
    Clears user‐related session_state so the app falls back to the auth screen.
    """
    for key in [
        "authenticated",
        "user_id",
        "profile",
        "page",
        "selected_product_code",
        "recommended_products",
    ]:
        st.session_state.pop(key, None)
# ——————————————————————————————————————————
# 3) AUTH PAGE
# ——————————————————————————————————————————
if st.session_state.page == "auth":
    st.title("🔒 Welcome to NutriWeb")
    st.image("images/nutrition.jpeg", use_container_width=True)
    st.markdown("**Welcome to NutriWeb: Please log in or register to continue.**")
    
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        login_id = st.text_input("User ID", key="login_id")
        login_pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Log In"):
            user = load_profile(login_id)
            if user and user["password"] == login_pw:
                st.session_state.authenticated = True
                st.session_state.user_id = login_id
                st.session_state.profile = {
                    "age": user["age"],
                    "gender": user["gender"],
                    "cholesterol": user["cholesterol"],
                    "blood_pressure": user["blood_pressure"],
                    "allergens": user.get("allergens", []),
                    "dietary_restrictions": user.get("dietary_restrictions", [])
                }
                st.session_state.page = "search"
                
            else:
                st.error("Invalid credentials.")

    with tab_register:
        reg_id = st.text_input("User ID", key="reg_id")
        reg_pw = st.text_input("Password", type="password", key="reg_pw")
        age = st.number_input("Age", 0, 120, 30, key="reg_age")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")
        chol = st.selectbox("Cholesterol", ["Normal", "High"], key="reg_chol")
        bp = st.selectbox("Blood Pressure", ["Normal", "High"], key="reg_bp")
        allergens = st.multiselect(
            "Allergens",
            ["Gluten", "Peanuts", "Soy", "Dairy", "Eggs", "Shellfish", "Fish", "Tree Nuts"],
            key="reg_allergens"
        )
        dietary_restrictions = st.multiselect(
            "Dietary Restrictions", ["Vegetarian", "Vegan"], key="reg_diet"
        )
        if st.button("Register"):
            if not reg_id or not reg_pw:
                st.error("ID & password required.")
            else:
                profile = {
                    "age": age,
                    "gender": gender,
                    "cholesterol": chol,
                    "blood_pressure": bp,
                    "allergens": allergens,
                    "dietary_restrictions": dietary_restrictions
                }
                if save_profile(reg_id, profile, reg_pw):
                    st.success("Registered—now switch to Login.")
                else:
                    st.error("User ID exists.")

    st.stop()  # don't run anything else on the auth page

# ────────────────────────────────────────────────────
# 4) REQUIRE AUTH FOR ALL OTHER PAGES
# ────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.session_state.page = "auth"

# ——————————————————————————————————————————
# 5) Import risk & recommendation modules
# ——————————————————————————————————————————

from nutriweb.assess_risk import classify_product, assess_product_risks
from nutriweb.data_loader import load_cleaned_data, get_product_by_code, get_category_slice
from nutriweb.personalization import get_user_profile, personalize_recommendations
from modules.recommendations import filter_by_allergens, recommend_by_ingredients, recommend_products
from modules.radar_chart import preprocess_data, create_radar_chart_with_dropdown
from modules.allergens import find_allergens 


# ────────────────────────────────
# 6) Load Products & Embeddings
# ────────────────────────────────

@st.cache_data(show_spinner="⏳ Getting things ready... Hang tight!")
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

df, combined_embeddings = load_data(name_weight=0.2)

@st.cache_resource
def create_faiss_index(embeddings: np.ndarray):
    """Build and return a FAISS index for the provided embeddings using L2 distance."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

faiss_index = create_faiss_index(combined_embeddings)
# ——————————————————————————————————————————
# 7) DIETARY EXCLUSION LISTS & HELPERS
# ——————————————————————————————————————————
vegetarian_exclusions = [
    "meat","chicken","beef","pork","fish","shellfish","eggs",
    "shrimp","crab","lobster","gelatin","bacon","lard","turkey"
]
vegan_exclusions = vegetarian_exclusions + [
    "milk","butter","cheese","cream","egg","eggs",
    "honey","whey","casein","yogurt"
]

def format_risk_level(risk: str) -> str:
    if risk == "Avoid":
        return "🔥 Avoid"
    elif risk == "Caution":
        return "⚠️ Caution"
    return "✅ Safe"

def candidate_is_safe(row):
    cls, _, _ = classify_product(
        row.get("ingredients_text",""), row.get("additives_en","")
    )
    return cls in ["Safe","Caution"]

def filter_by_diet(df: pd.DataFrame, diets: list[str]) -> pd.DataFrame:
    if not diets:
        return df
    def ok(row):
        ingr = str(row.get("ingredients_text","")).lower()
        if "vegan" in diets:
            return not any(kw in ingr for kw in vegan_exclusions)
        elif "vegetarian" in diets:
            return not any(kw in ingr for kw in vegetarian_exclusions)
        return True
    return df[df.apply(ok, axis=1)]

# ────────────────────────────────────────────────────
# 8) SEARCH PAGE
# ────────────────────────────────────────────────────
if st.session_state.page == "search":
    _, colp, col_logout = st.columns([7,3,3])
    with colp:
        if st.button("👤My Profile"):
            st.session_state.page = "profile"
    with col_logout:
        st.button("🚪 Logout", on_click=logout)

    #st.title("NutriWeb: Personalized Food Products Recommendations")
    st.markdown("<h1 style='color: green;'>NutriWeb: Personalized Food Products Recommendation System</h41", unsafe_allow_html=True)

    prof = st.session_state.profile
    dietary_restrictions = prof.get("dietary_restrictions", [])  
    allergens            = prof.get("allergens", [])
    high_bp              = (prof.get("blood_pressure") == "High")
    high_chol            = (prof.get("cholesterol")    == "High")

    user_allergens = [a.lower() for a in allergens]
    user_diets     = [d.lower() for d in dietary_restrictions]

    # 1) SELECT
    mode = st.radio("Find by:", ["Product Name","Barcode"])
    q    = st.text_input(f"Enter { 'name' if mode=='Product Name' else 'barcode' }:")
    selected = None
    if q:
        if mode=="Product Name":
            hits = df[df["product_name"].str.contains(q,case=False,na=False)]
            if not hits.empty:
                if len(hits)>1:
                    choice = st.selectbox("Select one", hits["product_name"].unique())
                    if choice:
                        selected = hits[hits["product_name"]==choice].iloc[0]
                else:
                    selected = hits.iloc[0]
            else:
                st.warning("No matches.")
        else:
            hits = df[df["code"]==q.strip()]
            if not hits.empty:
                selected = hits.iloc[0]
                st.success(f"Found: {selected['product_name']}")
            else:
                st.warning("No barcode match.")

    if selected is None:
        st.stop()

    # Risk assessment & history logging
    cls, ing_risks, add_risks = classify_product(
        selected.get("ingredients_text",""), selected.get("additives_en","")
    )
    warnings = []

    ingr_text = str(selected.get("ingredients_text","")).lower()
    raw_allergen_tags = find_allergens(selected.get("ingredients_text",""))
    detected = [tag.split(":",1)[1] for tag in raw_allergen_tags]
    found = [a for a in detected if a in user_allergens]
    if found:
        cls = "Avoid"
        warnings.append(f"Contains allergen(s): {', '.join(found)}")

    diet_violation = False
    if "vegan" in user_diets and any(kw in ingr_text for kw in vegan_exclusions):
        diet_violation = True
    elif "vegetarian" in user_diets and any(kw in ingr_text for kw in vegetarian_exclusions):
        diet_violation = True
    if diet_violation:
        cls = "Avoid"
        warnings.append(f"Not suitable for a {', '.join(dietary_restrictions).lower()} diet.")

    if high_bp:
        sodium_val = selected.get("sodium_100g")
        if (sodium_val is not None and sodium_val > 5.0) or ("salt" in ingr_text):
            cls = "Avoid"
            warnings.append("High sodium — not recommended for high blood pressure.")

    if high_chol:
        sat_val = selected.get("saturated-fat_100g")
        if (sat_val is not None and sat_val > 5.0) or any(
            f in ingr_text for f in ["butter","cream","palm oil","lard"]
        ):
            cls = "Avoid"
            warnings.append("High saturated fat — not recommended for high cholesterol.")

    append_history(st.session_state.user_id, {
        "timestamp":   datetime.utcnow().isoformat(),
        "product_name": selected["product_name"],
        "classification": cls
    })
    
    st.subheader("General Risk Assessment")
    st.write(f"**Classification:** {cls}")
    if warnings:
        st.error("⚠️ Not ideal for your profile.")
        for w in warnings:
            st.warning(w)
            
    
    st.subheader("🔄 Personalized Ingredient-Based Recommendations")   
    recs = recommend_by_ingredients(
        selected.get("ingredients_text",""),
        selected.get("product_name",""),
        df,
        product_code=selected["code"],
        top_n=5,
        allergens_to_avoid=user_allergens,
        name_weight=0.1,
        match_boost=0.2
    )
    if recs is None or recs.empty:
        st.write("No alternatives found.")
    else:
        # 1) Merge back both ingredients_text AND additives_en
        recs = recs.merge(
            df[["product_name","ingredients_text","additives_en"]],
            on="product_name",
            how="left"
        )

        # 2) Filter out any that still contain allergens
        recs = filter_by_allergens(recs, user_allergens)
        # 3) Filter by dietary restrictions
        recs = filter_by_diet(recs, user_diets)
        # 4) Filter out any that re-classify to Avoid
        recs = recs[recs.apply(candidate_is_safe, axis=1)]

        # 5) Dedupe & take top 5
        recs = recs.drop_duplicates("product_name").head(5)

        # 6) Inject the brand column
        brand_map = (
            df[["product_name","brands"]]
            .drop_duplicates(subset="product_name")
            .set_index("product_name")["brands"]
            .to_dict()
        )
        recs["Brands"] = recs["product_name"].map(brand_map)

        # 7) Drop no-longer-needed columns
        recs = recs.drop(columns=["ingredients_text","additives_en","score"], errors="ignore")

        # 8) Display only Product, Brand, Allergens
        display = recs.rename(columns={
            "product_name":"Product",
            "brands":"Brands",
            "allergens_en":"Allergens"
        })[["Product","Brands","Allergens"]]

        st.table(display)

    # Ingredient Risk Analysis
    with st.expander("🧂 Ingredient Risk Analysis", expanded=True):
        if ing_risks:
            df_ir = pd.DataFrame(list(ing_risks.items()), columns=["Ingredient","Risk"])
            df_ir["Risk"] = df_ir["Risk"].apply(format_risk_level)
            st.table(df_ir)
        else:
            st.write("No specific ingredient risks identified.")

    # Additive Risk Analysis
    with st.expander("⚗️ Additive Risk Analysis", expanded=False):
        if add_risks:
            df_ar = pd.DataFrame(list(add_risks.items()), columns=["Additive","Risk"])
            df_ar["Risk"] = df_ar["Risk"].apply(format_risk_level)
            st.table(df_ar)
        else:
            st.write("No additives of concern identified.")

    st.stop()

# ────────────────────────────────────────────────────
# 9) PROFILE PAGE
# ────────────────────────────────────────────────────
if st.session_state.page == "profile":
    if st.button("← Back to Search"):
        st.session_state.page = "search"
    prof = st.session_state.profile
    st.header("📝 My Profile & Search History")
    st.markdown(
        f"- **Age:** {prof['age']}  \n"
        f"- **Gender:** {prof['gender']}  \n"
        f"- **Cholesterol:** {prof['cholesterol']}  \n"
        f"- **Blood Pressure:** {prof['blood_pressure']}  \n"
        f"- **Allergens:** {', '.join(prof['allergens']) or 'None'}  \n"
        f"- **Dietary Restrictions:** {', '.join(prof['dietary_restrictions']) or 'None'}"
    )
    st.subheader("🕘 Scan History")
    hist = list(history_col.find({"user_id": st.session_state.user_id}))
    if not hist:
        st.write("No scans yet.")
    else:
        dfh = pd.DataFrame(hist)[["timestamp","product_name","classification"]]
        st.table(dfh.sort_values("timestamp", ascending=False).reset_index(drop=True))

    st.stop()


st.write("---")
st.write("Developed with Nutriweb - Personalized Food Products Recommendation")     
