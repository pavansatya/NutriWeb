import re

def clean_ingredients(text):
    # Remove ALL content in parentheses/brackets/braces (including nested ones)
    text = re.sub(r'\([^()]*\)', '', text)  # Removes parentheses and content
    text = re.sub(r'\[[^\[\]]*\]', '', text)  # Removes brackets and content
    text = re.sub(r'\{[^{}]*\}', '', text)  # Removes braces and content
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove trailing punctuation/whitespace
    text = re.sub(r'[.,;]\s*$', '', text)
    
    # Normalize whitespace and clean commas
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r',\s*,', ',', text)  # Fix double commas
    
    # Remove any remaining orphaned commas
    text = re.sub(r'^\s*,|\s*,\s*$', '', text)
    
    return text