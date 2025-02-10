# scoring.py

# Weight constants for the scoring system.
NUTRITION_WEIGHT = 0.6
ADDITIVES_WEIGHT = 0.3
ORGANIC_WEIGHT = 0.1

def calculate_nutrition_score(row):
    """
    Calculates a nutritional score (max 60) based on:
      - Negative factors: sugar, saturated fat, salt.
      - Positive factors: fiber, protein, fruit & vegetables percentage.
    The calories factor has been removed.
    """
    # Removed: row["calories"] * 0.02
    negative_factors = row["sugar"] * 2 + row["saturated_fat"] * 3 + row["salt"] * 1.5
    positive_factors = row["fiber"] * 3 + row["protein"] * 2 + row["fruit_vegetables_pct"] * 1.5
    score = 60 - negative_factors + positive_factors
    return max(0, min(60, score))

def calculate_additive_score(row):
    """
    Calculates an additive score (max 30) by subtracting points 
    for each harmful additive.
    Assumes that the 'additives' column contains the count of harmful additives.
    """
    harmful_additives = row["additives"]
    return max(0, 30 - harmful_additives * 3)

def calculate_organic_score(row):
    """
    Returns a bonus of 10 if the product is organic.
    """
    return 10 if row["organic"] == 1 else 0

def compute_base_health_score(product_row):
    """
    Computes the overall base health score (out of 100) for a product.
    """
    nutrition = calculate_nutrition_score(product_row)
    additive = calculate_additive_score(product_row)
    organic = calculate_organic_score(product_row)
    health_score = (nutrition * NUTRITION_WEIGHT +
                    additive * ADDITIVES_WEIGHT +
                    organic * ORGANIC_WEIGHT)
    return health_score
