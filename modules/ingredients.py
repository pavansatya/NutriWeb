import re

def clean_ingredients(text):
    # Remove content in parentheses and brackets
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove trailing full stop if it exists
    text = re.sub(r'\.$', '', text)  # This targets only a period at the very end
    
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
