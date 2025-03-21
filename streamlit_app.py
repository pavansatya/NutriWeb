# streamlit_app.py
import streamlit as st
import pandas as pd
from nutriweb.assess_risk import classify_product, assess_product_risks
from nutriweb.recommendations import load_products, get_product_by_name, find_alternatives

# Load data once
@st.cache_data
def load_data():
    return load_products('data/products.csv')

df = load_data()

st.title("NutriWeb: Personalized Food Recommendations")

product_query = st.text_input("Enter Product Name:")

if st.button("Get Recommendations"):
    if not product_query:
        st.warning("Please enter a product name.")
    else:
        product = get_product_by_name(product_query, df)
        
        if not product:
            st.error("No product found with that name.")
        else:
            classification, ing_risks, add_risks = classify_product(product['ingredients'], product['additives_en'])
            risk_details = assess_product_risks(product['ingredients'], product['additives_en'])

            st.subheader(product['product_name'])
            st.write(f"**Brand:** {product['brands']}")
            st.write(f"**Classification:** {classification}")

            if risk_details['warning']:
                st.warning(risk_details['warning'])

            st.write("**Ingredients Risk:**")
            st.table(pd.DataFrame(ing_risks, columns=['Ingredient', 'Risk']))

            st.write("**Additives Risk:**")
            st.table(pd.DataFrame(add_risks, columns=['Additive', 'Risk']))

            if classification != "Safe":
                alternatives = find_alternatives(product, df)
                if alternatives:
                    st.write("### Safer Alternatives:")
                    alt_df = pd.DataFrame(alternatives)[['product_name', 'brands']]
                    st.table(alt_df)
                else:
                    st.info("No safer alternatives found.")

