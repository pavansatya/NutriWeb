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
    return adjustment

def compute_personalized_score(user, product, base_score):
    """
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
