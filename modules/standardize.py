import pandas as pd

def standardize(brands_string):
    brands = brands_string.lower()
    brands_list = [brand.strip() for brand in brands.split(',')]
    unique_brands = set(brands_list)
    sorted_brands = sorted(unique_brands)
    return ', '.join(sorted_brands)