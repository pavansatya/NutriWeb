import re
import pandas as pd 

# Define a mapping of allergens and their common variations
allergen_mapping = {
    'milk': ['milk', 'dairy', 'cream', 'butter', 'cheese', 'yogurt'],
    'peanuts': ['peanut', 'peanuts'],
    'tree nuts': ['almond', 'cashew', 'walnut', 'pecan', 'pistachio', 'hazelnut', 'macadamia', 'brazil nut'],
    'eggs': ['egg', 'eggs', 'egg white', 'egg yolk'],
    'wheat': ['wheat', 'flour', 'bread', 'pasta', 'cereal'],
    'soy': ['soy', 'soya', 'tofu', 'soybean'],
    'fish': ['fish', 'salmon', 'tuna', 'cod', 'sardine'],
    'shellfish': ['shrimp', 'prawn', 'crab', 'lobster', 'clam', 'oyster'],
    'sesame': ['sesame', 'sesame seed', 'tahini'],
}


# Function to identify allergens in the ingredients column using regex
def find_allergens(ingredients):
    """
    Identifies known allergens in a given ingredient text using keyword matching.

    Parameters:
        ingredients (str): A string containing the ingredients list.

    Returns:
        list: A list of allergens found in the ingredient text, formatted as 'en:<allergen>'.
              Returns an empty list if no allergens are found or input is NaN.
    """
    if pd.isna(ingredients):
        return []
    
    allergens_found = []
    for allergen, keywords in allergen_mapping.items():
        for keyword in keywords:
            if re.search(rf'\b{re.escape(keyword)}\b', str(ingredients), flags=re.IGNORECASE):
                allergens_found.append(f'en:{allergen}')
                break  
    return allergens_found


# Function to fill missing allergens based on product name and ingredients
def fill_allergens(row):
    """
    Fills missing 'allergens_en' values in a DataFrame row by detecting allergens
    from 'product_name' and 'ingredients_text'.

    Parameters:
        row (pd.Series): A row from a DataFrame containing 'product_name',
                         'ingredients_text', and 'allergens_en' columns.

    Returns:
        str or None: A comma-separated string of detected allergens in 'en:<allergen>' format,
                     or the existing 'allergens_en' value if already present.
    """
    if pd.isna(row['allergens_en']):
        allergens_from_name = []
        for allergen, keywords in allergen_mapping.items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', str(row['product_name']), flags=re.IGNORECASE):
                    allergens_from_name.append(f'en:{allergen}')
                    break
        
        allergens_from_ingredients = find_allergens(row['ingredients_text'])
        
        all_allergens = list(set(allergens_from_name + allergens_from_ingredients))
        
        return ', '.join(all_allergens) if all_allergens else None
    return row['allergens_en']


