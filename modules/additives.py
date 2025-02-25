# Function to clean and split the additives_en column
import pandas as pd 
import re

# def clean_additives(additives):
#     if pd.isna(additives):
#         return 'No additives'
#     # Split by commas and remove leading/trailing whitespace
#     return list(set([additive.strip() for additive in str(additives).split(',')]))




# Function to extract additive codes
def extract_codes(text):
    # If the text is "No additives", return it as is
    if text == 'No additives':
        return text
    # Use regex to find all additive codes (e.g., E102, E129)
    codes = re.findall(r'E\d+\w*', text)
    # Join the codes with commas
    return ','.join(codes)