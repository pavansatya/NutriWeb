import pandas as pd
from rapidfuzz import fuzz, process

# Function to correct vowels
def correct_vowels(word, candidates):
    vowels = 'aeiou'
    word_lower = word.lower()
    corrected_candidates = []

    for candidate in candidates:
        candidate_lower = candidate.lower()
        # Replace each vowel in the word with each vowel in the candidate to find the best match
        if all(
            (c in vowels and w in vowels) or c == w
            for c, w in zip(candidate_lower, word_lower.ljust(len(candidate_lower)))
        ):
            corrected_candidates.append(candidate)

    return corrected_candidates

# Function to find the best matches
def suggest_categories(input_word, categories, top_n=5):
    # Normalize the categories
    categories = categories.str.lower().unique()

    # Step 1: Use Levenshtein distance to find initial matches
    matches = process.extract(input_word.lower(), categories, scorer=fuzz.ratio, limit=len(categories))

    # Step 2: Filter matches and correct for vowel errors
    top_matches = [match[0] for match in matches if match[1] > 60]  # Only keep matches with similarity > 60
    corrected_matches = correct_vowels(input_word, top_matches)

    # Step 3: Match corrections with the original `categories` column
    valid_matches = [match for match in (corrected_matches or top_matches) if match in categories]

    # Step 4: Return the top N suggestions
    suggestions = sorted(
        valid_matches,  # Use only matches found in `categories`
        key=lambda x: process.extractOne(input_word, [x], scorer=fuzz.ratio)[1],
        reverse=True
    )[:top_n]

    return suggestions