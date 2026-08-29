# ADR 0003: Identity baseline for estimated effective intake

Status: Accepted — 2026-08-30

Context: Evidence supports food–nutrient interactions qualitatively, but generalized quantitative absorption multipliers can overclaim physiology. Decision: implement an evidence/versioned rule engine and separate effective state, with no active quantitative rules initially. With none, effective equals consumed and the trace declares an identity estimate plus uncertainty. Consequences: distinction and reproducibility exist without false precision; reviewed bounded rules can be activated later as new versions.

