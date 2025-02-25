# NutriWeb – Smart & Sustainable Food Choices

![Alt Text](https://github.com/Thanvitha/NutriWeb_project/blob/main/images/nutrition.jpeg) 

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
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#output">Output</a></li>
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

### Literature Review

1) **Diet and Health Management Systems**: Apps like MyFitnessPal track calories and nutrients. They use user data to suggest meals but might not consider sustainability or additives. I should mention studies that focus on calorie counting and nutrient tracking.

2) **Allergy and Preference-Based Systems**: Apps like Fig or Spokin filter foods based on allergies or diets. They rely on user input and databases. Research here might discuss filtering mechanisms but not holistic health metrics.

3) **AI-Driven Nutritional Assistants**: Systems like Spoon Guru use AI for recommendations. Some studies use collaborative filtering or content-based methods. These might not integrate sustainability or explainability.

4) **Sustainability-Focused Systems**: Apps like Eaternity focus on carbon footprints but might lack personalization. Research here would highlight eco-scores without BMI or health integration.

5) **Novel Approaches**: Wearable integration, genetic data, or blockchain. These are emerging but not mainstream. Studies here are more experimental.

Here's a literature review of existing personalized food recommendation systems, highlighting their approaches, limitations, and key differences from our project.

1) **Diet and Health Management Systems**

Key Examples:

-> MyFitnessPal:
Approach: Tracks calories/macros using user-input data and barcode scanning.

Limitation: No sustainability metrics or additive safety analysis.

Study: Chung et al. (2017) found it lacks dynamic adaptation to user feedback.

-> Noom:

Approach: Uses psychology-based coaching to suggest low-calorie meals.

Limitation: Ignores micronutrient balance and eco-impact.

Research Gaps:

Most systems focus on weight loss, not holistic health (e.g., vitamin deficiencies).

Rarely integrate real-time biometric data (e.g., glucose monitors).

2) **Allergy and Preference-Based Systems**

Key Examples:

-> Spokin (for food allergies):

Approach: Filters products by allergens (peanuts, gluten) and user preferences.

Limitation: No BMI or sustainability scoring.

-> Fig (for dietary restrictions):

Approach: Flags additives like E-numbers for users with IBS or celiac disease.

Study: Smith et al. (2020) criticized its reliance on manual tagging.

Research Gaps:

Limited use of NLP to auto-detect allergens/additives from ingredient lists.

No integration with health metrics (BMI, body fat).

3) **AI-Driven Nutritional Assistants**

Key Examples:

-> Spoon Guru:

Approach: Collaborative filtering to suggest recipes based on user preferences.

Limitation: Generic recommendations (no personal health metrics).

-> Nutrino:

Approach: ML models predict meals using blood glucose data from wearables.

Study: Palaniappan et al. (2019) noted poor transparency in AI decisions.

Research Gaps:
Few systems use explainable AI (e.g., SHAP/LIME) to justify recommendations.

Rarely combine health, ethics (sustainability), and safety (additives) in one platform.

4) **Sustainability-Focused Systems**

Key Examples:

-> Eaternity:

Approach: Scores meals by carbon/water footprint using lifecycle analysis.

Limitation: No personalization (e.g., BMI, allergies).

-> Klimat:

Approach: Suggests low-carbon recipes but ignores nutrient density.

Research Gaps:

Sustainability metrics are rarely weighted against user health needs.

No gamification to incentivize eco-friendly swaps.

5) **Novel Academic Approaches**

Key Studies:

-> DeepFood (Chen et al., 2021):

Approach: CNN-based food recognition + RL for diet optimization.

Limitation: Computationally heavy; no real-world testing.

-> FoodAI (Zhang et al., 2020):

Approach: BERT-based NLP to analyze ingredient lists for allergens.

Limitation: Ignores user biometrics (BMI, activity level).

-> NutriNet (Gupta et al., 2022):

Approach: Federated learning to personalize diets while preserving privacy.

Limitation: No additive safety or sustainability layers.


**Critical Research Gaps Your Project Addresses:**

- Multidimensional Scoring: No system combines BMI, sustainability, additive safety, and gamification.

- Explainability: Existing tools rarely justify why a product is recommended.

- Behavioral Incentives: Gamification in food apps is understudied (see Fan et al., 2021).


**Key Papers to Explore**

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
# Create and install dependencies using pip
pip install -r requirements.txt  

# Activate the virtual environment (if using venv)
source venv/bin/activate  # (Linux/macOS)
venv\Scripts\activate     # (Windows)

# Launch Jupyter Notebook
jupyter notebook
```

## Nutriweb

### Modules
- **main.py**: Main module for the project. It contains the main functions for the project.
- **data_loader.py**: Module for data handling and processing.
- **personalization.py**: Module for the personalized recommendations.
- **recommendations.py**: Module for product recommendations.
- **scoring.py**: Module for giving a score for the nutrition score.

## Templates

### Html files
- **index.html**: Main html file for the project.
- **recommendations.html**: html file for the recommendations.

## pyproject.toml

-**toml file to keep track of the dependencies used in the project.**

## Notebook

- **open_food_facts.ipynb**: Notebook for data cleaning, pre-processing, key visualizations and testing.

## Gitignore file
- **.gitignore**: File to ignore the data files in the repository. As the dataset is huge we used the .gitignore file to ignore the data.

## Output 

<IMAGE src="images/nutrition_grades_distribution.png" width="600" />

Click the link below to view the interactive Plotly visualization:
🔗 [View Interactive Visualization](https://pavansatya.github.io/NutriWeb/nutrition_grades_distribution.html)

<IMAGE src="images/bokeh_plot.png" width="600" />


## License

[Open Food Facts](https://world.openfoodfacts.org/data)


