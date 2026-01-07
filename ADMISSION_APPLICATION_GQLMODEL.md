# AdmissionApplicationGQLModel

**Version:** 1.0  
**Status:** Production - With Simple RBAC  
**Module:** `src/GraphTypeDefinitions/AdmissionApplicationGQLModel.py`  
**Created:** January 2026

## Overview

The `AdmissionApplicationGQLModel` is a Strawberry GraphQL federated type that manages admission applications in the university system. It represents a single applicant's application to an admission process.

**Key features:**
- ✅ Federation support (federated with UserGQLModel)
- ✅ Role-based access control (Simple RBAC with AnyRole)
- ✅ Full CRUD mutations (Create, Read, Update, Delete)
- ✅ Related entity resolution (Process, Enrollments, Payments)
- ✅ Audit tracking (createdby_id, changedby_id)

## Architecture

### Data Model

```
AdmissionApplicationGQLModel
├── id: IDType [Federation Key]
├── process_id: IDType → AdmissionProcessGQLModel
├── applicant_user_id: IDType → User (federated)
├── applicant_name: str
├── applicant_email: str
├── applied_date: datetime
├── status_id: IDType
├── created: datetime [Audit]
├── createdby_id: IDType [Audit]
├── lastchange: datetime [Audit]
├── changedby_id: IDType [Audit]
├── Relationships:
│   ├── process → AdmissionProcessGQLModel
│   ├── enrollments[] → EnrollmentGQLModel[]
│   └── payments[] → PaymentGQLModel[]
```

### Class Hierarchy

```python
BaseGQLModel (base class)
    ↓
AdmissionApplicationGQLModel (@strawberry.federation.type)
    ├── Query: AdmissionApplicationQuery
    ├── Mutations: AdmissionApplicationMutation
    ├── Input: AdmissionApplicationInsertGQLModel
    ├── Input: AdmissionApplicationUpdateGQLModel
    ├── Input: AdmissionApplicationDeleteGQLModel
    └── Input: AdmissionApplicationInputFilter
```

## Components

### 1. Input Models

#### AdmissionApplicationInputFilter
Used for filtering admission applications in queries.

```python
@createInputs2
class AdmissionApplicationInputFilter:
    id: IDType
    process_id: IDType
    applicant_user_id: IDType
    applicant_name: str
    applicant_email: str
    applied_date: datetime.datetime
    status_id: IDType
```

**Usage in queries:**
```graphql
query {
  admissionApplicationPage(
    where: {
      processId: "process-uuid"
      applicantName: "John"
    }
  ) {
    id
    applicantName
  }
}
```

#### AdmissionApplicationInsertGQLModel
Input for creating new admission applications.

```python
@strawberry.input
class AdmissionApplicationInsertGQLModel:
    process_id: Optional[IDType] = None
    applicant_user_id: Optional[IDType] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applied_date: Optional[datetime.datetime] = None
    status_id: Optional[IDType] = None
```

**Auto-set fields (by mutation):**
- `createdby_id` ← Current user ID
- `rbacobject_id` ← None (for Simple RBAC compatibility)

#### AdmissionApplicationUpdateGQLModel
Input for updating existing admission applications.

```python
@strawberry.input
class AdmissionApplicationUpdateGQLModel:
    id: IDType  # Required - identifies which record to update
    lastchange: datetime.datetime  # Required - optimistic concurrency control
    process_id: Optional[IDType] = None
    applicant_user_id: Optional[IDType] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None
    applied_date: Optional[datetime.datetime] = None
    status_id: Optional[IDType] = None
```

**Important:** 
- `id` and `lastchange` are required for concurrency safety
- Omitted fields are not updated (only changed fields needed)

#### AdmissionApplicationDeleteGQLModel
Input for deleting admission applications.

```python
@strawberry.input
class AdmissionApplicationDeleteGQLModel:
    id: IDType  # Required - which record to delete
    lastchange: datetime.datetime  # Required - concurrency control
```

### 2. Query Type

