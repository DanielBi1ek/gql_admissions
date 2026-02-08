# Project Diary – GQL Admissions

## 06.10.2025 – Project Initialization
- *(initial setup commit not recorded in this branch)*
- Set up the initial project structure and repository.
- Configured the database connection and environment variables.
- Created the first GraphQL server setup with a basic schema and test query.
- Verified that the backend runs locally without major issues.

## 03.11.2025 – Restart After Wrong Branch
- *(reinitialization commit not recorded in this branch)*
- Discovered that work had been done on an outdated branch, causing schema and dependency conflicts.
- Decided to restart the project from a clean base.
- Recreated the environment setup and restructured the project to match the latest requirements.
- Reinitialized a new database schema to ensure compatibility with the backend logic.

## 07.11.2025 – New Setup and Data Models
- **Commit:** `41a9625` – *“First project day commit, demo data AdmissionModel, Enrolment model, Payment model, no relations yet.”*
- Rebuilt the database schema and GraphQL models from scratch.
- Added core entities: `AdmissionModel`, `Enrolment`, and `Payment`.
- Integrated demo data for testing purposes.
- Confirmed that the GraphQL API handles queries and mutations correctly for standalone models.
- Relations between entities are not yet implemented.

## 25.11.2025 – Admissions Relationships & Validation Pass
- **Commit:** `c58e3b1` – *“Link admission entities and add validation layer.”*
- Connected applicants, applications, offers, payments, and processes across both SQLAlchemy models and GraphQL types.
- Brought in the first round of business-rule validations (date windows, one-offer-per-program, payment positivity, numeric account guards).
- Seeded richer demo data in `systemdata.json` so pagination/list queries finally return realistic shapes.
- Documented the expanded model field expectations inside `DOCUMENTATION.md`.

## 15.12.2025 – RBAC Foundations & Service Refactor
- **Commit:** `9fb21d4` – *“Admission services split + RBAC scaffolding.”*
- Refactored `src/services/admissions.py` to centralize mutations (insert/accept/withdraw) and share loader utilities.
- Added the first RBAC matrix draft under `src/GraphTypeDefinitions/admission_permissions.py`, wiring it into the schema resolvers.
- Tightened test coverage around owner/admin/public scenarios, which exposed several missing auth guards that were subsequently patched.
- Stubs for Docker-based local stack were introduced but not yet finalized.

## 12.01.2026 – Unified RBAC, Admissions Logic Overhaul & Tooling
- **Commit:** `b7d4a0c` – *“RBAC unification, admissions logic rewrite, docker stack + tests.”*
- Collapsed scattered permission snippets into a single authoritative table inside `admission_permissions.py`, then updated every resolver/mutation to consult it.
- Restructured admissions models to share consistent base fields (timestamps, audit IDs) and ensured business logic (withdraw vs accept, payment-process linkage) resides in service helpers instead of resolvers.
- Added the docker-compose stack (Apollo gateway + FastAPI app + auth proxy) so tests can hit the same URLs exposed on `tests.html`.
- Backfilled pytest coverage (business logic, RBAC, GT definitions, client smoke tests) and set sane defaults for GraphQL client env vars to keep the suite runnable out of the box.

