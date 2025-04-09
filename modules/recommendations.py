import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer



def get_primary_category(categories_en):
    if pd.isna(categories_en):
        return None
    return categories_en.split(',')[-1].strip()

def clean_allergens(allergens):
    if isinstance(allergens, str):
        allergens = [a.replace('en:', '').strip() for a in allergens.split(',')]
        return ', '.join(allergens)
    return allergens

def filter_by_allergens(products, allergens_to_avoid):
    allergens_to_avoid = [a.lower().strip() for a in allergens_to_avoid]

    def has_allergen(allergens):
        if isinstance(allergens, str):
            allergens = [a.replace('en:', '').lower().strip() for a in allergens.split(',')]
            return any(a in allergens_to_avoid for a in allergens)
        return False

    return products[~products['allergens_en'].apply(has_allergen)]

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r'\W+', ' ', text).lower().strip()

def name_match_boost(input_name, product_names, boost_value=0.2):
    input_clean = normalize_text(input_name)
    return np.array([
        boost_value if input_clean in normalize_text(name) else 0.0
        for name in product_names
    ])

import faiss

def recommend_by_ingredients(ingredients_text, product_name, df, product_code, top_n=5, allergens_to_avoid=[], name_weight=0.3, match_boost=0.2):
    if pd.isna(ingredients_text) or ingredients_text.strip() == "":
        print("⚠️ No ingredients available for ingredient-based recommendations.")
        return None

    # Load embeddings
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')
    name_embeddings = np.load('embeddings/product_name_embeddings.npy')

    ingredient_query = MODEL.encode([ingredients_text])[0]
    name_query = MODEL.encode([product_name])[0]
    combined_query = (1 - name_weight) * ingredient_query + name_weight * name_query

    combined_embeddings = (1 - name_weight) * ingredient_embeddings + name_weight * name_embeddings

    # FAISS indexing
    dimension = combined_query.shape[0]
    index = faiss.IndexFlatL2(dimension)
    index.add(combined_embeddings)

    distances, indices = index.search(np.array([combined_query]), top_n * 20)

    candidate_rows = df.iloc[indices[0]].copy()

    # Exclude the same product based on code
    candidate_rows = candidate_rows[candidate_rows['code'] != product_code]

    scores = -distances[0]
    boost = name_match_boost(product_name, candidate_rows['product_name'], boost_value=match_boost)
    final_scores = scores[:len(candidate_rows)] + boost  # Ensure matching lengths
    candidate_rows['score'] = final_scores

    # Allergen filter
    if allergens_to_avoid:
        candidate_rows = filter_by_allergens(candidate_rows, allergens_to_avoid)

    candidate_rows['allergens_en'] = candidate_rows['allergens_en'].apply(clean_allergens)

    return candidate_rows.sort_values('score', ascending=False)[['product_name', 'additives_en', 'allergens_en']].head(top_n)

def recommend_products(bar_code, df, top_n=5, allergens_to_avoid=[], name_weight=0.3, match_boost=0.2):
    product_row = df[df['code'] == bar_code]

    if product_row.empty:
        print("❌ No product found with the given barcode!")
        return None

    primary_category = get_primary_category(product_row.iloc[0]['categories_en'])

    if primary_category:
        filtered_products = df[df['categories_en'].str.contains(primary_category, na=False)]
        if allergens_to_avoid:
            filtered_products = filter_by_allergens(filtered_products, allergens_to_avoid)
        filtered_products['allergens_en'] = filtered_products['allergens_en'].apply(clean_allergens)
        return filtered_products[['product_name', 'additives_en', 'allergens_en']].head(top_n)

    return recommend_by_ingredients(
        product_row.iloc[0]['ingredients_text'],
        product_row.iloc[0]['product_name'],
        df,
        product_code=bar_code,
        top_n=top_n,
        allergens_to_avoid=allergens_to_avoid,
        name_weight=name_weight,
        match_boost=match_boost
    )