#### AdmissionApplicationQuery

```python
@strawberry.type(description="Admission application queries")
class AdmissionApplicationQuery:
    admission_application_by_id: Optional[AdmissionApplicationGQLModel]
    admission_application_page: List[AdmissionApplicationGQLModel]
```

**Query: By ID**

```graphql
query {
  admissionApplicationById(id: "app-123") {
    id
    applicantName
    applicantEmail
    appliedDate
    process {
      id
      name
    }
  }
}
```

**Permissions:** `OnlyForAuthentized` (authenticated users only)

**Usage in Python:**
```python
async def get_application(info, app_id: str):
    result = await AdmissionApplicationGQLModel.load_with_loader(info, id=app_id)
    return result
```

**Query: Page with Filtering**

```graphql
query {
  admissionApplicationPage(
    skip: 0
    limit: 20
    where: {
      processId: "proc-123"
      applicantName: "Smith"
    }
  ) {
    id
    applicantName
    applicantEmail
    status { id name }
  }
}
```

**Permissions:** `OnlyForAuthentized` (authenticated users only)

**Features:**
- Pagination with `skip` and `limit`
- Filtering with `where` clause (AdmissionApplicationInputFilter)
- Resolver: `PageResolver[AdmissionApplicationGQLModel]`

### 3. Mutation Type

#### AdmissionApplicationMutation

All three mutations use combined permissions:
1. `OnlyForAuthentized` - Must be logged in
2. `AnyRole` - Must have at least one role

```python
@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    admission_application_insert(...)
    admission_application_update(...)
    admission_application_delete(...)
```

#### Mutation: Insert (Create)

```graphql
mutation {
  admissionApplicationInsert(application: {
    processId: "proc-123"
    applicantUserId: "user-456"
    applicantName: "Jane Smith"
    applicantEmail: "jane@example.com"
    appliedDate: "2026-01-15T10:00:00Z"
    statusId: "status-1"
  }) {
    ... on AdmissionApplicationGQLModel {
      id
      applicantName
      createdby { id fullname }
    }
    ... on InsertError {
      message
    }
  }
}
```

**Python implementation:**
```python
@strawberry.mutation(
    description="Insert an admission application", 
    permission_classes=[OnlyForAuthentized, AnyRole]
)
async def admission_application_insert(
    self,
    info: strawberry.Info,
    application: AdmissionApplicationInsertGQLModel
) -> Union[AdmissionApplicationGQLModel, InsertError[AdmissionApplicationGQLModel]]:
    user = getUserFromInfo(info=info)
    application.createdby_id = user["id"]  # Auto-set creator
    application.rbacobject_id = None  # For RBAC compatibility
    
    return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(
        info=info, 
        entity=application
    )
```

**Permissions:**
- ✅ User is authenticated
- ✅ User has at least one role (editor, administrátor, viewer, etc.)

**Return types:**
- `AdmissionApplicationGQLModel` - Success, returns created record
- `InsertError[AdmissionApplicationGQLModel]` - Failure with error details

**Behavior:**
- Sets `createdby_id` to current user (permanent audit trail)
- Sets `created` timestamp automatically
- Performs database insert via `Insert` resolver
- Returns complete application object on success

**Error scenarios:**
- ❌ User not authenticated → Denied (OnlyForAuthentized)
- ❌ User has no roles → Denied (AnyRole)
- ❌ Invalid data → InsertError returned
- ❌ Database constraint violation → InsertError returned

#### Mutation: Update

```graphql
mutation {
  admissionApplicationUpdate(application: {
    id: "app-123"
    lastchange: "2026-01-15T12:00:00Z"
    applicantName: "Jane Marie Smith"
    applicantEmail: "jane.marie@example.com"
    statusId: "status-2"
  }) {
    ... on AdmissionApplicationGQLModel {
      id
      applicantName
      changedby { id fullname }
      lastchange
    }
    ... on UpdateError {
      message
    }
  }
}
```

