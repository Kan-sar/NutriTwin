# Data source register

Access date for web sources: 2026-08-30. No copyrighted source publication is committed.

| ID | Title / organization | URL / date | License / redistribution | Intended fields and extraction | Limitations / status |
|---|---|---|---|---|---|
| ICMR-RDA-2020 | *Nutrient Requirements for Indians: RDA and EAR 2020*, ICMR-NIN Expert Group | https://nin.res.in/RDA_Full_Report_2024.html; published 2020 | Full/short books are sold; electronic product redistribution permission not established | Local user-supplied table import: demographic criteria, EAR, RDA, TUL, units, formulas; source checksum retained | Authoritative; blocked from bundled import pending lawful access/permission |
| ICMR-RDA-BRIEF | *A Brief Note on Nutrient Requirements...*, ICMR-NIN | https://www.nin.res.in/rdabook/brief_note.pdf; 2020 | Official public brief; copyright retained | Definitions and design validation only; no table extraction | Confirms EAR/RDA/TUL semantics, not sufficient for targets |
| ICMR-DGI-2024 | *Dietary Guidelines for Indians 2024*, ICMR-NIN | https://nin.res.in/dietaryguidelines/pdfjs/locale/DGI_2024.pdf; 2024 | Personal reproduction with attribution; electronic product storage/reproduction requires prior written permission | Educational wording/design review only | Do not commit or bulk extract |
| IFCT-2017 | *Indian Food Composition Tables 2017*, ICMR-NIN | https://www.nin.res.in/ebooks/IFCT2017_16122024.pdf; 2017, web copy updated 2024 | Copyright/redistribution permission not established | Local source import: food identity, edible portion, nutrients per 100 g, analytical metadata | Preferred Indian foods; do not bundle/transcribe until permission clarified |
| USDA-FDC | USDA FoodData Central API/downloads | https://fdc.nal.usda.gov/api-guide/; releases vary | CC0 1.0; attribution requested | Optional demo/gap foods: FDC ID, description, data type, nutrient IDs/amounts/units; `nutritwin_data.fdc_demo` scripted acquisition | Not Indian-authoritative; latest `DEMO_KEY` attempt returned HTTP 429, so no FDC records are bundled |
| NIH-ODS-C | NIH ODS Vitamin C Health Professional Fact Sheet | https://ods.od.nih.gov/factsheets/VitaminC-HealthProfessional/; living page | US government informational material; source attribution | Qualitative relationship: vitamin C improves nonheme iron absorption | Does not by itself justify a quantitative multiplier |
| NIH-ODS-IRON | NIH ODS Iron Health Professional Fact Sheet | https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/; living page | US government informational material; source attribution | Qualitative iron enhancers/inhibitors and uncertainty | Calcium interference not definitively established; no active quantitative rule |
| NYAKUNDI-2026 | Nyakundi et al., ascorbate-rich foods and iron bioavailability | doi:10.1016/j.ajcnut.2026.101418; 2026 | Article copyright; metadata/abstract citation only | Evidence review candidate | Mixed endpoints; does not support a universal meal multiplier |

## Acquisition and transformation policy

Every imported artifact receives a source manifest with original filename/URL, retrieval timestamp, SHA-256, license decision, extractor version, row counts, unit mappings, rejected rows, and output checksum. Restricted input belongs in ignored `data/private/` or `data/raw/`; only allowed transformed outputs are committed. Missing data stays null with a reason code (`not_analysed`, `not_reported`, `not_applicable`, `unknown`).

## Demo data policy

The committed target and food fixtures use the `DEMO-SYNTHETIC` source code, conspicuous descriptions, and `authoritative=false`. The processed fixture contains seven foods and 28 nutrient rows. They exercise software only and cannot validate nutrition science. Future FDC-derived fixtures must use fixed FDC identifiers and store the CC0 source manifest.
