import pandas as pd
import os

# Load the product dataset (using 'data/cleaned_data.csv') ensuring that 'code' is a string.
#PRODUCT_DF = pd.read_csv('useful_data/cleaned_data.csv', dtype={'code': str})
def load_cleaned_data():
    csv_path = os.path.join('useful_data', 'cleaned_data.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found. Ensure it's extracted before calling this function.")
    
    df = pd.read_csv(csv_path, dtype={'code': str})
    df.reset_index(drop=True, inplace=True)
    return df

PRODUCT_DF = load_cleaned_data()

def get_product_by_code(barcode: str):
    """
    Return product details (as a dict) for a given barcode.
    Normalize the barcode by stripping spaces and zero-padding if needed.
    """
    code_str = str(barcode).strip()
    if code_str.isdigit() and len(code_str) < 13:
        code_str = code_str.zfill(13)
    result = PRODUCT_DF[PRODUCT_DF['code'] == code_str]
    if not result.empty:
        return result.iloc[0].to_dict()
    # Fallback: if code starts with zero, try removing it.
    if code_str.startswith('0'):
        result = PRODUCT_DF[PRODUCT_DF['code'] == code_str.lstrip('0')]
        if not result.empty:
            return result.iloc[0].to_dict()
    return None

def get_index_by_code(barcode: str) -> int:
    """Return the DataFrame index for the product matching the barcode."""
    code_str = str(barcode).strip()
    result_idx = PRODUCT_DF.index[PRODUCT_DF['code'] == code_str]
    if len(result_idx) == 0:
        return None
    return result_idx[0]

def get_category_slice(product: dict, level: int):
    """
    Return all products in the same category (specified by category_level_{level}) as the given product.
    If the category field is missing or empty, return the full dataset.
    """
    cat_col = f'category_level_{level}'
    if cat_col not in PRODUCT_DF.columns:
        return PRODUCT_DF
    cat_value = product.get(cat_col)
    if not cat_value:
        return PRODUCT_DF
    return PRODUCT_DF[PRODUCT_DF[cat_col] == cat_value]