**Python implementation:**
```python
@strawberry.mutation(
    description="Update an admission application",
    permission_classes=[OnlyForAuthentized, AnyRole],
    extensions=[LoadDataExtension[UpdateError, AdmissionApplicationGQLModel]()]
)
async def admission_application_update(
    self,
    info: strawberry.Info,
    application: AdmissionApplicationUpdateGQLModel,
    db_row: typing.Any
) -> Union[AdmissionApplicationGQLModel, UpdateError[AdmissionApplicationGQLModel]]:
    user = getUserFromInfo(info=info)
    application.changedby_id = user["id"]  # Auto-set who changed it
    
    return await Update[AdmissionApplicationGQLModel].DoItSafeWay(
        info=info, 
        entity=application
    )
```

**Permissions:**
- ✅ User is authenticated
- ✅ User has at least one role

**Important fields:**
- `id` - Required, identifies which record to update
- `lastchange` - Required, used for optimistic concurrency control
- Other fields - Optional, only specified fields are updated

**Behavior:**
- Loads existing record via `LoadDataExtension`
- Validates `lastchange` matches database (prevents conflicts)
- Sets `changedby_id` to current user
- Updates `lastchange` timestamp automatically
- Performs database update
- Returns updated application on success

**Error scenarios:**
- ❌ User not authenticated → Denied
- ❌ User has no roles → Denied
- ❌ Record not found → UpdateError
- ❌ Concurrency conflict (lastchange mismatch) → UpdateError
- ❌ Invalid data → UpdateError

#### Mutation: Delete

```graphql
mutation {
  admissionApplicationDelete(application: {
    id: "app-123"
    lastchange: "2026-01-15T12:00:00Z"
  }) {
    message
  }
}
```

**Python implementation:**
```python
@strawberry.mutation(
    description="Delete an admission application",
    permission_classes=[OnlyForAuthentized, AnyRole],
    extensions=[LoadDataExtension[DeleteError, AdmissionApplicationGQLModel]()]
)
async def admission_application_delete(
    self,
    info: strawberry.Info,
    application: AdmissionApplicationDeleteGQLModel,
    db_row: typing.Any
) -> Optional[DeleteError[AdmissionApplicationGQLModel]]:
    return await Delete[AdmissionApplicationGQLModel].DoItSafeWay(
        info=info, 
        entity=application
    )
```

**Permissions:**
- ✅ User is authenticated
- ✅ User has at least one role

**Behavior:**
- Loads existing record via `LoadDataExtension`
- Validates `lastchange` for concurrency control
- Performs database delete (hard delete)
- Returns None on success (or DeleteError on failure)

**Return type:**
- `None` - Success (record deleted)
- `DeleteError` - Failure with error details

**Error scenarios:**
- ❌ User not authenticated → Denied
- ❌ User has no roles → Denied
- ❌ Record not found → DeleteError
- ❌ Concurrency conflict → DeleteError

### 4. Field Permissions

All main fields require `OnlyForAuthentized`:

```python
process_id: Optional[IDType] = strawberry.field(
    default=None, 
    description="admission process reference", 
    permission_classes=[OnlyForAuthentized]
)
applicant_user_id: Optional[IDType] = strawberry.field(
    default=None, 
    description="applicant user reference", 
    permission_classes=[OnlyForAuthentized]
)
applicant_name: Optional[str] = strawberry.field(
    default=None, 
    description="applicant full name", 
    permission_classes=[OnlyForAuthentized]
)
applicant_email: Optional[str] = strawberry.field(
    default=None, 
    description="applicant email", 
    permission_classes=[OnlyForAuthentized]
)
applied_date: Optional[datetime.datetime] = strawberry.field(
    default=None, 
    description="application date", 
    permission_classes=[OnlyForAuthentized]
)
status_id: Optional[IDType] = strawberry.field(
    default=None, 
    description="application status id", 
    permission_classes=[OnlyForAuthentized]
)
```

**Effect:** Unauthenticated users cannot read these fields on the type.

