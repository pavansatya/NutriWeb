# nutriweb/risk_levels.py

# Define risk labels
HIGH_RISK = "High Risk"
MODERATE_RISK = "Moderate Risk"
LOW_RISK = "Low Risk"
UNKNOWN_RISK = "Unknown Risk"

# Risk mapping for ingredients (example values – expand as needed)
ingredient_risks = {
    "high fructose corn syrup": HIGH_RISK,
    "wheat gluten": MODERATE_RISK,
    "butter": MODERATE_RISK,
    # ... add more ingredients
}

# Risk mapping for additives (example values – expand as needed)
additive_risks = {
    "e101": LOW_RISK,
    "e101i": LOW_RISK,
    "e282": MODERATE_RISK,
    "sodium nitrite": HIGH_RISK,  # ensure sodium nitrite is marked as high risk
    # ... add more additives
}

# Threshold for unknown risk items to trigger a warning
UNKNOWN_RISK_THRESHOLD = 2
