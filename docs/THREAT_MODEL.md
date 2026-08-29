# Threat model

Method: STRIDE-informed review for a local academic prototype. Trust boundaries are client→API, API→PostgreSQL/Redis/Neo4j, Admin→scientific rules, and import pipeline→reference stores.

| Threat | Impact | Controls | Verification / residual risk |
|---|---|---|---|
| Credential stuffing/token theft | Account data disclosure | Argon2id, generic login errors, short access tokens, hashed rotating refresh tokens, revocation, rate-limit-ready boundary, TLS required outside local | Auth/reuse/revocation tests; distributed rate limiter deferred |
| Horizontal/vertical authorization bypass | Cross-user data or Admin mutation | User-scoped repository queries, backend role dependencies, deny by default, audit | RBAC/ownership tests |
| Nutrition-rule tampering | Unsafe/misleading estimates | Draft/review/approved workflow, activated versions immutable, evidence citation, checksums, Admin audit, deterministic traces | Mutation/approval tests; single-admin collusion remains |
| Reference-data poisoning | Corrupted foods/targets | Source manifests/checksums, schema/range validation, explicit missingness, quarantined rejects, reviewer activation | Pipeline tests; source truth still requires expert review |
| Malicious upload | Malware/resource exhaustion | Optional feature off; type allowlist, size/count limits, random names, no execution, isolated parsing when added | Upload tests required before enablement |
| SQL/graph injection | Data exfiltration/tampering | SQLAlchemy bound parameters, fixed Cypher templates/parameters, validated IDs, least privilege | Static review/integration tests |
| Prompt injection / LLM fabrication | Unsupported claims/numbers | External content untrusted; structured facts only; number/phrase validator; deterministic fallback; LLM cannot select/score | Disabled by default; adversarial tests before enablement |
| PII/secrets in logs | Privacy/credential exposure | Structured allowlisted logs, request IDs, token/password/email redaction, no request-body dumps | Log-capture and secret scan |
| Research re-identification | Participant harm | No real study claim; consent/purpose controls; pseudonymous export; remove direct IDs; date/age generalization and small-cell suppression later | Export tests; formal disclosure review required before research use |
| Provenance loss | Irreproducible science | Foreign keys to sources/rules, version/effective dates, immutable traces, manifest hashes | Referential/migration tests |
| Optional-service outage | Core workflow unavailable/corrupt | Required PostgreSQL only; timeouts/circuit behavior; synchronous or pending recompute; graph/LLM enrichment nullable | Failure-injection tests |
| Optimizer abuse/DoS | CPU exhaustion | Bounded candidates/servings, integer coefficient limits, deterministic single worker, short time limit, request quotas later | Bound/timeout tests |
| Overcollection/clinical inference | Sensitive or unsafe output | Minimal profile; unsupported conditions absent; non-clinical vocabulary; no medication/supplement advice | Schema and wording tests |

## Security assumptions

Compose credentials are development-only and must be replaced outside local use. The prototype has no public deployment approval. Dependency, secret, and workflow scanning are defense-in-depth; a human scientific/security review remains required before participant use.

