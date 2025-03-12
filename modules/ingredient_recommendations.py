from sentence_transformers import SentenceTransformer
import faiss 
import numpy as np
import pandas as pd

# def recommend_by_ingredients(user_input, df, top_n):
#     """
#     Recommends products based on ingredient similarity using precomputed embeddings.

#     Args:
#         query (str): The product name or ingredient query.
#         data (pd.DataFrame): The dataset containing 'product_name' and 'ingredients_text'.
#         top_n (int): Number of recommendations to return.

#     Returns:
#         pd.DataFrame: A DataFrame containing the top N recommended products.
#     """
#     ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')

#     model = SentenceTransformer('all-MiniLM-L6-v2')

#     dimension = ingredient_embeddings.shape[1]
#     index = faiss.IndexFlatL2(dimension)  
#     index.add(ingredient_embeddings)  

#     query_embedding = model.encode([user_input])

#     distances, indices = index.search(query_embedding, top_n)

#     similar_ingredients = [df.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(df)]

#     recommendations = df[df['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))][['product_name', 'additives_en', 'allergens_en']].head(top_n)
#     return recommendations  


def recommend_by_ingredients(user_input, df, top_n, allergens_to_avoid=None):
    """
    Recommends products based on ingredient similarity using precomputed embeddings while filtering out allergens.

    Args:
        user_input (str): The product name or ingredient query.
        df (pd.DataFrame): The dataset containing 'product_name', 'ingredients_text', and 'allergens_en'.
        top_n (int): Number of recommendations to return.
        allergens_to_avoid (list): List of allergens the user wants to avoid.

    Returns:
        pd.DataFrame: A DataFrame containing the top N recommended products.
    """
    ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')

    model = SentenceTransformer('all-MiniLM-L6-v2')

    dimension = ingredient_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  
    index.add(ingredient_embeddings)  

    query_embedding = model.encode([user_input])

    distances, indices = index.search(query_embedding, top_n * 5)  # Get more results initially

    # Extract similar ingredients from search results
    similar_ingredients = [df.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(df)]

    # Process allergens_en column: Replace "unknown" with empty string and clean values
    df['allergens_en'] = df['allergens_en'].replace("unknown", "").fillna("").str.lower()
    df['allergens_en'] = df['allergens_en'].apply(lambda x: [allergen.replace("en:", "").strip() for allergen in x.split(',') if allergen])

    if allergens_to_avoid:
        allergens_to_avoid = set(map(str.lower, allergens_to_avoid))  # Normalize user input
        df = df[~df['allergens_en'].apply(lambda allergens: any(a in allergens for a in allergens_to_avoid))]  # Filter out products with allergens

    # Filter products based on ingredient similarity
    recommendations = df[df['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))]

    return recommendations[['product_name', 'additives_en', 'allergens_en']].head(top_n)
