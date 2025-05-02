from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

def get_primary_category(categories_en):
    """
    Extracts the last (most specific) category from a comma-separated category string.

    Parameters:
        categories_en (str): A comma-separated string of category names.

    Returns:
        str or None: The last category in the list, or None if input is NaN.
    """
    if pd.isna(categories_en):
        return None
    return categories_en.split(',')[-1].strip()

def filter_by_allergens(products, allergens_to_avoid):
    """
    Filters out products that contain any of the specified allergens, excluding 'unknown' entries.

    Parameters:
        products (pd.DataFrame): DataFrame containing a column 'allergens_en'.
        allergens_to_avoid (list): List of allergen strings to exclude.

    Returns:
        pd.DataFrame: Filtered DataFrame excluding products with matching allergens.
    """
    allergens_to_avoid = [allergen.lower().strip() for allergen in allergens_to_avoid]
    
    def has_allergen_to_avoid(allergens):
        if isinstance(allergens, str):
            allergens = [a.replace('en:', '').strip().lower() for a in allergens.split(',')]
            if 'unknown' in allergens:
                return False  
        return any(allergen in allergens_to_avoid for allergen in allergens)
    
    return products[~products['allergens_en'].apply(has_allergen_to_avoid)]

def clean_allergens(allergens):
    """
    Removes 'en:' prefix and trims whitespace from a comma-separated string of allergens.

    Parameters:
        allergens (str or any): Comma-separated allergen string, or any other type.

    Returns:
        str or original input: Cleaned allergen string or original input if not a string.
    """
    if isinstance(allergens, str):
        allergens = [a.replace('en:', '').strip() for a in allergens.split(',')]
        return ', '.join(allergens)
    return allergens 

def recommend_products(bar_code, df, top_n=5, allergens_to_avoid=[]):
    """
    Recommends similar products based on the primary category of a given product identified by barcode.
    Falls back to ingredient-based similarity if no category is found.

    Parameters:
        bar_code (str or int): Barcode of the reference product.
        df (pd.DataFrame): DataFrame containing product data.
        top_n (int): Number of recommendations to return.
        allergens_to_avoid (list): List of allergens to exclude in recommendations.

    Returns:
        pd.DataFrame or None: Recommended products as a DataFrame, or None if the barcode is not found.
    """
    # Step 1: Find the exact product by barcode
    product_row = df[df['code'] == bar_code]
    
    if product_row.empty:
        print("❌ No product found with the given barcode!")
        return None
    
    # Step 2: Get primary category
    primary_category = get_primary_category(product_row.iloc[0]['categories_en'])
    
    # Step 3: Category Filtering
    if primary_category:
        filtered_products = df[df['categories_en'].str.contains(primary_category, na=False)]
        
        if allergens_to_avoid:
            filtered_products = filter_by_allergens(filtered_products, allergens_to_avoid)

        # Step 4: Return top products
        filtered_products['allergens_en'] = filtered_products['allergens_en'].apply(clean_allergens)
        return filtered_products[['product_name', 'additives_en', 'allergens_en', 'nutrition_grade_fr']].head(top_n)
    
    # Step 5: Fallback to ingredient-based recommendation
    return recommend_by_ingredients(product_row.iloc[0]['ingredients_text'], df, top_n, allergens_to_avoid)

def recommend_by_ingredients(ingredients_text, df, top_n=5, allergens_to_avoid=[]):
    """
    Recommends products based on similarity of ingredient embeddings using FAISS index search.

    Parameters:
        ingredients_text (str): Ingredient string of the reference product.
        df (pd.DataFrame): DataFrame containing product and ingredient information.
        top_n (int): Number of similar products to recommend.
        allergens_to_avoid (list): List of allergens to filter from results.

    Returns:
        pd.DataFrame or None: Recommended products as a DataFrame, or None if ingredients are not available.
    """
    if pd.isna(ingredients_text) or ingredients_text.strip() == "":
        print("⚠️ No ingredients available for ingredient-based recommendations.")
        return None

    # Step 1: Load embeddings & FAISS index
    ingredient_embeddings = np.load('/Users/krishvenigalla/Desktop/embeddings/ingredient_embeddings.npy')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    dimension = ingredient_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  
    index.add(ingredient_embeddings)  
    
    # Step 2: Find similar products
    query_embedding = model.encode([ingredients_text])
    distances, indices = index.search(query_embedding, top_n * 10)  

    # Step 3: Retrieve products using indices
    similar_ingredients = [df.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(df)]
    
    recommendations = df[df['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))][['product_name', 'additives_en', 'allergens_en' 'nutrition_grade_fr']].head(top_n)
    
    # Step 4: Allergen filtering
    if allergens_to_avoid:
        recommendations = filter_by_allergens(recommendations, allergens_to_avoid)

    recommendations['allergens_en'] = recommendations['allergens_en'].apply(clean_allergens)
    
    return recommendations.head(top_n)



