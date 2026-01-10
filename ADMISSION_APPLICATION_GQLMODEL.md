# AdmissionApplicationGQLModel

**Version:** 2.0
**Status:** Production - Unified RBAC
**Module:** `src/GraphTypeDefinitions/AdmissionApplicationGQLModel.py`
**Updated:** 2026-01-xx

## Overview

`AdmissionApplicationGQLModel` represents a single application submitted by a user into an admission process. It exposes the application data, relations to process/payment, and CRUD mutations with unified RBAC.

**Key features:**
- Federation support
- Unified RBAC (creator ownership + group roles)
- Full CRUD mutations
- Relations to `AdmissionProcess` and `AdmissionPayment`
- Audit fields from `BaseGQLModel`

## Data Model (GraphQL)

```
AdmissionApplicationGQLModel
├── id: IDType [Federation Key]
├── applicant_id: IDType → AdmissionApplicantGQLModel
├── applied_date: datetime
├── process_id: IDType → AdmissionProcessGQLModel
├── payment_id: IDType → AdmissionPaymentGQLModel
├── created / lastchange / createdby_id / changedby_id / rbacobject_id
├── process (relation)
├── payment (relation)
└── applicant (relation)
```

## Input Models

### AdmissionApplicationInputFilter
Used for filtering in `admissionApplicationPage`.

```python
@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    applicant_id: IDType
    applied_date: datetime.datetime
    process_id: IDType
    payment_id: IDType
```

### AdmissionApplicationInsertGQLModel
```python
@strawberry.input
class AdmissionApplicationInsertGQLModel:
    applicant_id: Optional[IDType]
    applied_date: Optional[datetime]
    process_id: Optional[IDType]
    payment_id: Optional[IDType]
```

### AdmissionApplicationUpdateGQLModel
```python
@strawberry.input
class AdmissionApplicationUpdateGQLModel:
    id: IDType
    lastchange: datetime
    applicant_id: Optional[IDType]
    applied_date: Optional[datetime]
    process_id: Optional[IDType]
    payment_id: Optional[IDType]
```

### AdmissionApplicationDeleteGQLModel
```python
@strawberry.input
class AdmissionApplicationDeleteGQLModel:
    id: IDType
    lastchange: datetime
```

## Queries

### admissionApplicationById
```graphql
query {
  admissionApplicationById(id: "app-uuid") {
    id
    applicantId
    applicant { id street city }
    process { id }
    payment { id requiredAmount }
  }
}
```

### admissionApplicationPage
```graphql
query {
  admissionApplicationPage(where: { processId: "proc-uuid" }) {
    id
    applicantId
    appliedDate
  }
}
```

## Mutations

### admissionApplicationInsert
```graphql
mutation {
  admissionApplicationInsert(application: {
    applicantId: "applicant-uuid"
    appliedDate: "2025-03-01T08:00:00"
    processId: "proc-uuid"
    paymentId: "payment-uuid"
  }) {
    __typename
    ... on AdmissionApplicationGQLModel { id }
  }
}
```

### admissionApplicationUpdate
```graphql
mutation {
  admissionApplicationUpdate(application: {
    id: "app-uuid"
    lastchange: "2025-03-01T08:00:00"
    city: "Praha"
  }) {
    __typename
    ... on AdmissionApplicationGQLModel { id city }
  }
}
```

### admissionApplicationDelete
```graphql
mutation {
  admissionApplicationDelete(application: {
    id: "app-uuid"
    lastchange: "2025-03-01T08:00:00"
  }) {
    __typename
  }
}
```

## RBAC Summary

Permissions are enforced by unified RBAC extensions:
- **Read:** Any authenticated user
- **Insert / Update:** `EDITOR_ROLES`
- **Delete:** `ADMIN_ROLES`

Role lists are defined in `src/GraphTypeDefinitions/unified_rbac_extensions.py`.
