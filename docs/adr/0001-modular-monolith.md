# ADR 0001: Modular monolith with pure domain core

Status: Accepted — 2026-08-30

Context: A single student must deliver traceable nutrition calculations without operational complexity. Decision: use one FastAPI deployable with bounded modules, a separately testable pure-Python domain package, PostgreSQL as system of record, and optional Redis/Celery/Neo4j adapters. Consequences: simple local operation and transactions; modules may be extracted later only with measured need.

