import re

def clean_ingredients(ing_text: str) -> list:
    """
    Cleans and splits the ingredients_text into a list of individual ingredients.
    
    Steps:
      - Remove parenthetical content to simplify (optional, but helps in some cases)
      - Remove extraneous punctuation (except commas)
      - Convert text to lowercase
      - Split the text by commas and strip extra whitespace from each token.
    
    Example:
      Input: "Bananas, vegetable oil (coconut oil, corn oil and/or palm oil) sugar, natural banana flavor."
      Output: ["bananas", "vegetable oil", "sugar", "natural banana flavor"]
    """
    if not isinstance(ing_text, str):
        return []
    # Optionally remove content in parentheses
    ing_text = re.sub(r'\([^)]*\)', '', ing_text)
    # Remove extra punctuation (except commas and spaces)
    ing_text = re.sub(r'[^\w,\s]', '', ing_text)
    # Convert to lowercase and strip whitespace
    ing_text = ing_text.lower().strip()
    # Split by comma and remove empty entries
    ingredients = [token.strip() for token in ing_text.split(',') if token.strip()]
    return ingredients

def clean_additives(add_text: str) -> list:
    """
    Cleans the additives string by splitting on commas and stripping extra whitespace.
    
    Example:
      Input: "E102,E211,E222,E433,E509"
      Output: ["e102", "e211", "e222", "e433", "e509"]
    """
    if not isinstance(add_text, str):
        return []
    additives = [x.strip().lower() for x in add_text.split(',') if x.strip()]
    return additives
