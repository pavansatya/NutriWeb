import pandas as pd

def standardize(brands_string):
    """
    Standardizes a comma-separated string of brand names by lowercasing, removing duplicates, and sorting alphabetically.

    Parameters:
        brands_string (str): A comma-separated string of brand names.

    Returns:
        str: A standardized, comma-separated string of unique brand names in lowercase and sorted order.
    """
    brands = brands_string.lower()
    brands_list = [brand.strip() for brand in brands.split(',')]
    unique_brands = set(brands_list)
    sorted_brands = sorted(unique_brands)
    return ', '.join(sorted_brands)