# personalization.py
import pandas as pd

def has_allergy_conflict(user_allergies, product_allergens):
    """
    Checks whether the user's allergies conflict with the product's allergens.
    Both inputs are expected as comma-separated strings.
    Returns True if there is an overlap, otherwise False.
    """
    if pd.isna(user_allergies) or pd.isna(product_allergens):
        return False
    user_allergy_set = {x.strip().lower() for x in user_allergies.split(",")}
    product_allergen_set = {x.strip().lower() for x in product_allergens.split(",")}
    return not user_allergy_set.isdisjoint(product_allergen_set)

def personalized_adjustment(user, product):
    """
    Computes adjustments to the base product score based on user health metrics.
      - Penalizes high saturated fat if the user's cholesterol is high.
      - Penalizes high salt if the user's blood pressure is high.
      - Penalizes products with calories exceeding 30% of the user's daily calorie intake.
    """
    adjustment = 0.0

    if user["cholesterol"] > 200:
        adjustment -= product["saturated_fat"] * 1.0

    if user["blood_pressure"] > 130:
        adjustment -= product["salt"] * 1.0

    if product["calories"] > user["daily_calorie_intake"] * 0.3:
        excess_ratio = (product["calories"] - user["daily_calorie_intake"] * 0.3) / user["daily_calorie_intake"]
        adjustment -= excess_ratio * 10

    return adjustment

def compute_personalized_score(user, product, base_score):
    """
    Computes the final personalized score:
      - If there is an allergen conflict, returns a very low score.
      - Otherwise, adjusts the base score based on user metrics.
    """
    if has_allergy_conflict(user.get("allergies", ""), product.get("allergens", "")):
        return -999  # Exclude product if allergen conflict exists.
    adjustment = personalized_adjustment(user, product)
    return base_score + adjustment
