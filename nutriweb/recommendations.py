# recommendations.py
import pandas as pd
from nutriweb.data_loader import load_users, load_products
from nutriweb.scoring import compute_base_health_score
from nutriweb.personalization import compute_personalized_score

def personalized_recommendations(user_id, category=None, top_n=5):
    """
    Generates personalized product recommendations for a given user.
    
    Parameters:
      - user_id: The identifier of the user.
      - category: (Optional) A product category to filter by.
      - top_n: Number of recommendations to return.
    
    Returns:
      A DataFrame with the top recommended products.
    """
    users_df = load_users()
    products_df = load_products()

    # Compute the base health score for each product.
    if "base_health_score" not in products_df.columns:
        products_df["base_health_score"] = products_df.apply(lambda row: compute_base_health_score(row), axis=1)
    
    # Retrieve the user data.
    user = users_df[users_df["user_id"] == user_id]
    if user.empty:
        print("User not found.")
        return None
    user = user.iloc[0]

    # Filter by category if provided.
    if category:
        products_subset = products_df[products_df["category"] == category].copy()
    else:
        products_subset = products_df.copy()

    # Compute the personalized score for each product.
    products_subset["personalized_score"] = products_subset.apply(
        lambda row: compute_personalized_score(user, row, row["base_health_score"]), axis=1
    )

    # Filter out products with low scores (e.g., allergen conflicts).
    filtered_products = products_subset[products_subset["personalized_score"] > 0]

    # Sort products by personalized score in descending order.
    recommended_products = filtered_products.sort_values(by="personalized_score", ascending=False)

    return recommended_products.head(top_n)[["product_name", "category", "personalized_score"]]
