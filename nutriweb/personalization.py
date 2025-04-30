from nutriweb.risk_levels import RISK_LEVELS
import pandas as pd

def profile_specific_avoid_list(profile: dict) -> set:
    """
    Create a set of ingredients that the user must avoid based on:
      - Allergens (always avoid),
      - Dietary restrictions (e.g., for vegetarians/vegans),
      - Health conditions (e.g., high cholesterol or high blood pressure).
    """
    avoid_set = set()
    # Allergens: strictly avoid any product containing these.
    for allergen in profile.get("allergens", []):
        avoid_set.add(allergen.lower())
    # Dietary restrictions:
    diet = [d.lower() for d in profile.get("dietary_restrictions", [])]
    if "vegetarian" in diet or "vegan" in diet:
        avoid_set.update(["meat", "gelatin", "fish", "chicken", "beef", "pork"])
    if "vegan" in diet:
        avoid_set.update(["milk", "egg", "honey", "cheese", "butter"])
    if "gluten-free" in diet:
        avoid_set.update(["wheat", "barley", "rye", "malt"])
    # Health conditions:
    if profile.get("cholesterol", "").lower() == "high":
        avoid_set.update(["palm oil", "butter", "lard", "hydrogenated", "coconut oil"])
    if profile.get("blood_pressure", "").lower() == "high":
        avoid_set.update(["salt", "sodium", "sodium benzoate"])
    return avoid_set

def assess_product_for_user(product_ingredients: list[str], base_risk: dict, profile: dict) -> dict:
    """
    Adjust a product's risk assessment based on the user's profile.
    If any ingredient is in the user's avoid list, mark the product as 'Avoid' and record the reason.
    Returns a dictionary with:
      - 'user_overall_risk': (Safe, Caution, or Avoid),
      - 'flags': a list of reasons.
    """
    user_overall = base_risk.get("overall_risk", "Safe")
    flags = []
    avoid_set = profile_specific_avoid_list(profile)
    for ing in product_ingredients:
        name = ing.lower()
        if name in avoid_set:
            flags.append(f"contains '{ing}' which you should avoid")
            user_overall = "Avoid"
        elif base_risk["ingredient_risks"].get(ing, "") == "Caution":
            flags.append(f"contains '{ing}' marked for caution")
            if user_overall == "Safe":
                user_overall = "Caution"
    return {"user_overall_risk": user_overall, "flags": flags}

def get_user_profile(cholesterol: str, blood_pressure: str, allergens: str, diet_type: str) -> dict:
    """
    Create a user profile dictionary from inputs.
    'allergens' and 'dietary_restrictions' are stored as lists.
    """
    return {
        "cholesterol": cholesterol,
        "blood_pressure": blood_pressure,
        "allergens": [a.strip() for a in allergens.split(',') if a.strip()],
        "dietary_restrictions": [d.strip() for d in diet_type.split(',') if d.strip()]
    }

def personalize_recommendations(user_profile: dict, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Filter the products DataFrame to return only those that do NOT contain any ingredients 
    from the user's avoid list. This function now uses the "ingredients_text" column.
    """
    avoid_list = profile_specific_avoid_list(user_profile)
    
    def is_product_safe(row):
        ingredients = row.get("ingredients_text", "")
        if not ingredients:
            return True  # If missing, assume safe.
        ing_list = [ing.strip().lower() for ing in ingredients.split(",") if ing.strip()]
        return not any(ing in avoid_list for ing in ing_list)
    
    filtered_df = df[df.apply(is_product_safe, axis=1)]
    return filtered_df.head(top_n)
