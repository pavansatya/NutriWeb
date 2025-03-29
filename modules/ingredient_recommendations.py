from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

def get_primary_category(categories_en):
    if pd.isna(categories_en):
        return None
    return categories_en.split(',')[-1].strip()

def find_primary_category_from_matches(top_matches, df):
    for match, _ in top_matches:
        categories_en = df[df['product_name'] == match]['categories_en'].values[0]
        primary_category = get_primary_category(categories_en)
        if primary_category is not None:
            return primary_category, match
    return None, None  

def filter_by_allergens(products, allergens_to_avoid):
    allergens_to_avoid = [allergen.lower().strip() for allergen in allergens_to_avoid]
    
    def has_allergen_to_avoid(allergens):
        if isinstance(allergens, str):
            allergens = [a.replace('en:', '').strip().lower() for a in allergens.split(',')]
            if 'unknown' in allergens:
                return False  
        return any(allergen in allergens_to_avoid for allergen in allergens)
    
    return products[~products['allergens_en'].apply(has_allergen_to_avoid)]

def clean_allergens(allergens):
    if isinstance(allergens, str):
        allergens = [a.replace('en:', '').strip() for a in allergens.split(',')]
        return ', '.join(allergens)
    return allergens 

def recommend_products(user_input, df, top_n, allergens_to_avoid=[]):
    top_matches = [(row['product_name'], 1.0) for _, row in df.iterrows() if user_input.lower() in row['product_name'].lower()][:5]
    
    primary_category, matched_product = find_primary_category_from_matches(top_matches, df)
    
    if primary_category is None:
        return recommend_by_ingredients(user_input, df, top_n=top_n, allergens_to_avoid=allergens_to_avoid)
    
    filtered_products = df[df['categories_en'].str.contains(primary_category, na=False)]
    
    if allergens_to_avoid:
        filtered_products = filter_by_allergens(filtered_products, allergens_to_avoid)
    
    return filtered_products[['product_name', 'additives_en', 'allergens_en']].head(top_n)


def recommend_by_ingredients(user_input, df, top_n, allergens_to_avoid=None):
    
    ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    dimension = ingredient_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  
    index.add(ingredient_embeddings)  

    query_embedding = model.encode([user_input])

    distances, indices = index.search(query_embedding, top_n*10)

    similar_ingredients = [df.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(df)]
    
    recommendations = df[df['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))][['product_name', 'additives_en', 'allergens_en']].head(top_n)
    
    if allergens_to_avoid:
        recommendations = filter_by_allergens(recommendations, allergens_to_avoid)

    recommendations['allergens_en'] = recommendations['allergens_en'].apply(clean_allergens)
    return recommendations.head(top_n)