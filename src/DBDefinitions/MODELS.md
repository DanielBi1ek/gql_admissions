# DBDefinitions overview

This document describes the current SQLAlchemy models in `src/DBDefinitions` and why the schema is structured this way.
The service is federated, so references to external services (users, RBAC, status catalogs) are stored without foreign
key constraints.

## Shared base

### BaseModel (BaseModel.py)
- Common fields: `id`, `created`, `lastchange`, `createdby_id`, `changedby_id`, `rbacobject_id`.
- `createdby_id`/`changedby_id`/`rbacobject_id` are UUIDs without FKs because users and RBAC objects live in other
  services (`gql_ug`, RBAC service).
- `UUIDFKey` and `UUIDColumn` keep UUID usage consistent across models.

## Core admissions domain

### AdmissionProcessModel (AdmissionProcessModel.py)
- Table: `admission_processes`.
- Purpose: definition of an admission process (time window, rules, program, fees).
- Fields:
  - Identity: `name`, `name_en`.
  - References: `program_id` (FK to `study_programs`), `payment_info_id` (FK to `admission_payment_infos`).
  - Timeline: `application_start_date`, `application_end_date`, `exam_start_date`, `exam_end_date`,
    `decision_deadline`, `payment_deadline`, `enrollment_date`, `condition_deadline`, `condition_extended_deadline`.
- Relationships:
  - `payment_info` (view-only FK), `study_program` (view-only FK).
- Why: process rules are reused by multiple applications, so this is a distinct entity.

### AdmissionApplicationModel (AdmissionApplicationModel.py)
- Table: `admission_applications`.
- Purpose: a specific applicant’s submission into a process.
- Fields:
  - References: `process_id` (FK to `admission_processes`), `applicant_user_id` (no FK).
  - Applicant data: `applicant_name`, `applicant_email`, `applied_date`, `status_id` (no FK).
- Relationships:
  - `process` (view-only FK), `enrollments` (1:N), `payments` (1:N).
- Why: separates applicant-specific data from process rules and supports multiple applications per process.

### EnrollmentModel (EnrollmentModel.py)
- Table: `enrollments`.
- Purpose: the result of a successful admission (the actual enrollment).
- Fields: `application_id` (FK), `study_program_id` (FK), `status_id` (no FK), `enrolled_at`.
- Relationships: `application` (view-only FK), `study_program` (view-only FK).
- Why: enrollment is downstream of applications; it should not carry payment details.

### PaymentInfoModel (PaymentInfoModel.py)
- Table: `admission_payment_infos`.
- Purpose: payment rules (account number, symbols, IBAN/SWIFT, required amount).
- Why: shared by multiple processes and payments to keep payment rules consistent.

### PaymentModel (PaymentModel.py)
- Table: `payments`.
- Purpose: actual payment records for an admission application.
- Fields:
  - References: `application_id` (FK), `payment_info_id` (FK), `payer_id` (no FK), `status_id` (no FK).
  - Bank details: `bank_unique_data`, `variable_symbol`.
  - Money: `amount`, `currency`, `method`, `paid_at`.
- Relationships: `application` (FK), `payment_info` (view-only FK).
- Why: payments are tied to applications (application fee). Enrollment payments can be added later if needed.

## Supporting tables

### StudyProgramModel (StudyProgramModel.py)
- Table: `study_programs`.
- Purpose: catalog of programs referenced by admission processes and enrollments.
- Fields: `name`, `name_en`, `code`, `description`, `degree_level`, `duration_years`, `credits`.

### StateModel (StateModel.py)
- Table: `states`.
- Purpose: optional local catalog for statuses (admission/enrollment/payment/event).
- Note: `status_id` fields do not enforce FK in this service to stay compatible with federated status sources.

### UserModel (UserModel.py)
- Table: `users`.
- Purpose: minimal placeholder for local seeding/testing.
- Real user data is owned by `gql_ug`, so only `display_name` is stored here.

## Events domain (shared infrastructure)

### EventModel (EventDBModel.py)
- Table: `events_evolution`.
- Purpose: reusable event entity (used by tests/other parts of the stack).
- Self-referential tree: `masterevent_id` + `subevents` (materialized path style).
- Computed properties: `duration`, `valid`.

### EventInvitationModel (EventInvitationModel.py)
- Table: `event_invitations_evolution`.
- Purpose: invitation of a user to an event.
- Fields: `event_id` (FK), `user_id` (no FK), `state_id` (no FK).
- Why: user and state references are federated.

## Utilities

### uuid.py
- Exposes `uuid = uuid4` helper used for defaults in a few places.
