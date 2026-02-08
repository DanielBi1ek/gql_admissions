# GQL Admissions - Unified Documentation

This document consolidates the current project state, data model, GraphQL API,
RBAC rules, and the admission lifecycle into one place.

## 1) Project Overview

GQL Admissions is a federated GraphQL service that manages admission offers,
applications, applicant profiles, and related payment templates. The service is
integrated into a federation together with `gql_ug` (users/roles) and is
typically accessed via the gateway at `localhost:33001`.

Key goals:
- Manage offers for study programs with a valid application window.
- Allow applicants to submit and withdraw applications.
- Allow study office admins to manage bank accounts, payment templates, offers,
  and accept applications.

## 2) Services, Ports, and Endpoints

Main endpoints:
- Local service (non-federated): `http://127.0.0.1:8001/gql`
- Federated gateway: `http://127.0.0.1:33001/api/gql`
- OAuth demo login: `http://127.0.0.1:33001/oauth/login3`

When using federation, authentication is required. The frontend/gateway will
redirect unauthenticated requests to `/oauth/login2` or `/oauth/login3`.

## 3) Runtime Configuration

Environment is loaded from `environment.txt` when running `uvicorn main:app --env-file environment.txt --port 8001`. Key flags:
- `DEMO` / `DEMODATA`: enable demo data loading.
- `GQLUG_ENDPOINT_URL`: federation link to `gql_ug`.
- `ADMISSIONS_ADMIN_GROUP_ID` and `ADMISSIONS_ADMIN_ROLETYPE_ID`: IDs that
  define admissions admin role.
- `GQL_ENDPOINT_URL`/`GQLUG_ENDPOINT_URL`: URLs that tests hit when they import `main` or call live federation.

Developer/tests context:
- `tests/shared.py` provisions in-memory SQLite sessions and now automatically commits/rolls back around every `execute_gql` call. If a mutation raises an integrity error, the resolver sets `context["_transaction_failed"]` so the harness rolls the session back and keeps subsequent tests stable.
- GraphQL tests expect the seeding helper `prepare_demodata` to run before each module. It feeds `systemdata.json` through `uoishelpers.feeders.ImportModels`, so keep that file aligned with the current DB schema.

## 4) Data Model (DBDefinitions)

Shared base:
- `BaseModel`: `id`, `created`, `lastchange`, `createdby_id`, `changedby_id`,
  `rbacobject_id`.
- `createdby_id` and `changedby_id` are UUID references to users in `gql_ug`.

Core tables:
- `study_programs` (StudyProgramModel)
  - Fixed reference data for programs, used in offers.
- `admission_bank_accounts` (AdmissionBankAccountModel)
  - `account_prefix`, `account_number`, `bank_code`, `description`.
  - Unique constraint on (account_prefix, account_number, bank_code).
- `admission_payment_infos` (AdmissionPaymentInfoModel)
  - `required_amount > 0`, `bank_account_id` (FK).
- `admission_offers` (AdmissionOfferModel)
  - `program_id` (FK), `payment_info_id` (FK),
    `application_start_date`, `application_end_date`.
  - Unique constraint on `program_id` (one offer per program).
- `admission_payments` (AdmissionPaymentModel)
  - `required_amount > 0`, `paid_at`, `bank_statement_id` (FK).
- `admission_processes` (AdmissionProcessModel)
  - `payment_id` (FK).
- `admission_applicants` (AdmissionApplicantModel)
  - `applicant_user_id` (unique), personal contact data fields.
- `admission_applications` (AdmissionApplicationModel)
  - `applicant_id` (FK), `offer_id` (FK), `payment_id` (FK),
    `applied_date`,
    `accepted`, `accepted_at`, `acceptedby_id`,
    `withdrawn`, `withdrawn_at`, `withdrawnby_id`,
    `process_id` (FK).
  - Unique constraint on (applicant_id, offer_id).

Reference tables:
- `bank_statements` (BankStatementModel) - read-only input for payment matching.
- `users` (UserModel) - lightweight local reference for demo data.

## 5) GraphQL API - Queries

All admission domain read operations require authentication (`OnlyForAuthentized`).
`currentUserRole` returns `null` when the user is not authenticated.

