# app.py
from flask import Flask, render_template, request
import pandas as pd
from nutriweb.assess_risk import assess_product_risks, classify_product
from nutriweb.recommendations import load_products, get_product_by_name, find_alternatives

app = Flask(__name__)

# Load the full product dataset once at startup
products_df = load_products(sample_size=10000)  # adjust sample_size as needed

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/recommendations', methods=['POST'])
def recommendations_page():
    product_query = request.form.get('product_name', '').strip()
    if not product_query:
        return render_template('recommendations.html', error="Please enter a product name.", product=None, alternatives=None)
    
    # Look up the product by name
    target_product = get_product_by_name(product_query, products_df)
    if target_product is None:
        return render_template('recommendations.html', error=f"No product found matching '{product_query}'.", product=None, alternatives=None)
    
    # Classify the target product based on ingredients and additives
    classification, ing_risks, add_risks = classify_product(target_product.get('ingredients', ''), target_product.get('additives_en', ''))
    
    # Assess detailed risks (for warning)
    risk_details = assess_product_risks(target_product.get('ingredients', ''), target_product.get('additives_en', ''))
    
    # Find alternatives using reverse-hierarchy category search
    alternatives = find_alternatives(target_product, products_df)
    
    # Prepare product details for display
    product_details = {
        "product_name": target_product.get('product_name'),
        "brands": target_product.get('brands'),
        "category_level_1": target_product.get('category_level_1'),
        "classification": classification,
        "ingredients": ing_risks,
        "additives": add_risks,
        "risk_warning": risk_details.get("warning")
    }
    
    return render_template('recommendations.html',
                           product=product_details,
                           alternatives=alternatives,
                           error=None)

if __name__ == '__main__':
    app.run(debug=True)
