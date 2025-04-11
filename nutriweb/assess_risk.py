from modules.ingredients import clean_ingredients, clean_additives
from nutriweb.risk_levels import RISK_LEVELS

def classify_ingredient(ingredient_name: str) -> str:
    """
    Return the risk level for an ingredient/additive.
    Comparison is performed in lowercase.
    """
    name = ingredient_name.lower().strip()
    for key, level in RISK_LEVELS.items():
        if key in name:
            return level
    return "Safe"

def assess_product_ingredients(ingredients: list[str]) -> dict:
    """
    Assess the list of ingredients.
    Returns a dict containing:
      - 'ingredient_risks': a mapping of each ingredient to its risk level.
      - 'overall_risk': Overall risk—'Avoid' if any ingredient returns Avoid;
                         if any caution and none Avoid, then Caution; else Safe.
    """
    ingredient_risks = {}
    overall_level = "Safe"
    for ing in ingredients:
        risk = classify_ingredient(ing)
        ingredient_risks[ing] = risk
        if risk == "Avoid":
            overall_level = "Avoid"
        elif risk == "Caution" and overall_level == "Safe":
            overall_level = "Caution"
    return {"ingredient_risks": ingredient_risks, "overall_risk": overall_level}

def classify_product(ingredients_text: str, additives_text: str):
    """
    Classify a product based on its raw ingredients_text and additives_en.
    First clean and split the text, then assess risks.
    Returns a tuple:
      (overall_classification, ingredient risk mapping, additive risk mapping).
    """
    ingredients = clean_ingredients(ingredients_text)
    additives = clean_additives(additives_text)
    
    ing_assessment = assess_product_ingredients(ingredients)
    add_assessment = assess_product_ingredients(additives)
    
    overall_classification = "Safe"
    if ing_assessment["overall_risk"] == "Avoid" or add_assessment["overall_risk"] == "Avoid":
        overall_classification = "Avoid"
    elif ing_assessment["overall_risk"] == "Caution" or add_assessment["overall_risk"] == "Caution":
        overall_classification = "Caution"
    
    return overall_classification, ing_assessment["ingredient_risks"], add_assessment["ingredient_risks"]

def assess_product_risks(ingredients_text: str, additives_text: str) -> dict:
    """
    Returns a detailed risk assessment for the product:
      - overall classification,
      - warning message (if Avoid or Caution),
      - detailed breakdowns for ingredients and additives.
    """
    classification, ing_risks, add_risks = classify_product(ingredients_text, additives_text)
    warnings = []
    if classification == "Avoid":
        warnings.append("Product contains ingredients/additives that should be avoided based on health guidelines.")
    elif classification == "Caution":
        warnings.append("Product contains ingredients/additives that might need to be used with caution.")
    
    return {
        "overall_classification": classification,
        "warning": " ".join(warnings),
        "ingredient_risks": ing_risks,
        "additive_risks": add_risks
    }
