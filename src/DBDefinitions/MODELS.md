# DBDefinitions overview

This document describes the current SQLAlchemy models in `src/DBDefinitions` and the intended meaning of each table.
The service is federated, so user references are stored without foreign keys.

## Shared base

### BaseModel (BaseModel.py)
- Common fields: `id`, `created`, `lastchange`, `createdby_id`, `changedby_id`, `rbacobject_id`.
- User and RBAC references are UUIDs without FK constraints because they live in other services.
- `UUIDFKey` and `UUIDColumn` standardize UUID column definitions.

### UserModel (UserModel.py)
- Table: `users`.
- Purpose: lightweight local reference for demo users and seeds.
- Field: `display_name`.

## Core admissions domain

### StudyProgramModel (StudyProgramModel.py)
- Table: `study_programs`.
- Purpose: catalog of study programs used as fixed reference data.
- Field: `name`.
- Note: managed outside this service (no GraphQL API here).

### AdmissionPaymentInfoModel (AdmissionPaymentInfoModel.py)
- Table: `admission_payment_infos`.
- Purpose: reusable template with bank details and required fee amount.
- Fields: `account_prefix`, `account_number`, `bank_code`, `required_amount`.

### ExamModel (ExamModel.py)
- Table: `exams`.
- Purpose: admission offer for a specific study program with a valid application window and payment info.
- Fields: `program_id` (FK), `application_start_date`, `application_end_date`, `payment_info_id` (FK).
- Relationships: `program`, `payment_info` (view-only).

### BankStatementPaymentModel (BankStatementPaymentModel.py)
- Table: `bank_statement_payments`.
- Purpose: imported payments from bank statements used for matching.
- Fields: `variable_symbol`, `amount_received`.
- Note: treated as read-only reference data (no GraphQL API here).

### AdmissionPaymentModel (AdmissionPaymentModel.py)
- Table: `admission_payments`.
- Purpose: waiting/confirmed admission payments to be matched against bank statements.
- Fields: `required_amount`, `paid_at`, `bank_payment_id` (FK).
- Relationship: `bank_payment` (view-only).

### AdmissionProcessModel (AdmissionProcessModel.py)
- Table: `admission_processes`.
- Purpose: high-level admission process that points to a pending payment condition.
- Fields: `name`, `payment_id` (FK to `admission_payments`).
- Relationship: `payment` (view-only).

### AdmissionApplicationModel (AdmissionApplicationModel.py)
- Table: `admission_applications`.
- Purpose: submitted application by a user.
- Fields: `applicant_user_id` (no FK), `street`, `house_number`, `city`, `postal_code`, `applied_date`,
  `process_id` (FK), `payment_id` (FK).
- Relationships: `process`, `payment` (view-only).

## Utilities

### uuid.py
- Exposes `uuid = uuid4` helper used for defaults in a few places.
