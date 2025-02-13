# app.py
import pandas as pd
from flask import Flask, render_template, request
from nutriweb.data_loader import load_products
from nutriweb.scoring import compute_base_health_score
from nutriweb.personalization import compute_personalized_score

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Create a user profile dictionary from form inputs.
            user = {
                "age": int(request.form.get("age")),
                "gender": request.form.get("gender"),
                "height": float(request.form.get("height")),
                "weight": float(request.form.get("weight")),
                "bmi": float(request.form.get("bmi")),
                "daily_calorie_intake": int(request.form.get("daily_calorie_intake")),
                "cholesterol": int(request.form.get("cholesterol")),
                "blood_pressure": int(request.form.get("blood_pressure")),
                "allergies": request.form.get("allergies", "")
            }
        except Exception as e:
            return render_template("index.html", error="Invalid input. Please check your entries.")
        
        product_query = request.form.get("product_name", "").strip()
        if not product_query:
            return render_template("index.html", error="Please enter a product name.")
        
        # Optionally filter by preferred category (if provided)
        pref_category = request.form.get("category", "").strip()
        
        # Load products from the sample dataset (complete_data_sample.csv)
        products_df = load_products()  # Uses all rows from the sample dataset
        if pref_category:
            products_df = products_df[products_df["category"].str.lower() == pref_category.lower()]
        
        # Find the target product by matching product_name (case-insensitive partial match)
        target_df = products_df[products_df["product_name"].str.contains(product_query, case=False, na=False)]
        if target_df.empty:
            return render_template("index.html", error=f"No product found matching '{product_query}'.")
        
        # Use the first matching product as the target.
        target_product = target_df.iloc[0]
        target_base = compute_base_health_score(target_product)
        target_score = compute_personalized_score(user, target_product, target_base)
        
        # Compute base and personalized scores for all products.
        products_df["base_health_score"] = products_df.apply(lambda row: compute_base_health_score(row), axis=1)
        products_df["personalized_score"] = products_df.apply(
            lambda row: compute_personalized_score(user, row, row["base_health_score"]), axis=1
        )
        
        # Filter to products in the same category as the target.
        category_mask = products_df["category"].str.lower() == target_product["category"].lower()
        # Recommend alternatives with a higher personalized score than the target.
        recommendations_df = products_df[
            (products_df["personalized_score"] > target_score) & category_mask
        ].sort_values("personalized_score", ascending=False).head(5)
        
        recommendations = recommendations_df.to_dict(orient="records")
        
        return render_template("recommendations.html",
                               target=target_product.to_dict(),
                               target_score=target_score,
                               recommendations=recommendations)
    return render_template("index.html")

@app.route("/debug")
def debug():
    # For debugging: display the first 10 rows of the dataset.
    sample = load_products(sample_size=100)
    return sample.head(10).to_html()

if __name__ == "__main__":
    app.run(debug=True)
