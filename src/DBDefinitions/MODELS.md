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
- Purpose: reusable template with required fee amount and selected bank account.
- Fields: `required_amount`, `bank_account_id` (FK to `admission_bank_accounts`).
- Relationship: `bank_account` (view-only).

### AdmissionBankAccountModel (AdmissionBankAccountModel.py)
- Table: `admission_bank_accounts`.
- Purpose: stored bank account details for admission payments.
- Fields: `account_prefix`, `account_number`, `bank_code`, `description`.

### AdmissionOfferModel (AdmissionOfferModel.py)
- Table: `admission_offers`.
- Purpose: admission offer for a specific study program with a valid application window and payment info.
- Fields: `program_id` (FK), `application_start_date`, `application_end_date`, `payment_info_id` (FK).
- Relationships: `program`, `payment_info` (view-only).
- GraphQL: AdmissionOfferGQLModel with RBAC permissions requiring user authentication. Queries available: `admissionOfferById`, `admissionOfferPage`.
- RBAC: All fields require `OnlyForAuthentized` permission. Mutations (insert/update/delete) require `AnyRole`.

### BankStatementModel (BankStatementModel.py)
- Table: `bank_statements`.
- Purpose: imported payments from bank statements used for matching.
- Fields: `variable_symbol`, `amount_received`.
- Note: treated as read-only reference data (no GraphQL API here).

### AdmissionPaymentModel (AdmissionPaymentModel.py)
- Table: `admission_payments`.
- Purpose: waiting/confirmed admission payments to be matched against bank statements.
- Fields: `required_amount`, `paid_at`, `bank_statement_id` (FK).
- Relationship: `bank_statement` (view-only).

### AdmissionProcessModel (AdmissionProcessModel.py)
- Table: `admission_processes`.
- Purpose: high-level admission process that points to a pending payment condition.
- Fields: `payment_id` (FK to `admission_payments`).
- Relationship: `payment` (view-only).

### AdmissionApplicantModel (AdmissionApplicantModel.py)
- Table: `admission_applicants`.
- Purpose: personal data for admission applicants.
- Fields: `applicant_user_id`, `firstname`, `lastname`, `street`, `house_number`, `city`, `phone_number`, `email`, `databox_number`.

### AdmissionApplicationModel (AdmissionApplicationModel.py)
- Table: `admission_applications`.
- Purpose: submitted application by a user in a specific admission process.
- Fields: `applicant_id` (FK), `applied_date`, `accepted`, `accepted_at`, `acceptedby_id`, `process_id` (FK), `payment_id` (FK), `offer_id` (FK).
- Relationships: `process`, `payment`, `offer`, `applicant` (view-only).
- GraphQL: AdmissionApplicationGQLModel with RBAC permissions. Queries available: `admissionApplicationById`, `admissionApplicationPage`.
- RBAC: All fields require `OnlyForAuthentized` permission. Mutations (insert/update/delete) require `AnyRole` (user must have at least one role).
  - Insert sets `createdby_id` from authenticated user context.
  - Update sets `changedby_id` from authenticated user context.

## Relationships

### AdmissionPayment ↔ BankStatement
- One AdmissionPayment can reference one BankStatement entry.
- `admission_payments.bank_statement_id` points to `bank_statements.id`.

## RBAC System (rbac_simple.py)

### AnyRole Permission Class
- **Purpose**: Simple role-based access control for mutations.
- **Logic**: Allows mutations only if the authenticated user has at least one role assigned.
- **Users without roles**: Cannot perform mutations (create, update, delete operations).
- **Users with roles**: Can perform mutations (e.g., editor, administrator, viewer roles).
- **Context**: User roles are read from `info.context["user"]["roles"]` or `request.scope["user"]["roles"]`.

### Implementation Details
- Checks if `roles` list/tuple is non-empty and contains at least one role string.
- Silently returns `False` for users without a user context (anonymous access).
- Used on all mutation resolvers in AdmissionApplicationGQLModel and AdmissionOfferGQLModel.

## Utilities

### uuid.py
- Exposes `uuid = uuid4` helper used for defaults in a few places.
