import pandas as pd
from rapidfuzz import fuzz, process

# Function to correct vowels
def correct_vowels(word, candidates):
    vowels = 'aeiou'
    word_lower = word.lower()
    corrected_candidates = []

    for candidate in candidates:
        candidate_lower = candidate.lower()
        if all(
            (c in vowels and w in vowels) or c == w
            for c, w in zip(candidate_lower, word_lower.ljust(len(candidate_lower)))
        ):
            corrected_candidates.append(candidate)

    return corrected_candidates

# Function to find the best matches
def suggest_categories(input_word, categories, top_n=5):
    categories = categories.str.lower().unique()

    matches = process.extract(input_word.lower(), categories, scorer=fuzz.ratio, limit=len(categories))

    top_matches = [match[0] for match in matches if match[1] > 70]  
    corrected_matches = correct_vowels(input_word, top_matches)

    valid_matches = [match for match in (corrected_matches or top_matches) if match in categories]

    suggestions = sorted(
        valid_matches,  
        key=lambda x: process.extractOne(input_word, [x], scorer=fuzz.ratio)[1],
        reverse=True
    )[:top_n]

    return suggestions