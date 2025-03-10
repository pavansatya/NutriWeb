# nutriweb/assess_risk.py

import re
from nutriweb.risk_levels import ingredient_risks, additive_risks, UNKNOWN_RISK, UNKNOWN_RISK_THRESHOLD

def normalize_text(text):
    """Lowercase, remove parentheses content, and trim extra spaces."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def assess_list(text, risk_map):
    """Given a comma-separated string and a risk mapping, return a list of (item, risk) tuples."""
    if not text or str(text).strip() == "":
        return [("Unknown", UNKNOWN_RISK)]
    norm_text = normalize_text(text)
    items = [item.strip() for item in norm_text.split(',') if item.strip()]
    results = []
    for item in items:
        # Remove any language tag like 'en:' if present.
        clean_item = item.replace("en:", "").strip()
        risk = risk_map.get(clean_item, UNKNOWN_RISK)
        results.append((clean_item, risk))
    return results

def assess_ingredients_risk(ingredients_text):
    """Assess risk for ingredients."""
    return assess_list(ingredients_text, ingredient_risks)

def assess_additives_risk(additives_text):
    """Assess risk for additives."""
    return assess_list(additives_text, additive_risks)

def assess_product_risks(ingredients_text, additives_text):
    """
    Assess the product's risk by analyzing ingredients and additives.
    Returns a dictionary containing risk lists and a warning flag if unknown risks exceed threshold.
    """
    ing_results = assess_ingredients_risk(ingredients_text)
    add_results = assess_additives_risk(additives_text)
    
    unknown_count = sum(1 for _, risk in ing_results if risk == UNKNOWN_RISK) + \
                    sum(1 for _, risk in add_results if risk == UNKNOWN_RISK)
    
    warning = None
    if unknown_count >= UNKNOWN_RISK_THRESHOLD:
        warning = f"This product contains {unknown_count} ingredient(s)/additive(s) with unknown risk levels."
    
    return {
        "ingredients": ing_results,
        "additives": add_results,
        "warning": warning
    }

def classify_product(ingredients_text, additives_text):
    """
    Classify a product as 'Avoid' if any ingredient is high risk, 'Caution' if no high-risk ingredients
    but any additive is high risk, and 'Safe' otherwise.
    """
    ing_risks = assess_ingredients_risk(ingredients_text)
    add_risks = assess_additives_risk(additives_text)
    
    if any(risk == "High Risk" for _, risk in ing_risks):
        return "Avoid", ing_risks, add_risks
    elif any(risk == "High Risk" for _, risk in add_risks):
        return "Caution", ing_risks, add_risks
    else:
        return "Safe", ing_risks, add_risks
