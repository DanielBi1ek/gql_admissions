# Admission Application RBAC Documentation

**Last Updated:** 2026-01-xx
**Version:** 2.0

## Overview

Admission applications use the **Unified RBAC** system implemented in
`src/GraphTypeDefinitions/unified_rbac_extensions.py`. The model is
`AdmissionApplicationGQLModel` and mutations are protected by role-based
extensions with creator ownership semantics.

Key ideas:
- Creator ownership: the user who created a record keeps full access.
- Group permissions: group roles can grant create/update/delete.
- Implicit view: group members can read even without explicit roles.

## Model Scope

The RBAC rules apply to GraphQL operations on `AdmissionApplicationGQLModel`:
- Query: `admissionApplicationById`, `admissionApplicationPage`
- Mutations: `admissionApplicationInsert`, `admissionApplicationUpdate`, `admissionApplicationDelete`

## Permission Levels

| Operation | Required Roles | Notes |
|-----------|----------------|-------|
| READ      | Authenticated user | Implicit view for group members |
| CREATE    | `EDITOR_ROLES` | Also assigns `rbacobject_id` if missing |
| UPDATE    | `EDITOR_ROLES` | Creator can always update |
| DELETE    | `ADMIN_ROLES`  | Creator can always delete |

Role lists are defined in `src/GraphTypeDefinitions/unified_rbac_extensions.py`.

## How It Works

- **Insert** uses `create_insert_permissions(...)` and auto group assignment.
- **Update** uses `create_update_permissions(...)` and validates ownership/roles.
- **Delete** uses `create_delete_permissions(...)` and is restricted to admin roles or creator.

## Example: Insert

```graphql
mutation {
  admissionApplicationInsert(application: {
    applicantUserId: "user-uuid"
    street: "Main"
    houseNumber: "123"
    city: "Brno"
    postalCode: "60200"
    appliedDate: "2025-03-01T08:00:00"
    processId: "proc-uuid"
    paymentId: "payment-uuid"
  }) {
    __typename
    ... on AdmissionApplicationGQLModel { id rbacobjectId createdbyId }
  }
}
```

## Example: Update

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

## Example: Delete

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
