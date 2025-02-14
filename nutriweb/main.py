# nutriweb/main.py
<<<<<<< HEAD
import pandas as pd
=======
>>>>>>> 32767bc6941ed8acc8c8b37a941a7b3b09e3febd
from nutriweb.recommendations import personalized_recommendations
from nutriweb.data_loader import load_products  # Just for testing purposes

def main():
    # For testing: load only a sample of 100 rows.
    sample_products = load_products(sample_size=100)
    print("Sample Products:")
    print(sample_products.head())

    # Now, run the recommendation system normally (which may load all rows)
    user_id_example = 1
    category = "Cereal"  # Or None for all categories
    recommendations = personalized_recommendations(user_id_example, category=category, top_n=5)
    if recommendations is not None and not recommendations.empty:
        print(f"Personalized recommendations for user {user_id_example}:")
        print(recommendations)
    else:
        print("No recommendations found.")

if __name__ == "__main__":
    main()
