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

## Upcoming Work (Next Phase)
- Implement relations between `Admission`, `Enrolment`, and `Payment` models in both DB and GraphQL.
- Expand models with detailed validation rules and additional fields.
- Add seed data to simulate realistic admission scenarios.
- Perform integration testing for model relations and API stability.
- Optionally start building a simple frontend or demo interface to visualize GraphQL queries.
