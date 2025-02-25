# nutriweb/personalization.py
import pandas as pd

def has_allergy_conflict(user_allergies, ingredients_text):
    """
    Checks if any allergens specified by the user appear in the ingredients.
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
    Adjusts the product's base score based on the user's parameters.
    - Penalizes products with high cholesterol_100g if user's cholesterol is high (>200).
    - Penalizes products with high salt_100g if user's blood pressure is high (>130).
    - Penalizes products with high energy relative to the user's daily calorie intake.
    - For a vegan user, applies a penalty if non-vegan ingredients appear.
    """
    adjustment = 0.0

    # Cholesterol penalty
    if user["cholesterol"] > 200:
        adjustment -= product.get("cholesterol_100g", 0) * 1.0

    # Blood pressure penalty
    if user["blood_pressure"] > 130:
        adjustment -= product.get("salt_100g", 0) * 1.0

    # Calorie adjustment: if product energy is high relative to daily calorie intake
    daily_cal = user.get("daily_calorie_intake", 2000)
    energy = product.get("energy_100g", 0)
    if energy > 0.05 * daily_cal:
        adjustment -= (energy / daily_cal) * 10

    # Vegan adjustment: if the user is vegan, penalize non-vegan ingredients.
    diettype = user.get("diettype", "").lower()
    if diettype == "vegan":
        ingredients = product.get("ingredients_text", "").lower()
        non_vegan_keywords = ["milk", "cheese", "egg", "meat", "honey", "chicken", "beef", "pork", "gelatin"]
        for keyword in non_vegan_keywords:
            if keyword in ingredients:
                adjustment -= 5  # apply a penalty once
                break

    return adjustment

def compute_personalized_score(user, product, base_score):
    """
    Computes the final personalized score by adjusting the base score.
    If there's an allergen conflict, returns a very low score (-999).
    Clamps negative scores to 0.
    """
    if has_allergy_conflict(user.get("allergies", ""), product.get("ingredients_text", "")):
        return -999
    adjustment = personalized_adjustment(user, product)
    score = base_score + adjustment
    # Clamp negative values to 0
    return max(0, score)

def classify_score(score):
    """
    Classifies the (clamped) score into:
      - "Safe" if score >= 70,
      - "Caution" if score is between 40 and 69,
      - "Avoid" if score is below 40.
    """
    score = max(0, score)  # Ensure score is not negative
    if score >= 70:
        return "Safe"
    elif score >= 40:
        return "Caution"
    else:
        return "Avoid"
