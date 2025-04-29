# Limitations

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
