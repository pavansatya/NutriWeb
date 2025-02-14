# nutriweb/data_loader.py
import pandas as pd
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

<<<<<<< HEAD
# List of columns to keep
SELECTED_COLS = ['code', 'product_name', 'categories_en', 'ingredients_text',
                 'additives_en', 'nutrition_grade_fr', 'energy_100g', 'fat_100g',
                 'sugars_100g', 'proteins_100g', 'salt_100g', 'carbohydrates_100g',
                 'cholesterol_100g', 'fiber_100g', 'sodium_100g', 'vitamin-a_100g',
                 'vitamin-c_100g', 'vitamin-b1_100g', 'vitamin-b2_100g',
                 'vitamin-pp_100g', 'vitamin-b9_100g', 'iron_100g']

def load_users(filepath=os.path.join(DATA_DIR, "users.csv")):
    return pd.read_csv(filepath)

def load_products(filepath=os.path.join(DATA_DIR, "complete_data_sample.csv"), sample_size=None):
    """
    Loads the complete_data_sample.csv file, keeps only SELECTED_COLS, cleans column names,
    and renames 'categories_en' to 'category' for consistency.
    """
    read_kwargs = {"on_bad_lines": "skip"}
    if sample_size is not None:
        read_kwargs["nrows"] = sample_size
        
    df = pd.read_csv(filepath, usecols=SELECTED_COLS, **read_kwargs)
    
    # Clean column names: strip whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    
    # Rename 'categories_en' to 'category'
    if "categories_en" in df.columns:
        df.rename(columns={"categories_en": "category"}, inplace=True)
    
    # Debug output: print columns and first few rows
    print("DEBUG: Cleaned columns:", df.columns.tolist())
    print("DEBUG: First 5 rows:\n", df.head())
    
    return df
=======
def load_users(filepath=os.path.join(DATA_DIR, "users.csv")):
    return pd.read_csv(filepath)

def load_products(filepath=os.path.join(DATA_DIR, "products.csv"), sample_size=None):
    """
    Loads the products CSV file.
    If sample_size is provided, only that many rows are loaded.
    The on_bad_lines parameter is used to skip rows that cause parsing errors.
    """
    read_kwargs = {"on_bad_lines": "skip"}  # Skip rows with unexpected number of fields
    if sample_size is not None:
        read_kwargs["nrows"] = sample_size
    return pd.read_csv(filepath, **read_kwargs)
>>>>>>> 32767bc6941ed8acc8c8b37a941a7b3b09e3febd
