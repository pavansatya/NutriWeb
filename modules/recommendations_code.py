from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

def get_primary_category(categories_en):
    if pd.isna(categories_en):
        return None
    return categories_en.split(',')[-1].strip()

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

def recommend_products(bar_code, df, top_n=5, allergens_to_avoid=[]):
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
        return filtered_products[['product_name', 'additives_en', 'allergens_en']].head(top_n)
    
    # Step 5: Fallback to ingredient-based recommendation
    return recommend_by_ingredients(product_row.iloc[0]['ingredients_text'], df, top_n, allergens_to_avoid)

def recommend_by_ingredients(ingredients_text, df, top_n=5, allergens_to_avoid=[]):
    if pd.isna(ingredients_text) or ingredients_text.strip() == "":
        print("⚠️ No ingredients available for ingredient-based recommendations.")
        return None

    # Step 1: Load embeddings & FAISS index
    ingredient_embeddings = np.load('embeddings/ingredient_embeddings.npy')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    dimension = ingredient_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  
    index.add(ingredient_embeddings)  
    
    # Step 2: Find similar products
    query_embedding = model.encode([ingredients_text])
    distances, indices = index.search(query_embedding, top_n * 10)  

    # Step 3: Retrieve products using indices
    similar_ingredients = [df.iloc[i]['ingredients_text'] for i in indices[0] if 0 <= i < len(df)]
    
    recommendations = df[df['ingredients_text'].apply(lambda x: any(ingredient in x for ingredient in similar_ingredients))][['product_name', 'additives_en', 'allergens_en']].head(top_n)
    
    # Step 4: Allergen filtering
    if allergens_to_avoid:
        recommendations = filter_by_allergens(recommendations, allergens_to_avoid)

    recommendations['allergens_en'] = recommendations['allergens_en'].apply(clean_allergens)
    
    return recommendations.head(top_n)
