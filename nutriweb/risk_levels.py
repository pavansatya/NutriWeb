# nutriweb/risk_levels.py

# Define risk labels
HIGH_RISK = "High Risk"
MODERATE_RISK = "Moderate Risk"
LOW_RISK = "Low Risk"
UNKNOWN_RISK = "Unknown Risk"

# Risk mapping for ingredients (example values – expand as needed)
ingredient_risks = {
    "water": LOW_RISK,
    "high fructose corn syrup": HIGH_RISK,
    "wheat gluten": MODERATE_RISK,
    "butter": MODERATE_RISK,
    "carbonated water": LOW_RISK,
    "sugar": MODERATE_RISK,
    "glucose": MODERATE_RISK,
    "citric acid": LOW_RISK,
    "natural flavors": LOW_RISK,
    "artificial flavors": MODERATE_RISK,
    "taurine": LOW_RISK,
    "sodium citrate": LOW_RISK,
    "color added": MODERATE_RISK,
    "panax ginseng extract": MODERATE_RISK,
    "L-Carnitine L-Tartrate": LOW_RISK,
    "caffeine": MODERATE_RISK,
    "sorbic acid": LOW_RISK,
    "benzoic acid": MODERATE_RISK,
    "niacinamide": LOW_RISK,
    "sucralose": HIGH_RISK,
    "salt": LOW_RISK,
    "eau gazéifiée": LOW_RISK,
    "sucre": MODERATE_RISK,
    "colorant caramel e150d":MODERATE_RISK ,
    "acidifiant": MODERATE_RISK,
    "arômes": LOW_RISK,
    "brewed starbucks coffee": LOW_RISK,
    "reduced-fat _milk_": LOW_RISK,
    "pectin.": LOW_RISK,
    "potassium bromate": HIGH_RISK,
    "propylparaben": HIGH_RISK,
    "bha": HIGH_RISK,
    "bht": HIGH_RISK,
    "sodium benzoate": HIGH_RISK,
    "titanium dioxide": HIGH_RISK,
    "sodium nitrite": HIGH_RISK,
    "red 3": HIGH_RISK,
    "red 40": HIGH_RISK,
    "red 40 lake": HIGH_RISK,
    "yellow 5": HIGH_RISK,
    "yellow 5 lake": HIGH_RISK,
    "yellow 6": HIGH_RISK,
    "blue 1": HIGH_RISK,
    "blue 2": HIGH_RISK,
    "green 3": HIGH_RISK,
    "aspartame": HIGH_RISK,
    "ada": HIGH_RISK,
    "propylgallate": HIGH_RISK,
    "methylene chloride": HIGH_RISK,
    "trichloroethylene": HIGH_RISK,
    "ethylene dichloride": HIGH_RISK,
    "pfas": HIGH_RISK,
    "phthalates": HIGH_RISK,
    "brominated vegetable oil": HIGH_RISK,
    "sodium nitrate": HIGH_RISK,
    "acesulfame potassium": HIGH_RISK,
    "advantame": HIGH_RISK,
    "neotame": HIGH_RISK,
    "saccharin": HIGH_RISK,
    

    # ... add more ingredients
}

# Risk mapping for additives (example values – expand as needed)
additive_risks = {
    "e101": LOW_RISK,
    "e101i": LOW_RISK,
    "e282": MODERATE_RISK,
    "sodium nitrite": HIGH_RISK,  # ensure sodium nitrite is marked as high risk
    "e1103": LOW_RISK,
    "e420i": MODERATE_RISK,
    "e955": MODERATE_RISK,
    "e210": HIGH_RISK,
    "e513": HIGH_RISK,
    "e450": MODERATE_RISK,
    "e100": LOW_RISK,
    "e318": LOW_RISK,
    "e281": MODERATE_RISK,
    "e327": LOW_RISK,
    "e555": HIGH_RISK,
    "e200": LOW_RISK,
    "e330": LOW_RISK,
    "e331": LOW_RISK,
    "e150d": LOW_RISK,
    "e338": MODERATE_RISK,
    "e440": LOW_RISK,
    "e440i": LOW_RISK,

    # ... add more additives
}

# Threshold for unknown risk items to trigger a warning
UNKNOWN_RISK_THRESHOLD = 2
