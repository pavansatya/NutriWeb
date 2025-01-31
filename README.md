# NutriVision

<!-- ABOUT THE PROJECT -->

## Dataset
The dataset can be accessed [here](https://drive.google.com/file/d/1SrVPakdOvOkUEsJekmsl9786MrxWXH0g/view?usp=sharing).

A food products database
Open Food Facts is a free, open, collbarative database of food products from around the world, with ingredients, allergens, nutrition facts and all the tidbits of information we can find on product labels.

Made by everyone
Open Food Facts is a non-profit association of volunteers.
5000+ contributors like you have added 600 000+ products from 150 countries using our Android, iPhone or Windows Phone app or their camera to scan barcodes and upload pictures of products and their labels.

For everyone
Data about food is of public interest and has to be open. The [complete database](https://world.openfoodfacts.org/data) is published as open data and can be reused by anyone and for any use. Check-out the cool reuses or make your own!

Dataset structure
The dataset contains a single table, FoodFacts, in a tab-separated form in en.openfoodfacts.org.products.tsv 

A brief explanation of the columns in our dataset is provided below:

- code: Barcode of the product.
- creator: Contributor who first added the product
- created_t: Date that the product was added in UNIX format.
- last_modified_t: Date that the product page was last modified.
- product_name: Name of the product.
- generic_name: A generic description of the product.
- quantity: The amount of product in the packaging with unit.
- packaging: Information about packaging material.
- brands: Product’s brand name.
- categories: Product categories like groceries, and biscuits.
- origins: Origins of ingredients.
- manufacturing_places: Locations where the product was manufactured.
- labels: Certifications or labels of the product.
- emb_codes: Official manufacturing site codes.
- purchases_places: Locations where the product can be purchased.
- stores: Retail stores that carry the product.
- countries: list of countries where the product is sold.
- ingredients_text: List of ingredients used in the product.
- allergens: Known allergens present in the product.
- nutriments: Nutritional information per serving.
- additives_n: Number of food additives in the product.
- ingredients_from_palm_oil_n: Number of ingredients made from palm oil.
- nutrition_grade_fr: nutrition grade (‘a’ to ‘e’) given by france.

and you can access the complete information on the different fields [here](https://static.openfoodfacts.org/data/data-fields.txt)
