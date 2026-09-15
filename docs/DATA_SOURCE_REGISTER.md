> 2026-09-14 update: USDA Foundation subset expanded reproducibly to 74 foods and 12 nutrients (751 reported, 137 missing). The original archive SHA-256 is unchanged; transformed output uses fdc-foundation-subset-v2. No ICMR values or real quantitative factors were added. The earlier eight-food subset described below is historical.

# Data source register

Access dates are recorded per source; the initial review was 2026-08-30 and the USDA
Foundation Foods release was acquired on 2026-09-11. No restricted source publication
is committed.

| ID | Title / organization | URL / date | License / redistribution | Intended fields and extraction | Limitations / status |
|---|---|---|---|---|---|
| ICMR-RDA-2020 | *Nutrient Requirements for Indians: RDA and EAR 2020*, ICMR-NIN Expert Group | https://nin.res.in/RDA_Full_Report_2024.html; published 2020 | Full/short books are sold; electronic product redistribution permission not established | Local user-supplied table import: demographic criteria, EAR, RDA, TUL, units, formulas; source checksum retained | Authoritative; blocked from bundled import pending lawful access/permission |
| ICMR-RDA-BRIEF | *A Brief Note on Nutrient Requirements...*, ICMR-NIN | https://www.nin.res.in/rdabook/brief_note.pdf; 2020 | Official public brief; copyright retained | Definitions and design validation only; no table extraction | Confirms EAR/RDA/TUL semantics, not sufficient for targets |
| ICMR-DGI-2024 | *Dietary Guidelines for Indians 2024*, ICMR-NIN | https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf; 2024 | Personal reproduction with attribution; electronic product storage/reproduction requires prior written permission | Educational wording/design review only | Do not commit or bulk extract |
| IFCT-2017 | *Indian Food Composition Tables 2017*, ICMR-NIN | https://www.nin.res.in/ebooks/IFCT2017_16122024.pdf; 2017, web copy updated 2024 | Copyright/redistribution permission not established | Local source import: food identity, edible portion, nutrients per 100 g, analytical metadata | Preferred Indian foods; do not bundle/transcribe until permission clarified |
| USDA-FDC-FOUNDATION-2026-04 | USDA FoodData Central Foundation Foods, April 2026; USDA Agricultural Research Service | https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip; released 2026-04-30; accessed 2026-09-11 | Public domain, CC0 1.0; attribution requested; transformed subset redistribution permitted | Pinned JSON archive SHA-256 `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`; eight fixed FDC IDs; descriptions, data type, publication date, four normalized nutrient rows, dietary tags and allergen metadata; `scripts/import_fdc_foundation.py` | Real analytical fallback data but not Indian-authoritative; dry/raw/prepared states are not interchangeable; 12 absent selected nutrient values remain explicit `missing/not_reported`; full raw archive is locally ignored |
| CHEBI-DEMO | Chemical Entities of Biological Interest, EMBL-EBI | https://www.ebi.ac.uk/chebi/; accessed 2026-08-30 | CC BY 4.0; attribution required | Two-record transformed subset: preferred name, synonyms, formula, SMILES, InChI, InChIKey, stable ChEBI ID | Chemical identity only; does not establish a nutrition interaction or clinical effect |
| FOODON-2025-12-30 | FoodOn food ontology, FoodOn/OBO Foundry | http://purl.obolibrary.org/obo/foodon/releases/2025-12-30/foodon.owl; version 2025-12-30 | CC BY 4.0; attribution required | Three manually reviewed demo food mappings retrieved through EMBL-EBI OLS; stable ID, IRI, label, mapping type/confidence | Broad mappings are not composition equivalence; no full ontology file is bundled |
| RDKIT-2026-03-5 | RDKit cheminformatics toolkit | https://github.com/rdkit/rdkit; Release_2026_03_5 / commit de8add1e32ff6d3c4e4e406f64b703b662dff1d6 | BSD-3-Clause | Optional pipeline validation of SMILES canonicalization, formula, InChI, and InChIKey | Technical validation only; never used to predict absorption, bioactivity, diagnosis, or treatment |
| PLAYWRIGHT-1-62 | Playwright for Python, Microsoft | https://github.com/microsoft/playwright-python; v1.62.0 / commit 3b7c24c3e67dc84f7b0eddd0c5fd2ca685705021 | Apache-2.0 | Reproducible local Swagger/API evidence screenshots | Development evidence tool only; not an application runtime component |
| NIH-ODS-C | NIH ODS Vitamin C Health Professional Fact Sheet | https://ods.od.nih.gov/factsheets/VitaminC-HealthProfessional/; living page | US government informational material; source attribution | Qualitative relationship: vitamin C improves nonheme iron absorption | Does not by itself justify a quantitative multiplier |
| NIH-ODS-IRON | NIH ODS Iron Health Professional Fact Sheet | https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/; living page | US government informational material; source attribution | Qualitative iron enhancers/inhibitors and uncertainty | Calcium interference not definitively established; no active quantitative rule |
| NYAKUNDI-2026 | Nyakundi et al., ascorbate-rich foods and iron bioavailability | doi:10.1016/j.ajcnut.2026.101418; 2026 | Article copyright; metadata/abstract citation only | Evidence review candidate | Mixed endpoints; does not support a universal meal multiplier |

## Acquisition and transformation policy

Every imported artifact receives a source manifest with original filename/URL, retrieval timestamp, SHA-256, license decision, extractor version, row counts, unit mappings, rejected rows, and output checksum. Restricted input belongs in ignored `data/private/` or `data/raw/`; only allowed transformed outputs are committed. Missing data stays null with a reason code (`not_analysed`, `not_reported`, `not_applicable`, `unknown`).

## Demo and fallback data policy

The committed target and synthetic food fixtures use the `DEMO-SYNTHETIC` source code,
conspicuous descriptions, and `authoritative=false`. The synthetic fixture contains seven
foods and 28 nutrient rows. They exercise software only and cannot validate nutrition
science.

The committed USDA fallback subset contains eight real Foundation Foods records and 32
normalized nutrient rows, of which 20 are reported values and 12 are explicit missing
values. Fixed FDC identifiers, the CC0 license, raw archive checksum, transformation
steps, and processed checksum are stored in
`data/processed/fdc_foundation_subset.manifest.json`. These records remain
`authoritative=false` because they do not replace ICMR-NIN targets or IFCT Indian-food
composition.

The committed chemistry fixture contains two ChEBI identities, three FoodOn mappings,
and one NIH ODS qualitative interaction record. RDKit validates the structure fields.
The relational and pipeline schemas require qualitative evidence to remain
`calculation_effect=false`; it cannot change consumed or estimated-effective totals.
