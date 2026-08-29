# ADR 0004: Python 3.12–3.14 compatibility

Status: Accepted — 2026-08-30

Context: The host has Python 3.14.5; all selected current core packages publish compatible metadata/wheels, while contributors may use 3.12/3.13. Decision: require `>=3.12,<3.15`, pin dependency versions, and use a pinned Python container image for reproducibility. Consequences: local verification works on the host and CI can cover the lower supported version.