### 5. Related Fields (Resolvers)

#### Process (Scalar Resolution)

```python
process: Optional["AdmissionProcessGQLModel"] = strawberry.field(
    description="related admission process",
    permission_classes=[OnlyForAuthentized],
    resolver=ScalarResolver["AdmissionProcessGQLModel"](
        fkey_field_name="process_id"
    )
)
```

**Example query:**
```graphql
query {
  admissionApplicationById(id: "app-123") {
    id
    applicantName
    process {
      id
      name
      startDate
    }
  }
}
```

**Resolver:** Follows `process_id` foreign key and loads related process.

#### Enrollments (Vector Resolution)

```python
enrollments: List["EnrollmentGQLModel"] = strawberry.field(
    description="enrollments derived from this application",
    permission_classes=[OnlyForAuthentized],
    resolver=VectorResolver["EnrollmentGQLModel"](
        fkey_field_name="application_id",
        whereType=EnrollmentInputFilter
    )
)
```

**Example query:**
```graphql
query {
  admissionApplicationById(id: "app-123") {
    id
    enrollments {
      id
      studentUser { id fullname }
      course { id name }
    }
  }
}
```

**Resolver:** Finds all enrollments where `application_id` = application.id

#### Payments (Vector Resolution)

```python
payments: List["PaymentGQLModel"] = strawberry.field(
    description="payments for this application",
    permission_classes=[OnlyForAuthentized],
    resolver=VectorResolver["PaymentGQLModel"](
        fkey_field_name="application_id",
        whereType=PaymentInputFilter
    )
)
```

**Example query:**
```graphql
query {
  admissionApplicationById(id: "app-123") {
    id
    payments {
      id
      amount
      status
      paidDate
    }
  }
}
```

**Resolver:** Finds all payments where `application_id` = application.id

## Usage Patterns

### Complete CRUD Workflow

```graphql
# 1. CREATE - Estera (editor role) creates new application
mutation {
  admissionApplicationInsert(application: {
    processId: "process-2026"
    applicantName: "John Doe"
    applicantEmail: "john@example.com"
    appliedDate: "2026-01-15T00:00:00Z"
  }) {
    ... on AdmissionApplicationGQLModel {
      id  # Returns: "app-uuid-123"
      applicantName
      createdby { id fullname }
    }
  }
}

# 2. READ - Query the created application
query {
  admissionApplicationById(id: "app-uuid-123") {
    id
    applicantName
    applicantEmail
    process {
      id
      name
    }
    enrollments {
      id
      course { name }
    }
  }
}

# 3. UPDATE - Same user updates the application
mutation {
  admissionApplicationUpdate(application: {
    id: "app-uuid-123"
    lastchange: "2026-01-15T10:00:00Z"
    applicantEmail: "john.doe@example.com"
    statusId: "status-approved"
  }) {
    ... on AdmissionApplicationGQLModel {
      id
      applicantEmail
      changedby { fullname }
    }
  }
}

# 4. DELETE - Admin deletes if needed
mutation {
  admissionApplicationDelete(application: {
    id: "app-uuid-123"
    lastchange: "2026-01-15T10:30:00Z"
  }) {
    message
  }
}
```

### Filtering and Pagination

```graphql
query {
  admissionApplicationPage(
    skip: 0
    limit: 50
    where: {
      processId: "process-2026"
      applicantName: "Smith"
    }
  ) {
    id
    applicantName
    applicantEmail
    appliedDate
    process { name }
  }
}
```

### Related Entity Navigation

```graphql
query {
  admissionApplicationPage(limit: 100) {
    id
    applicantName
    
    # Related process
    process {
      id
      name
      startDate
      endDate
    }
    
    # Related enrollments
    enrollments(limit: 10) {
      id
      studentUser { fullname email }
      course { code name }
      status
    }
    
    # Related payments
    payments {
      id
      amount
      status
      paidDate
    }
  }
}
```

## Permission Model

### Permission Layers

