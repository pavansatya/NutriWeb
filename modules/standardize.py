import pandas as pd

def standardize(brands_string):
    # Convert to lowercase
    brands = brands_string.lower()
    # Split by comma and strip whitespace
    brands_list = [brand.strip() for brand in brands.split(',')]
    # Remove duplicates by converting to a set
    unique_brands = set(brands_list)
    # Sort the allergens
    sorted_brands = sorted(unique_brands)
    # Join back to a string
    return ', '.join(sorted_brands)