Core query endpoints:
- Offers: `admissionOfferById`, `admissionOfferPage`
- Applications: `admissionApplicationById`, `admissionApplicationPage`
- Applicants: `admissionApplicantById`, `admissionApplicantPage`
- Payments: `admissionPaymentById`, `admissionPaymentPage`
- Payment templates: `admissionPaymentInfoById`, `admissionPaymentInfoPage`
- Bank accounts: `admissionBankAccountById`, `admissionBankAccountPage`
- Processes: `admissionProcessById`, `admissionProcessPage`
- User permissions: `currentUserRole`

Visibility rules:
- Admin sees all applications and applicants.
- Non-admin users can only see their own applicant profile and applications.

Pagination notes:
- Page queries accept `skip`, `limit`, `orderby`, `desc`, and `offset`.
- `offset` is treated as an alias to `skip`.

## 6) GraphQL API - Mutations

### Applicant
- `admissionApplicantInit` (applicant):
  - Creates a profile linked to the current user.
  - Auto-fills firstname/lastname from `me`.
  - Allowed only if profile does not exist.
- `admissionApplicantInsert` (admin)
- `admissionApplicantUpdate` (admin or owner, only if no applications exist)
- `admissionApplicantDelete` (admin or owner, only if no applications exist)

### Bank accounts and payment templates (admin)
- `admissionBankAccountCreate`
  - Validates numeric prefix/number/bank_code.
- `admissionBankAccountInsert`/`admissionBankAccountUpdate`/`Delete`
  - Numeric validation is enforced via `validate_digits`.
  - Duplicate prefix/number/bank_code combinations now surface as `AdmissionBankAccountGQLModelInsertError` and leave the surrounding test session in a valid state (the mutation rolls back its loader session and flags the transaction for the harness).
- `admissionPaymentInfoCreate`
  - Validates numeric required_amount and existing bank_account_id.
- `admissionPaymentInfoInsert`, `admissionPaymentInfoUpdate`,
  `admissionPaymentInfoDelete`

### Offers (admin)
- `admissionOfferCreate`
  - Validates program exists, payment info exists, unique offer per program,
    and dates (`end > start`, not same day).
- `admissionOfferInsert`, `admissionOfferUpdate`, `admissionOfferDelete`

### Applications
- `admissionApplicationSubmit` (applicant):
  - Requires existing applicant profile.
  - Checks offer exists and date window is open.
  - Ensures one application per offer.
  - Creates a pending payment and the application in a single transaction.
- `admissionApplicationAccept` (admin):
  - Fails if withdrawn or already accepted.
  - Creates `AdmissionProcess` and marks application accepted (single transaction).
- `admissionApplicationWithdraw` (applicant):
  - Only own application.
  - Allowed even if already accepted.
- `admissionApplicationInsert` and `admissionApplicationUpdate` (admin only)

### Payments (admin)
- `admissionPaymentInsert`, `admissionPaymentUpdate`, `admissionPaymentDelete`
  - `required_amount` must be numeric and > 0.

## 7) RBAC Summary

Admissions admin is defined by:
- `ADMISSIONS_ADMIN_GROUP_ID`
- `ADMISSIONS_ADMIN_ROLETYPE_ID`

Rules:
- Read: authenticated users only.
- Admin-only: maintenance inserts/updates/deletes for offers, payment info,
  bank accounts, payments, and administrative application CRUD.
- Applicant ownership enforced for:
  - `admissionApplicantUpdate` / `admissionApplicantDelete`
  - `admissionApplicationWithdraw`
  - application visibility in queries.

**Permission classes implemented in** `src/GraphTypeDefinitions/admission_permissions.py`:
- `ADMISSION_READ_PERMISSION = [OnlyForAuthentized]` protects every field/page query.
- `ADMISSION_ADMIN_PERMISSION = [OnlyForAuthentized, AdmissionsAdminPermission]` is wired into admin mutations via `admission_admin_required` and `admission_field(permission_level="admin")`.
- `ADMISSION_USER_PERMISSION = [OnlyForAuthentized, AdmissionsUserPermission]` gates applicant-facing mutations such as `admissionApplicantInit`.
- `ADMISSION_OWNERSHIP_PERMISSION = [OnlyForAuthentized, AdmissionsOwnershipPermission]` is available for “owner or admin” flows when a resolver needs to double-check the current user ID.

