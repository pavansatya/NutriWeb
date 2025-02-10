# nutriweb/data_loader.py
import pandas as pd
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

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
