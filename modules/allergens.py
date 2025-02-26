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
    if pd.isna(ingredients):
        return []
    
    allergens_found = []
    for allergen, keywords in allergen_mapping.items():
        for keyword in keywords:
            # Use regex to match whole words, case-insensitive
            if re.search(rf'\b{re.escape(keyword)}\b', str(ingredients), flags=re.IGNORECASE):
                allergens_found.append(f'en:{allergen}')
                break  # Avoid adding duplicates
    return allergens_found


# Function to fill missing allergens based on product name and ingredients
def fill_allergens(row):
    if pd.isna(row['allergens_en']):
        # Check product name for allergens using regex
        allergens_from_name = []
        for allergen, keywords in allergen_mapping.items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', str(row['product_name']), flags=re.IGNORECASE):
                    allergens_from_name.append(f'en:{allergen}')
                    break
        
        # Check ingredients for allergens using regex
        allergens_from_ingredients = find_allergens(row['ingredients_text'])
        
        # Combine allergens from name and ingredients
        all_allergens = list(set(allergens_from_name + allergens_from_ingredients))
        
        # Return the allergens as a comma-separated string
        return ', '.join(all_allergens) if all_allergens else None
    return row['allergens_en']