**Layer 1: Authentication**
```
OnlyForAuthentized
├── ✅ Logged-in user → Allowed
└── ❌ Not logged in → Denied
```

**Layer 2: Role-Based**
```
AnyRole
├── ✅ User has roles ["editor"] → Allowed
├── ✅ User has roles ["administrátor", "viewer"] → Allowed
└── ❌ User has roles [] or None → Denied
```

**Combined (Mutations):**
```
Both must pass:
  1. User is authenticated (Layer 1)
  2. User has at least one role (Layer 2)
```

### Access Matrix

| Operation | Query/List | By ID | Insert | Update | Delete |
|-----------|-----------|-------|--------|--------|--------|
| Permission | OnlyForAuthentized | OnlyForAuthentized | OnlyForAuthentized + AnyRole | OnlyForAuthentized + AnyRole | OnlyForAuthentized + AnyRole |
| Logged-in, has role | ✅ Read | ✅ Read | ✅ Mutate | ✅ Mutate | ✅ Mutate |
| Logged-in, no role | ✅ Read | ✅ Read | ❌ Denied | ❌ Denied | ❌ Denied |
| Not logged in | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied | ❌ Denied |

### Audit Trail

Every mutation is tracked:

```python
# On INSERT
application.createdby_id = user["id"]      # Who created it
application.created = now()                 # When created

# On UPDATE
application.changedby_id = user["id"]       # Who changed it
application.lastchange = now()              # When changed (automatic)

# Always available in queries
query {
  admissionApplicationById(id: "...") {
    id
    createdby { id fullname email }
    created
    changedby { id fullname email }
    lastchange
  }
}
```

## Error Handling

### Possible Errors

#### Permission Denied
```json
{
  "errors": [
    {
      "message": "User must have at least one role to perform this action",
      "extensions": {
        "code": "FORBIDDEN"
      }
    }
  ]
}
```

**Cause:** User trying to mutate without any role assigned.

**Solution:** Grant user a role (editor, administrátor, viewer, etc.)

#### Not Authenticated
```json
{
  "errors": [
    {
      "message": "Only for authentized users",
      "extensions": {
        "code": "UNAUTHENTICATED"
      }
    }
  ]
}
```

**Cause:** User not logged in.

**Solution:** Authenticate user first.

#### Validation Error (Insert)
```json
{
  "errors": [
    {
      "message": "Validation failed",
      "extensions": {
        "code": "INVALID_INPUT"
      }
    }
  ],
  "data": {
    "admissionApplicationInsert": {
      "message": "Field 'applicant_email' is invalid format"
    }
  }
}
```

**Cause:** Invalid input data.

**Solution:** Validate input before sending or fix data format.

#### Concurrency Conflict (Update/Delete)
```json
{
  "data": {
    "admissionApplicationUpdate": {
      "message": "Record was modified by another user. Please refresh and try again."
    }
  }
}
```

**Cause:** `lastchange` timestamp doesn't match current database value.

**Solution:** Refresh the record and retry with current `lastchange`.

### Best Practices

1. **Always include lastchange in updates/deletes**
   ```graphql
   mutation {
     admissionApplicationUpdate(application: {
       id: "..."
       lastchange: "2026-01-15T12:00:00Z"  # Must match DB
       ...
     })
   }
   ```

2. **Check for errors in mutations**
   ```graphql
   mutation {
     admissionApplicationInsert(application: {...}) {
       ... on AdmissionApplicationGQLModel {
         id
       }
       ... on InsertError {
         message
       }
     }
   }
   ```

3. **Handle permission denied gracefully**
   - Show "You don't have permission to perform this action"
   - Offer to request access or contact admin

4. **Retry on concurrency conflict**
   - Query latest record
   - Merge changes if needed
   - Retry update with new `lastchange`

## Integration Points

### With Other GraphQL Types

- **AdmissionProcessGQLModel** - Referenced via `process_id`
- **UserGQLModel** - Referenced via `applicant_user_id` (federated)
- **EnrollmentGQLModel** - Related via enrollments list
- **PaymentGQLModel** - Related via payments list
- **EventGQLModel** - Through admission process

