# Local scientific source handoff

Store the acquired publication and manifest under ignored `data/private/` or outside Git. No restricted publication or real reference row is provided by this repository. The manifest is parsed by `ImportManifest` in `services/scientific_import.py`; use that model's JSON schema as the machine-readable contract.

Required top-level fields are `source_file`, `acquisition_permission`, `source_review_record`, `source`, `canonical_units`, and `proposals`. Relative source paths resolve beside the manifest. The source object records code, title, organization, URL, license, redistribution status, version, effective date, authority, and the acquired file's SHA-256. Authoritative handoffs are restricted to ICMR-NIN-2020 source codes; that label is an operator attestation, not automatic verification of scientific authenticity.

Each proposal contains kind (`target` or `effective`), effective date, and the payload described by the API's TargetPayload or EffectivePayload. The importer supplies source_id and acquisition_permission. Every nutrient must have an explicit canonical unit matching the registry. Each payload includes its citation and independent scientific review record. Target values and multiplier values must come from the reviewed source; do not infer them from qualitative evidence.

Run `python scripts/import_scientific.py data/private/manifest.json --admin-id ADMIN_UUID` to validate and roll back. Add `--commit` only to submit the validated immutable records for review. Reimporting an identical payload is idempotent. Source mutation, checksum mismatch, canonical-unit mismatch, and backdating fail the transaction.

A separate Admin reviews the resulting submission in Evidence review or through `/api/v1/admin/science/revisions/{id}/review`. Approval does not activate it. Activation must occur no later than its effective date. The importer and UI do not establish that an expert review has really happened: retain the actual review artifact and permissions with the private source acquisition records.

The repository's isolated import tests use explicitly fictional source text and values. They test governance and reproducibility, not nutrition validity. Lawful ICMR data and independently checked golden calculations remain outstanding release prerequisites.
