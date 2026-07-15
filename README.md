---
title: NutriWeb
emoji: 🥗
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.44.1
app_file: streamlit_app.py
pinned: false
---

# NutriWeb – Smart & Sustainable Food Choices


<IMAGE src="images/nutrition.jpeg" width="1200" />

<!-- TABLE OF CONTENTS -->

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#literature review">Literature Review</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#output & results">Output & Results</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

## NutriWeb

NutriWeb is an intelligent food recommendation platform designed to enhance dietary choices by providing **personalized insights, transparency, and sustainability tracking**. Unlike existing apps that offer generic ratings, NutriWeb tailors recommendations based on **BMI, allergies, and dietary goals**, while also highlighting the **environmental impact** of food choices.

### **Problem Statement:**
Current nutrition apps **lack clarity, personalization, and sustainability awareness**:
- **Confusing information:** Complex ingredient lists make it hard to understand nutritional values.
- **Lack of personalization:** Generic health scores fail to consider individual dietary needs.
- **Environmental ignorance:** Most apps overlook the carbon footprint and eco-impact of food choices.

### **Solution: NutriWeb’s Unique Approach**
NutriWeb integrates **Personalized Nutrition analysis, visual comparisons, and context-aware insights** to help users make **smarter food choices**:
- **Personalized nutrition** based on user profiles (BMI, allergies, health goals).
- **Ingredient transparency** with easy-to-understand visual comparisons.
- **Sustainability tracking** to highlight a product’s carbon footprint.

## Dataset
1) **Open Food Facts:** Crowdsourced database with 3M+ food products.

