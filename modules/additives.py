import pandas as pd 
import re

def extract_codes(text):
    if text == 'No additives':
        return text
    codes = re.findall(r'E\d+\w*', text)
    return ','.join(codes)