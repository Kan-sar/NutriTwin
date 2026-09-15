# Review-1 academic artifact

These artifacts record the original backend and chemistry milestone. They are retained unchanged for academic review and should not be read as screenshots of the current Flutter client or latest test suite.

- [Project report](NutriTwin_Project_Review1_Report.docx)
- [Architecture diagram](architecture.svg) and [PNG version](architecture.png)
- [Evidence manifest](evidence/manifest.json), including capture commands, timestamps, application commits and image hashes

| Evidence | Image |
|---|---|
| API interface | [Swagger](evidence/01-api-interface.png) |
| Health and authenticated workflow | [PowerShell](evidence/02-health-workflow.png) |
| Nutrition twin | [Consumed/effective/target trace](evidence/03-nutrition-twin.png) |
| Recommendation trace | [Hard checks and scores](evidence/04-recommendation-trace.png) |
| Chemistry | [Reference provenance](evidence/05-chemistry-evidence.png) |
| Automated checks | [Recorded test run](evidence/06-automated-tests.png) |
| PostgreSQL state | [Database inspection](evidence/07-database-state.png) |

Capture scripts remain in `scripts/capture_powershell_evidence.ps1` and `scripts/capture_review_evidence.py`. New captures must have their own accurate provenance; do not relabel these historical images as current validation.

Return to [current documentation](../README.md).
