import re

# Function to clean ingredients
def clean_ingredients(text):
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()  
    text = re.sub(r',\s*,', ',', text)  
    return text