<<<<<<< HEAD
# nutriweb/personalization.py
import pandas as pd

def has_allergy_conflict(user_allergies, ingredients_text):
    """
    Checks if any of the allergens provided by the user appear in the ingredients text.
    Both inputs are assumed to be comma-separated strings.
    """
    if pd.isna(user_allergies) or user_allergies.strip() == "":
        return False
    user_allergy_set = {a.strip().lower() for a in user_allergies.split(",")}
    if pd.isna(ingredients_text) or ingredients_text.strip() == "":
        return False
    ingredients_lower = ingredients_text.lower()
    for allergen in user_allergy_set:
        if allergen in ingredients_lower:  
            return True
    return False 

def personalized_adjustment(user, product):
    """
    Adjusts the product's score based on user health metrics.
    For example, if the user has high cholesterol, penalize products with high cholesterol_100g.
    Similarly, if blood pressure is high, penalize high salt_100g.
    """
    adjustment = 0.0
    if user["cholesterol"] > 200:
        adjustment -= product.get("cholesterol_100g", 0) * 1.0
    if user["blood_pressure"] > 130:
        adjustment -= product.get("salt_100g", 0) * 1.0
=======
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

>>>>>>> 32767bc6941ed8acc8c8b37a941a7b3b09e3febd
    return adjustment

def compute_personalized_score(user, product, base_score):
    """
<<<<<<< HEAD
    Computes the final personalized score by adjusting the base score.
    If the product's ingredients contain allergens that conflict with the user,
    the product is excluded by returning a very low score (-999).
    """
    if has_allergy_conflict(user.get("allergies", ""), product.get("ingredients_text", "")):
        return -999
    adjustment = personalized_adjustment(user, product)
    return base_score + adjustment

if __name__ == '__main__':
    print("DEBUG: pd is imported:", pd)
=======
    Computes the final personalized score:
      - If there is an allergen conflict, returns a very low score.
      - Otherwise, adjusts the base score based on user metrics.
    """
    if has_allergy_conflict(user.get("allergies", ""), product.get("allergens", "")):
        return -999  # Exclude product if allergen conflict exists.
    adjustment = personalized_adjustment(user, product)
    return base_score + adjustment
>>>>>>> 32767bc6941ed8acc8c8b37a941a7b3b09e3febd
