import pandas as pd 
import re

def extract_codes(text):
    """
    Extracts additive codes from a given text string.

    Parameters:
        text (str): The input text containing additive information.

    Returns:
        str: A comma-separated string of extracted additive codes or 
             'No additives' if the input indicates no additives.
    """
    if text == 'No additives':
        return text
    codes = re.findall(r'E\d+\w*', text)
    return ','.join(codes)