# nutriweb/recommendations.py

import pandas as pd

# Load the CSV dataset from the data directory
def load_products(filepath='data/products.csv', sample_size=None):
    df = pd.read_csv(filepath)
    # Clean column names: strip and lowercase
    df.columns = df.columns.str.strip().str.lower()
    # Fill missing key columns with empty strings
    for col in ['ingredients', 'additives_en', 'brands', 'category_level_1',
                'category_level_2', 'category_level_3', 'category_level_4',
                'category_level_5', 'category_level_6']:
        if col in df.columns:
            df[col] = df[col].fillna('')
    # Optionally limit number of rows for testing
    if sample_size is not None:
        df = df.head(sample_size)
    return df

def get_product_by_name(product_name, df):
    """Return the first product that matches the product name (case-insensitive)."""
    matches = df[df['product_name'].str.lower().str.contains(product_name.lower(), na=False)]
    if matches.empty:
        return None
    # Return as a dictionary for convenience
    return matches.iloc[0].to_dict()

def find_alternatives(target_product, df):
    """
    Find up to 5 alternative products that are in the same most specific category.
    Search from category_level_6 (most specific) down to category_level_1.
    If none of the category levels contain a valid value (or if the value is 'Not Specified'),
    fallback to keyword matching on the product name.
    """
    alternatives = []
    # Try from the most specific category (level 6) to the broadest (level 1)
    for level in range(6, 0, -1):
        cat_key = f'category_level_{level}'
        target_cat = target_product.get(cat_key, '').strip().lower()
        # Skip if category is empty or 'not specified'
        if not target_cat or target_cat == "not specified":
            continue
        # Filter for alternatives in the same category at this level
        alt_df = df[df[cat_key].str.lower() == target_cat]
        # Exclude the target product (based on product name)
        alt_df = alt_df[alt_df['product_name'] != target_product['product_name']]
        if not alt_df.empty:
            alternatives = alt_df.head(5).to_dict(orient='records')
            return alternatives
    # Fallback: if no valid category found, use keyword from product name
    keyword = target_product.get('product_name', '').split()[-1].lower()
    alt_df = df[df['product_name'].str.lower().str.contains(keyword, na=False)]
    alt_df = alt_df[alt_df['product_name'] != target_product['product_name']]
    if not alt_df.empty:
        alternatives = alt_df.head(5).to_dict(orient='records')
    return alternatives