The dataset can be accessed [here](https://drive.google.com/file/d/1SrVPakdOvOkUEsJekmsl9786MrxWXH0g/view?usp=sharing).

A food products database
Open Food Facts is a free, open, collaborative database of food products worldwide, with ingredients, allergens, nutrition facts and all the tidbits of information we can find on product labels.

Made by everyone
Open Food Facts is a non-profit association of volunteers.
5000+ contributors like you have added 600 000+ products from 150 countries using our Android, iPhone or Windows Phone app or their camera to scan barcodes and upload pictures of products and their labels.

For everyone
Data about food is of public interest and has to be open. The [complete database](https://world.openfoodfacts.org/data) is published as open data and can be reused by anyone and for any use. Check out the cool reuses or make your own!

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
- nutrition-score-fr_100g: Nutri-Score - Nutrition score derived from the UK FSA score and adapted for the French market (formula defined by the team of Professor Hercberg).
- biotin_100g: also known as Vitamine B8.
- pantothenic-acid_100g: also known as Vitamine B5.

and, you can access the complete information on the different fields [here](https://static.openfoodfacts.org/data/data-fields.txt).

2) **Users Data for personalized recommendation:** 
- link for the dataset: https://www.kaggle.com/datasets/ziya07/diet-recommendations-dataset?resource=download

3) **Non-GMO Database:** Identifies GMO-containing products.
- link for the dataset: https://world.openfoodfacts.org/data , https://www.nongmoproject.org/find-non-gmo/


<!-- GETTING STARTED -->
## Getting Started

### Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install fuzzywuzzy
```
```bash
pip install rapidfuzz
```
The following packages are required to execute the notebook:

  - python
  - numpy
  - pandas
  - scipy
  - matplotlib
  - seaborn
  - plotly
  - bokeh
  - panel
  - kaleido

```bash
# Activate the virtual environment (if using venv)
source venv/bin/activate  # (Linux/macOS)
venv\Scripts\activate     # (Windows)

# Create and install dependencies using pip
pip install -r requirements.txt

# Install dependencies from Poetry
poetry install
 
# Launch Jupyter Notebook
jupyter notebook
```

<!-- LITERATURE REVIEW -->
## Literature Review

1) **Diet and Health Management Systems**: Apps like MyFitnessPal track calories and nutrients. They use user data to suggest meals but might not consider sustainability or additives. I should mention studies that focus on calorie counting and nutrient tracking.

2) **Allergy and Preference-Based Systems**: Apps like Fig or Spokin filter foods based on allergies or diets. They rely on user input and databases. Research here might discuss filtering mechanisms but not holistic health metrics.

3) **AI-Driven Nutritional Assistants**: Systems like Spoon Guru use AI for recommendations. Some studies use collaborative filtering or content-based methods. These might not integrate sustainability or explainability.

4) **Sustainability-Focused Systems**: Apps like Eaternity focus on carbon footprints but might lack personalization. Research here would highlight eco-scores without BMI or health integration.

5) **Novel Approaches**: Wearable integration, genetic data, or blockchain. These are emerging but not mainstream. Studies here are more experimental.

Here's a literature review of existing personalized food recommendation systems, highlighting their approaches, limitations, and key differences from our project.

1. **Calorie & Nutrient Trackers (e.g. MyFitnessPal, Yuka)**:

-> What they do: Enable users to log foods and see calories, macros, and some micronutrients.

**Key limitations:**

-> Manual logging burden: Users must enter every item and portion themselves, leading to “logging fatigue” and high drop-off rates.

-> Data gaps: Many micronutrient values are missing or inconsistent across entries.

-> Subscription walls: Advanced features (barcode scan, detailed history) often require paid tiers.

**NutriWeb contrast:**

-> No tracking required: Instead of manual logs, users get recommendations by simply entering or scanning a product’s ingredients or barcode.

-> Free and open: Every feature is available without subscription.

2. **Allergy & Preference Filters (e.g. Fig, Spokin)**:

-> What they do: Let users list allergens or dietary preferences and then filter out unsafe items.

**Key limitations:**

-> Rule-based only: Products are excluded purely by keyword or database flags—no deeper understanding of ingredient similarity.

-> Rigid filters: If a product’s label is incomplete or uses unexpected terminology, it may slip through.

-> Limited suggestions: They show “safe” versus “unsafe,” but don’t recommend truly similar alternatives.

**NutriWeb contrast:**

-> Semantic matching: By embedding each product’s full, preprocessed ingredient list into a dense vector space (384-D using all-MiniLM-L6-v2), NutriWeb can find and recommend the closest peanut-free or gluten-free products—even when they use different wording.

-> Ingredient-level intelligence: No more brittle keyword matching—NutriWeb’s FAISS index retrieves nearest-neighbor products based on true semantic similarity, so substitutes feel natural.

3. **AI-Powered Nutrition Assistants (e.g. Spoon Guru)**:

-> What they do: Use collaborative filtering or recipe-based content recommendations to suggest meals or products.

**Key limitations:**

-> Black-box models: Often opaque, with little insight into why a suggestion was made.

-> Surface features: Many rely on co-purchase or user-rating data rather than understanding the chemistry of ingredients.

-> Narrow scope: Usually focused on recipe suggestions, not universal product recommendation across ingredient lists.

**NutriWeb contrast:**

-> Transparent embedding pipeline: You see exactly how input ingredients are tokenized, lemmatized, and vectorized (see diagram below).

-> Ingredient embeddings > co-occurrence: Instead of “users who bought X also bought Y,” NutriWeb learns the semantics of each ingredient phrase, so it generalizes to new products and phrasing.

### Why Users Will Choose NutriWeb:

-> Effortless recommendations – no logging, just enter or scan ingredients once.

-> Truly free – all features unlocked, no paywalls or subscriptions.

-> Rich allergen safety plus smart swaps – if you’re allergic to peanuts, NutriWeb not only filters out peanut-containing items but also suggests the “next best” alternatives using deep semantic similarity.

-> Modern NLP + vector search – leverages state-of-the-art sentence-transformer embeddings and FAISS for real-time semantic matching across thousands of products.

-> Transparent and extensible – the pipeline is clear, and new metrics (nutrients, eco-scores) can be integrated later by tagging each product record.

In sum, NutriWeb fills the gap between static filters and subscription-locked trackers by offering an open, allergy-aware, and ingredient-semantics engine that requires zero ongoing user effort beyond the initial input.

### Key Papers to Explore

->Paper 1:-
Caroline Gauthier, Frederic Bally,
Digitalization and power shift in the food market,
Journal of Business Research,
Volume 186,
2025,
115039,
ISSN 0148-2963,
https://doi.org/10.1016/j.jbusres.2024.115039.

Link to the paper: (https://www.sciencedirect.com/science/article/pii/S0148296324005435)

->Paper 2:-
TY  - JOUR
AU  - Hamdollahi Oskouei, Saeed
AU  - Hashemzadeh, Mahdi
PY  - 2023
DA  - 2023/09/01
TI  - FoodRecNet: a comprehensively personalized food recommender system using deep neural networks
JO  - Knowledge and Information Systems
SP  - 3753
EP  - 3775
VL  - 65
IS  - 9
SN  - 0219-3116
UR  - https://doi.org/10.1007/s10115-023-01897-4
DO  - 10.1007/s10115-023-01897-4
ID  - Hamdollahi Oskouei2023

Link to the paper: https://link.springer.com/article/10.1007/S10115-023-01897-4#citeas

->Paper 3:-
C. -H. Chen, M. Karvela, M. Sohbati, T. Shinawatra and C. Toumazou, "PERSON—Personalized Expert Recommendation System for Optimized Nutrition," in IEEE Transactions on Biomedical Circuits and Systems, vol. 12, no. 1, pp. 151-160, Feb. 2018, doi: 10.1109/TBCAS.2017.2760504.
keywords: {Logic gates;Genetics;Data models;Recurrent neural networks;Genetic algorithms;Biological neural networks;Expert system;recommendation system;personalized diets;deep learning;grocery decisions;neural networks;genetic algorithm},

Link to the paper: https://ieeexplore.ieee.org/abstract/document/8089390

<!-- System Design & Workflow -->
## NutriWeb System Design and Workflow

NutriWeb is designed to overcome the above gaps by being free and fully integrative. It requires no subscription fees, removing the cost barrier noted in other apps​. It simultaneously checks for allergens, analyzes nutrients, and computes sustainability metrics for foods. NutriWeb’s novel engine relies on deep semantic representations of ingredients. As shown below, raw ingredient lists are cleaned and embedded into a dense vector space, and a FAISS index enables fast nearest-neighbor queries for similar foods. 

<table>
  <tr>
    <td>
      <IMAGE src="images/a.jpg" width="500" />
    </td>
    <td>
      <IMAGE src="images/b.jpg" width="500" />
    </td>
  </tr>
</table> 


NutriWeb transforms each product’s ingredient list into a 384-dimensional embedding using a pretrained sentence transformer (all-MiniLM-L6-v2). First, the app applies NLP preprocessing (tokenization, lemmatization, stop-word removal) to normalize the ingredient text. The cleaned ingredients string is fed into the sentence transformer, producing a semantic embedding vector. All product embeddings are indexed using Facebook’s FAISS library, which is optimized for rapid nearest-neighbor search on large high-dimensional datasets​. This dense-vector approach allows NutriWeb to retrieve foods with similar ingredient profiles, enabling personalized recommendations and substitutions that go beyond simple keyword matching. 

<IMAGE src="images/c.jpg" width="1200" />

Raw ingredient labels (e.g. “Organic pasta (organic wheat flour), cheese sauce mix (dried whey, cheddar cheese (cultured milk, salt, enzymes), dried buttermilk, salt, sea salt)”) are preprocessed stepwise. As illustrated above, NutriWeb removes parenthetical details, converts text to lowercase, and strips punctuation to yield a uniform ingredient phrase. This text cleaning ensures consistency (e.g. “organic pasta cheese sauce mix dried buttermilk salt sea salt”) before embedding. By standardizing ingredient strings in this way, NutriWeb captures true semantic similarity (e.g. recognizing that “soy milk” and “tofu” are more alike than “soy sauce”) in its recommendations. NutriWeb’s key strengths stem from this architecture and its comprehensive data integration. Unlike other apps, it is entirely free and open to users (no paywalls)​. It combines multiple metrics: nutrient content (like trackers), allergen/diet filters (like preference apps), and environmental impact (like sustainability apps) in one platform. Crucially, its use of dense vector similarity allows ingredient-level personalization. In the literature, very few systems exploit such semantic embedding for food​. By contrast, NutriWeb leverages these modern NLP techniques so that even subtle similarities between recipes can inform suggestions. For example, a user allergic to peanuts will not only have peanut-containing items filtered out, but NutriWeb can also suggest novel peanut-free products with a similar taste profile based on ingredient embedding.



<!-- USAGE -->
## Nutriweb

### Modules

## Nutriweb module:
- **data_loader.py**: Module for data handling and processing.
- **personalization.py**: Module for the personalization.
- **recommendations.py**: Module for product recommendations.
- **risk_levels.py**: Module for assigning risk levels like low, moderate and high risks for ingredients and additives.
- **assess_risk.py**: Module for assessing ingredients and additives risks and then classify the products as "AVOID" and "SAFE" based on the classification.

## Modules module:
- **recommendations.py**: Module for product recommendations.
- **allergens.py**: Module for allergens filtering.
- **radar_chart.py**: Module for data visualizations.

## pyproject.toml

-**toml file to keep track of the dependencies used in the project.**

## Notebook

- **open_food_facts.ipynb**: Notebook for data cleaning, pre-processing, key visualizations and testing.

## Gitignore file
- **.gitignore**: File to ignore the data files in the repository. As the dataset is huge we used the .gitignore file to ignore the data.


<!-- LIMITATIONS-->
## Limitations

## Null Values in Nutrition Scores

### Description: 
Many products in the dataset have missing nutrition-score fields (e.g. Nutri-Score or national nutritional scores), resulting in null values in those columns. This limitation reduces the completeness of nutritional quality information and complicates any analysis that relies on a continuous distribution of scores. It also means some foods cannot be directly compared or classified by their standard nutrition-grade metrics. 

### Reasons Behind the Issue:
- These scores are often not provided on product labels for all items, especially for legacy or imported products. Compliance with labeling (like Nutri-Score) has been voluntary or not yet universal, so many entries simply lack these values.
- The source data (e.g. Open Food Facts) may not have captured or calculated the score for every product. In some cases the required nutrient data existed but the score was not computed or updated during data import.
- Historical data ingestion may have omitted scores for products added before score labeling became common.

### Actions Taken to Address It:
- We treated missing nutrition-score entries explicitly as “no data” rather than assuming a default value, to avoid biasing analyses.
- Where possible, alternate score fields were used (for example, a different country’s nutrition score or a computed score) to fill gaps. For example, if a French nutrition score was missing but a UK traffic-light score or the raw nutrient information was available, we used those as proxies.
- Data processing scripts were updated to attempt calculation of scores from nutrient columns when feasible. If an item had complete nutrient composition, we implemented logic to derive the Nutri-Score or equivalent.
- For any remaining null-score records, we flagged them in the dataset and excluded them from analyses that required a valid score. Documentation was updated to make clear which entries lack a nutrition-score and how they are handled.

## Missing Carbon-Footprint Data

### Description: 
The dataset includes very few entries for carbon footprint or environmental impact measures, leaving that column largely empty. Many products have no value for carbon emissions, so any analysis of ecological impact is severely limited by this sparsity. 

### Reasons Behind the Issue:
- Limited Availability on Labels: Very few manufacturers currently calculate or print carbon footprint values on product packaging. As noted by Open Food Facts, “a very limited amount of companies compute and print the carbon footprint on the packaging”​. In practice, almost all products lack this data.
- Newness of Data Collection: Carbon or eco-scores (like the new Eco-Score) are a relatively recent addition to the domain. Historical product entries predate such labels, and older data sources did not include them.
- Data Pipeline Issues: Early versions of the OpenFoodFacts database had separate fields for carbon footprint which were later deprecated or replaced. Some values were lost or never transferred during those schema changes. (For example, OpenFoodFacts even removed an old carbon footprint field when introducing newer eco-labels.)

### Actions Taken to Address It:
- The largely empty carbon-footprint column was removed from the working dataset schema. Keeping a mostly-null column would only add confusion or skew storage, so it was discarded to streamline analysis.
- In narrative reports and metadata, we noted the absence of carbon-footprint values as a data limitation (rather than silently ignoring it). Users of the dataset are warned that environmental impact analysis cannot be performed with this data.
- To the extent possible, we explored using related data (e.g. product categories × standard lifecycle analysis values) as a proxy for carbon footprint, but determined that without granular categorical mapping this was not reliable. Instead, we confined any mention of ecological impact to general discussion, not detailed metrics.

## Ambiguity of Zero vs. Null Nutrient Values
### Description: 
Some nutrient fields (such as fat, sugar, fiber, etc.) contain values of zero. It is unclear in many cases whether a zero represents an actual measurement (e.g. a product truly has 0g of that nutrient) or a placeholder for missing/unknown data. This ambiguity complicates data interpretation, since treating a zero as real or as null leads to very different conclusions. 

### Reasons Behind the Issue:
- Data Entry Conventions: In the raw data source, a “0” may have been entered either because the manufacturer declared “no [nutrient] content” or because the information was not available and defaulted to zero. Different contributors or scanning software may have made different assumptions when a nutrient was not specified.
- Formatting and Conversion Errors: Some extraction or parsing steps might have inserted zeros in place of empty fields. For example, if a parser interprets a missing value as numeric 0, that would introduce false zeros.
- Real vs. Missing: As noted in data analysis literature, “zero values” can mean fundamentally different things – either a true zero (the house was never renovated) or an unknown (not applicable)​
. In our context, a “0g” label could mean legitimately none present (scenario 1) or simply “not measured” (scenario 2)​
. Without auxiliary data, we cannot tell which is which.

### Actions Taken to Address It:
- We adopted a conservative approach: any zero value in a nutrient field that appeared likely ambiguous was treated as missing (NA) rather than assumed true. For example, if an improbable zero was recorded (such as 0g fat in an oil-based product), we marked it as missing.
- When context made it clear the zero was real (e.g. “0g sugar” on a diet soda label), we left it as 0. We used category heuristics (water-based drinks, pure spices, etc.) to judge plausible zeros.
- To make analyses robust, our data cleaning scripts replaced many nutrient zeros with NA and flagged which records were modified. This prevented analysis algorithms from treating those zeros as if they were measured quantities.
- All assumptions and rules were documented. Downstream analysis (correlations, models) was therefore done with the understanding that some zeros were converted to NA, in line with best practices for handling “missing vs. zero” data​

## Missing ingredients_text Field
### Description: 
The ingredients_text field is empty for a substantial number of products. This means that for those items, we do not have the raw list of ingredients that typically appears on the label. Missing ingredients lists limit our ability to analyze composition, detect allergens, or apply ingredient-based classifiers. 

### Reasons Behind the Issue:
- Incomplete Data Capture: Many product entries were created without scanning or manually entering the full ingredients list. Since ingredients must often be entered manually or extracted via OCR, they are frequently missing if no one contributed them.
- Truncated Exports: In some cases, the ingredients_text field is truncated or omitted during dataset export (e.g. CSV conversion or MongoDB dump). Very long ingredient lists may have been cut off by field-length limits or lost in transit.
- API vs. Bulk Data Differences: Some products have ingredients accessible via the API but missing in the bulk database dump. Synchronization issues between the OpenFoodFacts API and the downloaded dataset can leave ingredients_text null even if present online.

### Actions Taken to Address It:
- We dropped any records where ingredients_text was entirely null from analyses that required ingredient information (e.g. ingredient-based filtering or allergen rules). Those records remain in the raw dataset but are flagged as having no ingredient data.
- For records with partial or suspect data, we cross-checked against other language fields (e.g. if ingredients_text_en was blank, we looked for ingredients_text_fr). If an ingredient list existed in any language, it was copied into a common field to recover at least one complete list.

## Missing allergens_en Field
### Description: 
The allergens_en field (English-language allergens list) is missing for many products. Without a consistent allergens list, it is difficult to automatically identify products containing common allergens (e.g. nuts, gluten). The gap hampers any analysis of allergen prevalence or filtering for consumer safety. 

### Reasons Behind the Issue:
- Labeling Variations: Not all sources include an allergens_en entry. On packaging, allergens may only be labeled in the native language or sometimes not explicitly extracted into the English field.
- Data Entry Practices: Since allergens are often a subset of ingredients, if the full ingredient list was never entered or parsed, the allergen fields remain empty. The crowdsourced nature of the data means these fields are filled only if contributors took the extra step.
- Mapping and Translation: Even when allergens are present on the label, they may not have been mapped correctly into the standardized allergens_en field (versus allergens_fr, etc.). The automated pipelines rely on English labels, so non-English labels frequently end up as null.

### Actions Taken to Address It:
- We treated missing allergens_en as an unresolved gap. Since there is no reliable source within the dataset to fill them, we did not attempt to impute allergens. Instead, any consumer-safety analysis notes the absence explicitly.
- We added validation rules in the data ingestion pipeline: if an ingredient is one of the known allergens and appears in ingredients_text, we automatically populate the corresponding allergens_en entry. This heuristic improved coverage but is not foolproof.
- All remaining blank allergen entries are marked and excluded from any analysis that assumes a full allergen list. 

## Entirely Null Columns
### Description: 
The raw dataset contained some columns where every value was null (empty). These columns provided no information and could not be meaningfully analyzed. Having full-null columns increases storage and complicates data processing without benefit. 

### Reasons Behind the Issue:
- Legacy or Planned Fields: Some columns may have been defined in the data schema for future use or legacy support but were never populated. For example, fields like pnns_groups_1 or specific_pnr might exist in the schema but lack data entries.
- Data Export Alignment: When merging or updating multiple data sources, sometimes placeholder columns persist even if not used by any source. This can happen during schema evolution.
Incomplete Data Acquisition: Occasionally a field was meant to be filled by scraping, OCR, or user input, but that process never ran or failed for those fields across the entire dataset.

### Actions Taken to Address It:
- We performed an audit of all columns and identified those that were completely null. Such columns were removed from the cleaned dataset. This cleanup reduced confusion and improved computational efficiency.

## Limitations We Could Not Fully Tackle
### Persistent Missing Scores and Labels: We could not fully recover nutrition scores or labeling data for entries where the source never provided them. 
### Ingredients and Allergens Gaps: Products lacking ingredient lists or allergen data remain incomplete. Without external data sources or manual entry, these gaps cannot be auto-filled.
### Zero vs. Missing Ambiguity: Despite heuristic rules, we cannot be certain in all cases whether a zero is real or missing. 
### Carbon-Footprint Coverage: Given the scarcity of carbon footprint data, we cannot retrofit accurate environmental scores. Any ecological impact analysis is limited to categories or proxies, not product-specific values.
### Additives: As the risk levels of additives fickle, this might be a limitation. For example, according to latest scientific studies, some additives which were classified as higher risk are now classified as low risk.



<!-- OUTPUT & RESULTS -->
## Output & Results

<IMAGE src="images/nutrition_grades_distribution.png" width="1200" />

Click the link below to view the interactive Plotly visualization:
🔗 [View Interactive Visualization](https://pavansatya.github.io/NutriWeb/nutrition_grades_distribution.html)

<IMAGE src="images/NGD_cross_top15_cats.png" width="1200" />

<IMAGE src="images/category_hierarchy.png" width="1200" />

Click this link below to view the treemap:
🔗 [Treemap](https://pavansatya.github.io/NutriWeb/category_hierarchy_treemap.html)

This is the three dimensional Underlying Manifold Approximation & Projection (Umap) of the 384 dimensional vector embeddings of ingredients and respective product names

<IMAGE src="images/3D_Umap.png" width="1200" />

Click this link below to view the 2D Umap:
🔗 [Umap](https://pavansatya.github.io/NutriWeb/2D_UMAP_top10_categories.html)

<!-- LICENSE -->
## License

[Open Food Facts](https://world.openfoodfacts.org/data)
