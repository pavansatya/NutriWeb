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
