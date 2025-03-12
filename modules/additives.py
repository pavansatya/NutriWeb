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
    if text == 'No additives':
        return text
    codes = re.findall(r'E\d+\w*', text)
    return ','.join(codes)