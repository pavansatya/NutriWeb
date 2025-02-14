<<<<<<< HEAD
# nutriweb/scoring.py
import pandas as pd

NUTRITION_WEIGHT = 0.6
ADDITIVES_WEIGHT = 0.3
GRADE_WEIGHT = 0.1 

def calculate_nutrition_score(row):
    """
    Calculates a nutrition score using key nutrient values.
    Negative factors: fat_100g, sugars_100g, salt_100g, cholesterol_100g.
    Positive factors: fiber_100g, proteins_100g.
    (Other nutrients can be added as needed.)
    We compute: score = 60 - (negative factors) + (positive factors)
    """
    negative = (row.get("fat_100g", 0) * 2 +
                row.get("sugars_100g", 0) * 2.5 +
                row.get("salt_100g", 0) * 3 +
                row.get("cholesterol_100g", 0) * 2)
    
    positive = (row.get("fiber_100g", 0) * 3 +
                row.get("proteins_100g", 0) * 2)
    
    score = 60 - negative + positive
    # Clip the score between 0 and 100
    return max(0, min(100, score))

def calculate_additive_score(row):
    """
    Calculates an additive penalty score based on the number of additives.
    Assumes 'additives_en' is a comma-separated string of additives.
    Each additive reduces the score by 2 points (up to a maximum penalty of 30).
    """
    additives_text = row.get("additives_en", "")
    if pd.isna(additives_text) or additives_text.strip() == "":
        count = 0
    else:
        count = len(additives_text.split(","))
    reduction = count * 2
    return max(0, 30 - reduction)

def grade_score(row):
    """
    Converts the nutrition_grade_fr (a letter) to a numeric bonus.
    Mapping: a->10, b->8, c->6, d->4, e->2; if missing, bonus=0.
    """
    grade_map = {'a': 10, 'b': 8, 'c': 6, 'd': 4, 'e': 2}
    grade = row.get("nutrition_grade_fr", "")
    if pd.isna(grade) or grade.strip() == "":
        return 0
    return grade_map.get(grade.strip().lower(), 0)

def compute_base_health_score(product_row):
    """
    Combines the nutrition score, additive score, and grade bonus into a base score.
    """
    nutrition = calculate_nutrition_score(product_row)
    additive = calculate_additive_score(product_row)
    grade_bonus = grade_score(product_row)
    
    base_score = (nutrition * NUTRITION_WEIGHT +
                  additive * ADDITIVES_WEIGHT +
                  grade_bonus * GRADE_WEIGHT)
    return base_score
=======
# scoring.py

# Weight constants for the scoring system.
NUTRITION_WEIGHT = 0.6
ADDITIVES_WEIGHT = 0.3
ORGANIC_WEIGHT = 0.1

def calculate_nutrition_score(row):
    """
    Calculates a nutritional score (max 60) based on:
      - Negative factors: sugar, saturated fat, salt.
      - Positive factors: fiber, protein, fruit & vegetables percentage.
    The calories factor has been removed.
    """
    # Removed: row["calories"] * 0.02
    negative_factors = row["sugar"] * 2 + row["saturated_fat"] * 3 + row["salt"] * 1.5
    positive_factors = row["fiber"] * 3 + row["protein"] * 2 + row["fruit_vegetables_pct"] * 1.5
    score = 60 - negative_factors + positive_factors
    return max(0, min(60, score))

def calculate_additive_score(row):
    """
    Calculates an additive score (max 30) by subtracting points 
    for each harmful additive.
    Assumes that the 'additives' column contains the count of harmful additives.
    """
    harmful_additives = row["additives"]
    return max(0, 30 - harmful_additives * 3)

def calculate_organic_score(row):
    """
    Returns a bonus of 10 if the product is organic.
    """
    return 10 if row["organic"] == 1 else 0

def compute_base_health_score(product_row):
    """
    Computes the overall base health score (out of 100) for a product.
    """
    nutrition = calculate_nutrition_score(product_row)
    additive = calculate_additive_score(product_row)
    organic = calculate_organic_score(product_row)
    health_score = (nutrition * NUTRITION_WEIGHT +
                    additive * ADDITIVES_WEIGHT +
                    organic * ORGANIC_WEIGHT)
    return health_score
>>>>>>> 32767bc6941ed8acc8c8b37a941a7b3b09e3febd
