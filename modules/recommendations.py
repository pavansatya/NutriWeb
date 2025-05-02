import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


def get_primary_category(categories_en):
    """
    Extracts the most specific (last) category from a comma-separated category string.

    Parameters:
        categories_en (str): Comma-separated string of product categories.

    Returns:
        str or None: The last category in the string, or None if input is NaN.
    """
    if pd.isna(categories_en):
        return None
    return categories_en.split(',')[-1].strip()

def clean_allergens(allergens):
    """
    Cleans allergen strings by removing 'en:' prefix and trimming whitespace.

    Parameters:
        allergens (str or any): Allergen string with optional 'en:' prefixes, or other type.

    Returns:
        str or original input: Cleaned, comma-separated allergen names or original input if not a string.
    """
    if isinstance(allergens, str):
        allergens = [a.replace('en:', '').strip() for a in allergens.split(',')]
        return ', '.join(allergens)
    return allergens

def filter_by_allergens(products, allergens_to_avoid):
    """
    Filters out products that contain any of the specified allergens.

    Parameters:
        products (pd.DataFrame): DataFrame containing an 'allergens_en' column.
        allergens_to_avoid (list): List of allergens to avoid.

    Returns:
        pd.DataFrame: Filtered DataFrame excluding products with matching allergens.
    """
    allergens_to_avoid = [a.lower().strip() for a in allergens_to_avoid]

    def has_allergen(allergens):
        if isinstance(allergens, str):
            allergens = [a.replace('en:', '').lower().strip() for a in allergens.split(',')]
            return any(a in allergens_to_avoid for a in allergens)
        return False

    return products[~products['allergens_en'].apply(has_allergen)]

def normalize_text(text):
    """
    Normalizes text by removing non-alphanumeric characters, lowercasing, and stripping whitespace.

    Parameters:
        text (str): Input text string.

    Returns:
        str: Normalized version of the input text, or empty string if input is not a string.
    """
    if not isinstance(text, str):
        return ""
    return re.sub(r'\W+', ' ', text).lower().strip()

def name_match_boost(input_name, product_names, boost_value=0.2):
    """
    Applies a similarity boost to products whose names contain the input name (after normalization).

    Parameters:
        input_name (str): The product name to match.
        product_names (iterable): List or Series of product names to compare.
        boost_value (float): Score to add for matching products.

    Returns:
        np.ndarray: Array of boost values corresponding to the input product names.
    """
    input_clean = normalize_text(input_name)
    return np.array([
        boost_value if input_clean in normalize_text(name) else 0.0
        for name in product_names
    ])


def recommend_by_ingredients(ingredients_text, product_name, df, product_code, top_n=5, allergens_to_avoid=[], name_weight=0.3, match_boost=0.2):
    """
    Recommends similar products based on ingredient and name embeddings using FAISS and cosine similarity.

    Parameters:
        ingredients_text (str): Ingredients of the reference product.
        product_name (str): Name of the reference product.
        df (pd.DataFrame): DataFrame of product data.
        product_code (str or int): Barcode of the reference product to exclude from results.
        top_n (int): Number of top recommendations to return.
        allergens_to_avoid (list): List of allergens to filter out.
        name_weight (float): Weight to combine ingredient and name embeddings.
        match_boost (float): Boost to apply if product name closely matches.

    Returns:
        pd.DataFrame or None: Top recommended products as a DataFrame or None if ingredients are unavailable.
    """
    if pd.isna(ingredients_text) or ingredients_text.strip() == "":
        print("⚠️ No ingredients available for ingredient-based recommendations.")
        return None

    MODEL = SentenceTransformer('all-MiniLM-L6-v2')

    # Load and normalize precomputed embeddings
    #Change the path to your local directory where the embeddings are stored
    ingredient_embeddings = np.load('/Users/krishvenigalla/Desktop/NutriWeb_clone/embeddings/ingredient_embeddings.npy')
    name_embeddings = np.load('/Users/krishvenigalla/Desktop/NutriWeb_clone/embeddings/product_name_embeddings.npy')

    # Normalize the loaded embeddings
    def normalize_matrix(m):
        return m / np.linalg.norm(m, axis=1, keepdims=True)

    ingredient_embeddings = normalize_matrix(ingredient_embeddings)
    name_embeddings = normalize_matrix(name_embeddings)

    # Combine normalized embeddings, then normalize again
    combined_embeddings = (1 - name_weight) * ingredient_embeddings + name_weight * name_embeddings
    combined_embeddings = normalize_matrix(combined_embeddings)

    # Encode and normalize queries
    ingredient_query = MODEL.encode([ingredients_text], normalize_embeddings=True)[0]
    name_query = MODEL.encode([product_name], normalize_embeddings=True)[0]

    combined_query = (1 - name_weight) * ingredient_query + name_weight * name_query
    combined_query = combined_query / np.linalg.norm(combined_query)

    # FAISS search with cosine similarity
    dimension = combined_query.shape[0]
    index = faiss.IndexFlatIP(dimension)
    index.add(combined_embeddings)

    distances, indices = index.search(np.array([combined_query]), top_n * 20)
    candidate_rows = df.iloc[indices[0]].copy()
    candidate_rows = candidate_rows[candidate_rows['code'] != product_code]

    scores = distances[0]
    boost = name_match_boost(product_name, candidate_rows['product_name'], boost_value=match_boost)
    final_scores = scores[:len(candidate_rows)] + boost
    candidate_rows['score'] = final_scores

    if allergens_to_avoid:
        candidate_rows = filter_by_allergens(candidate_rows, allergens_to_avoid)

    candidate_rows['allergens_en'] = candidate_rows['allergens_en'].apply(clean_allergens)

    return candidate_rows.sort_values('score', ascending=False)[['product_name', 'additives_en', 'allergens_en', 'nutrition_grade_fr']].head(top_n)


def recommend_products(bar_code, df, top_n=5, allergens_to_avoid=[], name_weight=0.3, match_boost=0.2):
    """
    Recommends products similar to the one identified by barcode, based on category or ingredients.

    Parameters:
        bar_code (str or int): Barcode of the product to find recommendations for.
        df (pd.DataFrame): DataFrame containing product information.
        top_n (int): Number of recommendations to return.
        allergens_to_avoid (list): Allergens to filter out from results.
        name_weight (float): Weight between ingredient and name similarity.
        match_boost (float): Boost for matching product names.

    Returns:
        pd.DataFrame or None: DataFrame of recommended products or None if the product is not found.
    """
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
        return filtered_products[['product_name', 'additives_en', 'allergens_en', 'nutrition_grade_fr']].head(top_n)

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