**Admin detection** is name-based: `AdmissionsAdminPermission` calls `is_admissions_admin`, which treats a role as administrative when its `roletype.name` (lowercased) is in `{ "admin", "administrator", "administrátor", "rektor", "prorektor", "admission_admin", "study_office", "admission_officer" }`. The previous `ADMISSIONS_ADMIN_GROUP_ID` / `ADMISSIONS_ADMIN_ROLETYPE_ID` environment variables are still available for other layers, but the actual GraphQL permission check uses the role-name whitelist above.

**Declarative helpers**:
- `admission_field()` places the right permission class on a Strawberry field based on `permission_level` so contributors don’t forget to restrict access.
- Decorators (`admission_admin_required`, `admission_user_required`, etc.) wrap resolvers with the same centralized rules.

This means RBAC is enforced consistently at the schema layer: every resolver/field either uses the helpers or manually specifies one of the permission lists defined here.

## 8) Admission Lifecycle (Functional Flow)

1) Applicant profile init:
   - User calls `admissionApplicantInit`.
2) Admin config:
   - Create bank account (`admissionBankAccountCreate`).
   - Create payment template (`admissionPaymentInfoCreate`).
   - Create offer (`admissionOfferCreate`).
3) Applicant submits:
   - `admissionApplicationSubmit` creates payment + application.
4) Admin accepts:
   - `admissionApplicationAccept` creates process and marks acceptance.
5) Applicant can withdraw at any time:
   - `admissionApplicationWithdraw`.

## 9) Validation Rules (Summary)

- Offer:
  - `program_id` and `payment_info_id` must exist.
  - Only one offer per program.
  - End date after start date and not same day.
- Payment info:
  - `required_amount` numeric and > 0.
  - `bank_account_id` must exist.
- Bank account:
  - `account_prefix`, `account_number`, `bank_code` must be numeric.
  - Unique combination of prefix/number/bank_code.
- Application submit:
  - Offer exists and date window is valid.
  - Applicant profile exists.
  - Only one application per offer.
  - Payment info referenced by offer must exist.

## 10) Demo Data

Demo data in this repo is loaded from `systemdata.json` when `DEMODATA=True`.
In docker, `systemdata.rnd.json` can be mounted via volume (not handled here).
These files include:
- Users (roles are provided by `gql_ug`, not stored here).
- Study programs, offers, payment templates, applicants, applications.

## 11) Federation and Auth

Federation uses `gql_ug` for user identity. `WhoAmIExtension` resolves
the current user via:
- `GQLUG_ENDPOINT_URL` (GraphQL `me` query)

For federation access, obtain a token from:
- `GET /oauth/login3` (returns key)
- `POST /oauth/login3` with `{key, username, password}` (returns token)

Then use cookie:
- `authorization=<token>` when calling `/api/gql`.

## 12) Operations and HTML Tools

Static HTMLs:
- `/voyager` -> GraphQL Voyager
- `/doc` -> schema view
- `/ui` -> live data
- `/test` -> tests UI

Metrics:
- `/metrics` (Prometheus)

## 13) Notes

- Tests currently **do not fully pass**. Known failures (2026‑02‑08):
  - `tests/test_admission_business_logic.py::TestBankAccountValidation::test_bank_account_unique_constraint` still reports `PendingRollbackError` after the duplicate insert, meaning an additional rollback is needed in the test harness.
  - Several `tests/test_gt_definitions.py::*Page` cases fail with "Page query returned empty" whenever seeded data isn’t visible to the test session. Until seeding/visibility is fixed, expect these to fail.
  - Deprecation warnings from `datetime.utcnow()` and `strawberry.extensions.runner` are still outstanding.
- Application delete is not supported; withdraw is the official action.
- Some admin-only mutations return `null` on successful delete (by design).
- Schema is created on startup (no migrations). For production, move to a
  migration-based workflow.
