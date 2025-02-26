import re

# Function to clean ingredients
def clean_ingredients(text):
    # Step 1: Remove text inside parentheses ()
    text = re.sub(r'\([^)]*\)', '', text)
    # Step 2: Remove text inside square brackets []
    text = re.sub(r'\[[^\]]*\]', '', text)
    # Step 3: Convert to lowercase
    text = text.lower()
    # Step 4: Remove extra spaces and ensure comma-separation
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    text = re.sub(r',\s*,', ',', text)  # Remove duplicate commas
    return text