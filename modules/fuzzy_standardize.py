def fuzzy_standardize(packaging_string):
    packaging_types = packaging_string.lower()
    packaging_list = [package.strip() for package in packaging_types.split(',')]
    unique_packages = set(packaging_list)
    return ', '.join(sorted(set(unique_packages)))
