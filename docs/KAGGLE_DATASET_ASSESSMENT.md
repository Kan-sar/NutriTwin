# Kaggle dataset assessment — 2026-10-06

The current requirements distinguish food composition (IFCT preferred, USDA fallback)
from population reference targets (ICMR-NIN 2020). A food dataset cannot supply targets.
No Kaggle dataset reviewed here has been activated as an authoritative reference.

| Candidate | Observed source/license | Fit and decision |
|---|---|---|
| [Indian Food Nutritional Values Dataset (2025)](https://www.kaggle.com/datasets/batthulavinay/indian-food-nutrition) | Kaggle version 3; uploader lists CC BY-SA 4.0 and credits Anuvaad INDB | Strongest cooked-dish candidate. Download inspected: 1,014 unique dish names, 12 columns, 164 blank cells. Nutrient columns cover calories, carbohydrate, protein, fat, free sugar, fibre, sodium, calcium, iron, vitamin C and folate. No ingredient/allergen fields. Not installed in the application pending upstream redistribution/basis validation. |
| [ifct2017](https://www.kaggle.com/datasets/gijoe707/ifct2017) | Version 2; Kaggle lists license as Unknown; points to the community IFCT transcription | A mirror of IFCT, not an independent replacement or evidence of permission. Do not treat uploader availability as a new license grant. |
| [Indian Food Nutrition & Calories Dataset](https://www.kaggle.com/datasets/shadab80k/indian-food-nutrition-and-calories-dataset) | Version 2; uploader lists CC BY-SA 4.0, but the description does not identify specific underlying nutritional sources | Not preferred to the INDB-derived candidate; claims of verified data do not establish row-level provenance. |
| [Indian Packaged Foods Nutritional Dataset (2026)](https://www.kaggle.com/datasets/lalit7881/indian-packaged-foods-nutritional-dataset-2026) | Version 1; uploader lists CC0 and 852 products collected from labels/manufacturer sources | Candidate for a future packaged-product catalogue. Does not replace raw-ingredient composition or reference targets. Metadata inspected; rows not validated. |
| [RDA for Elements](https://www.kaggle.com/datasets/armaanjeetsandhu/recommended-dietary-allowances-for-elements), [Vitamins](https://www.kaggle.com/datasets/armaanjeetsandhu/recommended-dietary-allowances-for-vitamins), [Macronutrients](https://www.kaggle.com/datasets/armaanjeetsandhu/recommended-dietary-allowances-for-macronutrients) | Each version 2; uploader lists MIT and attributes RDA/AI values to the U.S. National Academies Food and Nutrition Board | A different population reference framework. Not verified ICMR-NIN equivalents; no complete EAR/TUL support established. Would require an explicit requirements change and separate scientific review, not relabeling as Indian targets. |

## Primary-source cross-check

[Anuvaad's INDB portal](https://www.anuvaad.org.in/indian-nutrient-databank/) confirms
1,014 recipes and per-100-g/per-serving values. Its
[methodology](https://www.anuvaad.org.in/methodology/) describes recipe calculations
using IFCT 2017/2004, UK food composition and USDA inputs. These are recipe-derived
estimates, not independent laboratory measurements of every prepared dish.

The inspected portal/methodology pages describe open access but do not establish the
Kaggle uploader's right to relicense the original database. The paper's open-access
license must not automatically be applied to all database inputs. The repository's
official-upstream policy favors acquiring and matching original INDB data before
bundling a Kaggle derivative. No permission email has been sent.

## Local audit artifact

- Download: `https://www.kaggle.com/api/v1/datasets/download/batthulavinay/indian-food-nutrition?datasetVersionNumber=3`
- Ignored local archive: `data/raw/kaggle-review/indian-food-nutrition-v3.zip`.
- SHA-256: `2d6b6d799e855576a2c47f95bc21bb2c43bf5598fd5029e21ba2d3531b9c2d11`.
- CSV member: `Indian_Food_Nutrition_Processed.csv`.
- The folate column has an encoding-damaged unit label. Match it to original source
  metadata before any unit conversion. Blank cells must stay unknown.
- The CSV omits original recipe codes, ingredient quantities, allergen labels and
  yield/preparation details. Do not infer allergy eligibility from dish names.

## Development completed independently

Expanded the pinned, permitted USDA Foundation subset from 74 to 122 foods with twelve
canonical nutrient fields (1,223 reported observations; 241 missing). The food-only
importer validates the processed manifest and rejects modification of existing source,
food or nutrient observations. It creates no accounts or target rules. Flutter now
defaults to real-food search, supports pagination and exposes installed source metadata.
ICMR target selection and scientific review gates remain unchanged.