### With Database Layer

- **Table:** `admissionapplication`
- **Model:** `AdmissionApplicationModel` (DBDefinitions)
- **Loader:** `AdmissionApplicationModel` (getLoader method)

### With Authentication

- Uses `getUserFromInfo()` to extract current user
- Sets `createdby_id` and `changedby_id` automatically
- Supports role-based access via `AnyRole` permission

## Configuration

### Required Imports

```python
import typing
import datetime
import strawberry

from uoishelpers.resolvers import (
    getLoadersFromInfo,
    PageResolver,
    createInputs2,
    VectorResolver,
    ScalarResolver,
    getUserFromInfo,
    InsertError,
    UpdateError,
    DeleteError,
    Insert,
    Update,
    Delete
)
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from .rbac_simple import AnyRole
from .BaseGQLModel import BaseGQLModel, IDType
```

### Lazy Loading

Types are lazily loaded to avoid circular imports:

```python
AdmissionProcessGQLModel = typing.Annotated[
    "AdmissionProcessGQLModel",
    strawberry.lazy(".AdmissionProcessGQLModel")
]
```

This prevents import cycles while maintaining type hints.

## Performance Considerations

- **Batch loading** - Uses DataLoader pattern for efficiency
- **Lazy loading** - Federation types loaded on-demand
- **Query optimization** - Resolvers use batch queries where possible
- **Concurrency** - Optimistic locking via `lastchange` prevents conflicts

## Testing

### Test Cases

```python
def test_admission_application_insert_with_role():
    # User with role can insert
    pass

def test_admission_application_insert_without_role():
    # User without role denied
    pass

def test_admission_application_update_permissions():
    # Update requires auth + role
    pass

def test_admission_application_delete_permissions():
    # Delete requires auth + role
    pass

def test_admission_application_concurrency():
    # Concurrency conflict on wrong lastchange
    pass

def test_admission_application_query_by_id():
    # Query returns correct application
    pass

def test_admission_application_query_page():
    # Pagination works correctly
    pass
```

## Future Enhancements

1. **Creator-Only Ownership** - Allow only creator to update/delete
2. **Group-Based Access** - Integrate `rbacobject_id` for group control
3. **Soft Deletes** - Mark as deleted instead of hard delete
4. **Status Workflow** - Enforce valid status transitions
5. **Notifications** - Notify admins on new applications
6. **Bulk Operations** - Batch insert/update multiple applications

## Related Documentation

- **Simple RBAC**: `SIMPLE_RBAC.md` - Role-based permission system
- **Unified RBAC**: `UNIFIED_RBAC_SYSTEM.md` - Advanced group-based access
- **BaseGQLModel**: `src/GraphTypeDefinitions/BaseGQLModel.py` - Base class
- **AdmissionProcessGQLModel**: `src/GraphTypeDefinitions/AdmissionProcessGQLModel.py`
- **Resolvers**: `uoishelpers.resolvers` - Query/mutation helpers

## Troubleshooting

**Q: How do I check who created an application?**  
A: Query the `createdby` field:
```graphql
query {
  admissionApplicationById(id: "...") {
    createdby { id fullname email }
  }
}
```

**Q: User gets "User must have at least one role" error?**  
A: Grant the user a role in the UG system. Verify roles are loaded correctly in context.

**Q: Update returns concurrency error?**  
A: The record was modified by another user. Query fresh data and retry with updated `lastchange`.

**Q: Can I see who made the last change?**  
A: Yes, query:
```graphql
query {
  admissionApplicationById(id: "...") {
    changedby { id fullname email }
    lastchange
  }
}
```

**Q: How to migrate to group-based RBAC later?**  
A: See `UNIFIED_RBAC_SYSTEM.md` migration guide.

---

**Last Updated:** January 2026  
**Maintainer:** Development Team  
**Status:** ✅ Production Ready

