import re

def clean_ingredients(text):
    """
    Cleans and standardizes an ingredient text string by removing unnecessary content and formatting.

    Parameters:
        text (str): The raw ingredient text to be cleaned.

    Returns:
        str: A cleaned version of the ingredient text with:
             - Parenthetical and bracketed content removed
             - Converted to lowercase
             - Additive codes (e.g., E300, E120ii) removed
             - Periods and commas cleaned
             - Extra whitespace normalized
    """
    # Remove content in parentheses and brackets
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove trailing full stop if it exists
    text = re.sub(r'[.,]', ' ', text)
    text = re.sub(r'\.$', '', text)  
    
    # Remove additives inside ingredinets
    text = re.sub(r'\be\d+[a-z]*\b', '', text)
    
    # Normalize whitespace and clean commas
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r',\s*,', ',', text)
    
    return text

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
