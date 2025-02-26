# app.py
from flask import Flask, render_template, request
from nutriweb.data_loader import load_products
from nutriweb.scoring import compute_base_health_score
from nutriweb.personalization import compute_personalized_score, classify_score

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Build a user profile dictionary from form inputs.
            user = {
                "age": int(request.form.get("age")),
                "gender": request.form.get("gender"),
                "height": float(request.form.get("height")),
                "weight": float(request.form.get("weight")),
                "bmi": float(request.form.get("bmi")),
                "daily_calorie_intake": int(request.form.get("daily_calorie_intake")),
                "cholesterol": int(request.form.get("cholesterol")),
                "blood_pressure": int(request.form.get("blood_pressure")),
                "allergies": request.form.get("allergies", ""),
                "diettype": request.form.get("diettype", "")  # New field for diet type
            }
        except Exception as e:
            return render_template("index.html", error="Invalid input. Please check your entries.")
        
        product_query = request.form.get("product_name", "").strip()
        if not product_query:
            return render_template("index.html", error="Please enter a product name.")
        
        pref_category = request.form.get("category", "").strip()
        
        # Load products from the sample dataset (complete_data_sample.csv)
        products_df = load_products()  # Loads the entire file (already filtered to selected columns)
        if pref_category:
            products_df = products_df[products_df["category"].str.lower() == pref_category.lower()]
        
        # Find the target product (case-insensitive partial match on product_name)
        target_df = products_df[products_df["product_name"].str.contains(product_query, case=False, na=False)]
        if target_df.empty:
            return render_template("index.html", error=f"No product found matching '{product_query}'.")
        
        target_product = target_df.iloc[0]
        target_base = compute_base_health_score(target_product)
        target_score = compute_personalized_score(user, target_product, target_base)
        target_class = classify_score(target_score)
        
        # Compute base and personalized scores for all products.
        products_df["base_health_score"] = products_df.apply(lambda row: compute_base_health_score(row), axis=1)
        products_df["personalized_score"] = products_df.apply(
            lambda row: compute_personalized_score(user, row, row["base_health_score"]), axis=1
        )
        # Create a classification column.
        products_df["classification"] = products_df["personalized_score"].apply(classify_score)
        
        recommendations = []
        # If target is not safe, suggest alternatives that are classified as Safe.
        if target_class in ["Caution", "Avoid"]:
            # Filter for products in the same category that are Safe.
            category_mask = products_df["category"].str.lower() == target_product["category"].lower()
            # Recommend alternatives that are higher than the target product's score,
            # regardless of classification.
            alternatives = products_df[(products_df["personalized_score"] > target_score) & category_mask]
            # Add the target product to the recommendations if it's classified as Safe. 
            recommendations = alternatives.sort_values("personalized_score", ascending=False).head(5).to_dict(orient="records")
        # Optionally, if the product is safe, you could still show similar products (optional).
        
        return render_template("recommendations.html",
                               target=target_product.to_dict(),
                               target_score=target_score,
                               target_class=target_class,
                               recommendations=recommendations)
    return render_template("index.html")

@app.route("/debug")
def debug():
    # For debugging: display the first 10 rows of the dataset.
    sample = load_products(sample_size=100)
    return sample.head(10).to_html()

if __name__ == "__main__":
    app.run(debug=True)
