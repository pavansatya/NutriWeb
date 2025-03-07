from sentence_transformers import SentenceTransformer
import faiss 
import numpy as np
import pandas as pd

def recommend_by_ingredients(user_input, data, top_n=5):
    """
    Recommends products based on ingredient similarity using precomputed embeddings.

    Args:
        query (str): The product name or ingredient query.
        data (pd.DataFrame): The dataset containing 'product_name' and 'ingredients_text'.
        top_n (int): Number of recommendations to return.

    Returns:
        pd.DataFrame: A DataFrame containing the top N recommended products.
    """
    ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')

    model = SentenceTransformer('all-MiniLM-L6-v2')

    dimension = ingredient_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  
    index.add(ingredient_embeddings)  

    query_embedding = model.encode([user_input])

    distances, indices = index.search(query_embedding, top_n)

    similar_ingredients = [data.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(data)]

    recommendations = data[data['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))][['product_name', 'ingredients_text']].head(top_n)

    return recommendations   


