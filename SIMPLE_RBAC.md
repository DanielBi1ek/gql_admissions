# Simple RBAC System

**Version:** 1.0  
**Status:** Production - Basic Role-Based Access Control  
**Module:** `src/GraphTypeDefinitions/rbac_simple.py`  
**Created:** January 2026

## Overview

The Simple RBAC system provides a lightweight, role-based authorization layer for GraphQL mutations. It enforces a single rule: **users must have at least one role assigned to perform mutations**.

This is a foundational RBAC implementation designed to be:
- **Easy to understand** - Single permission class with clear logic
- **Extensible** - Build more complex role requirements on top
- **Non-invasive** - Works alongside existing `OnlyForAuthentized` permission
- **Minimal overhead** - Minimal performance impact

## Philosophy

**"Any role is enough"** - A user with ANY role (editor, administrátor, viewer, reader, etc.) can perform mutations. Users with NO roles are denied.

This approach:
- ✅ Allows IT admins to grant mutation access by role assignment
- ✅ Prevents unauthenticated or untrusted users from mutating data
- ✅ Simplifies initial permission model (before group-based RBAC)
- ✅ Provides clear audit trail (createdby_id tracks who made changes)

## Implementation

### The AnyRole Permission Class

**Location:** `src/GraphTypeDefinitions/rbac_simple.py`

```python
class AnyRole(BasePermission):
    """Simple RBAC permission: allow only users that have any role assigned."""
    
    message = "User must have at least one role to perform this action"
    
    def has_permission(self, source, info, **kwargs) -> bool:
        # Check if user exists in context
        # Extract roles from user object
        # Return True if roles list is non-empty
        # Return False if no roles
```

**Input:** GraphQL `info` object containing request context with user data  
**Output:** Boolean - `True` (allow mutation) or `False` (deny with error message)

### User Context Structure

The permission expects user information in one of these formats:

**Dict-style context (tests/direct calls):**
```python
context = {
    "user": {
        "id": "user-uuid",
        "roles": ["editor", "administrátor"],  # List of role names
        # ... other user fields
    }
}
```

**Object-style context (GraphQL servers):**
```python
class User:
    id: str
    roles: List[str]  # Non-empty = allowed, empty/None = denied

context.user = User(id="...", roles=["editor"])
```

**Role can be:**
- A list: `["editor", "administrátor"]` ✅ Allowed if non-empty
- A string: `"editor"` ✅ Allowed if non-empty/not whitespace
- None/Missing: ❌ Denied
- Empty list: `[]` ❌ Denied

## Usage

### Basic: Add to Mutations

```python
from strawberry.permission import OnlyForAuthentized
from .rbac_simple import AnyRole

@strawberry.mutation(
    description="Create something",
    permission_classes=[OnlyForAuthentized, AnyRole]  # Both conditions required
)
async def create_item(self, info: strawberry.Info, item: ItemInput):
    user = getUserFromInfo(info=info)
    item.createdby_id = user["id"]
    return await Insert[ItemGQLModel].DoItSafeWay(info=info, entity=item)
```

**Permission Chain:**
1. `OnlyForAuthentized` - User must be logged in
2. `AnyRole` - User must have at least one role

If either fails, the mutation is rejected with appropriate error message.

### Apply to Multiple Mutations

```python
@strawberry.type(description="Item mutations")
class ItemMutation:
    @strawberry.mutation(permission_classes=[OnlyForAuthentized, AnyRole])
    async def item_insert(self, info, item: ItemInput):
        # Only users with roles can create
        ...
    
    @strawberry.mutation(permission_classes=[OnlyForAuthentized, AnyRole])
    async def item_update(self, info, item: ItemUpdate):
        # Only users with roles can update
        ...
    
    @strawberry.mutation(permission_classes=[OnlyForAuthentized, AnyRole])
    async def item_delete(self, info, item: ItemDelete):
        # Only users with roles can delete
        ...
```

## Access Scenarios

### Scenario 1: User WITH Role ✅

```
User: Estera
Roles: ["editor"]
Attempting: admissionApplicationInsert

Permission Check:
  1. OnlyForAuthentized → ✅ User is logged in
  2. AnyRole → ✅ User has roles ["editor"]
  
Result: MUTATION ALLOWED
Database: Writes new admission application
         Sets createdby_id = "estera-uuid"
```

### Scenario 2: User WITHOUT Role ❌

```
User: Oliver
Roles: [] or None
Attempting: admissionApplicationInsert

Permission Check:
  1. OnlyForAuthentized → ✅ User is logged in
  2. AnyRole → ❌ User has NO roles
  
Result: MUTATION DENIED
Error: "User must have at least one role to perform this action"
Database: No change
```

### Scenario 3: Unauthenticated User ❌

```
User: Not logged in
Roles: N/A
Attempting: admissionApplicationInsert

Permission Check:
  1. OnlyForAuthentized → ❌ Not authenticated
  2. AnyRole → (Not evaluated, fails at step 1)
  
Result: MUTATION DENIED
Error: (OnlyForAuthentized error message)
Database: No change
```

## Integration with Data Model

### AdmissionApplicationGQLModel Example

```python
# src/GraphTypeDefinitions/AdmissionApplicationGQLModel.py

from .rbac_simple import AnyRole

@strawberry.type(description="Admission application mutations")
class AdmissionApplicationMutation:
    
    @strawberry.mutation(
        description="Insert admission application",
        permission_classes=[OnlyForAuthentized, AnyRole]
    )
    async def admission_application_insert(
        self, info: strawberry.Info, application: AdmissionApplicationInsertGQLModel
    ):
        # User with ANY role can create admission applications
        user = getUserFromInfo(info=info)
        application.createdby_id = user["id"]
        application.rbacobject_id = None
        return await Insert[AdmissionApplicationGQLModel].DoItSafeWay(...)
    
    @strawberry.mutation(
        description="Update admission application",
        permission_classes=[OnlyForAuthentized, AnyRole]
    )
    async def admission_application_update(
        self, info: strawberry.Info, application: AdmissionApplicationUpdateGQLModel, db_row
    ):
        # User with ANY role can update admission applications
        user = getUserFromInfo(info=info)
        application.changedby_id = user["id"]
        return await Update[AdmissionApplicationGQLModel].DoItSafeWay(...)
    
    @strawberry.mutation(
        description="Delete admission application",
        permission_classes=[OnlyForAuthentized, AnyRole]
    )
    async def admission_application_delete(
        self, info: strawberry.Info, application: AdmissionApplicationDeleteGQLModel, db_row
    ):
        # User with ANY role can delete admission applications
        return await Delete[AdmissionApplicationGQLModel].DoItSafeWay(...)
```

## Error Handling

### Permission Denied Response

When a user fails the `AnyRole` check, GraphQL returns:

```json
{
  "errors": [
    {
      "message": "User must have at least one role to perform this action",
      "extensions": {
        "path": ["admissionApplicationInsert"],
        "code": "FORBIDDEN"
      }
    }
  ]
}
```

### Common Scenarios

| User State | Authenticated | Has Roles | OnlyForAuthentized | AnyRole | Result |
|------------|---------------|-----------|-------------------|---------|--------|
| Fresh user | ✅ Yes | ❌ No | ✅ Pass | ❌ Fail | DENIED |
| Role assigned | ✅ Yes | ✅ Yes | ✅ Pass | ✅ Pass | ALLOWED |
| Not logged in | ❌ No | N/A | ❌ Fail | - | DENIED |
| Logged out | ❌ No | N/A | ❌ Fail | - | DENIED |

## How the Permission Check Works

**Step-by-step execution:**

```python
def has_permission(self, source, info, **kwargs) -> bool:
    # 1. Get context from GraphQL info
    ctx = getattr(info, "context", None)
    if ctx is None:
        return False
    
    # 2. Extract user (supports dict and object styles)
    if isinstance(ctx, dict):
        user = ctx.get("user") or ctx.get("current_user")
    else:
        user = getattr(ctx, "user", None)
    
    if not user:
        return False
    
    # 3. Extract roles from user
    if isinstance(user, dict):
        roles = user.get("roles")
    else:
        roles = getattr(user, "roles", None)
    
    # 4. Check if roles exist and are non-empty
    if roles is None:
        return False
    
    # 5. Handle different role formats
    if isinstance(roles, str):
        return bool(roles.strip())  # Non-empty string
    
    if isinstance(roles, (list, tuple)):
        return len(roles) > 0  # Non-empty list
    
    try:
        return len(roles) > 0  # Other iterables
    except TypeError:
        return bool(roles)  # Fallback to truthiness
```

## Extending Simple RBAC

### Example 1: Only Editors Can Mutate

```python
class EditorOnly(BasePermission):
    message = "Only editors can perform this action"
    
    def has_permission(self, source, info, **kwargs) -> bool:
        ctx = getattr(info, "context", None)
        user = ctx.get("user") if isinstance(ctx, dict) else getattr(ctx, "user", None)
        roles = user.get("roles") if isinstance(user, dict) else getattr(user, "roles", None)
        return "editor" in (roles or [])

# Usage
@strawberry.mutation(permission_classes=[OnlyForAuthentized, EditorOnly])
async def sensitive_mutation(self, info):
    ...
```

### Example 2: Admin or Creator

```python
class AdminOrCreator(BasePermission):
    message = "Only admins or creators can perform this action"
    
    def has_permission(self, source, info, **kwargs) -> bool:
        ctx = getattr(info, "context", None)
        user = ctx.get("user") if isinstance(ctx, dict) else getattr(ctx, "user", None)
        roles = user.get("roles") if isinstance(user, dict) else getattr(user, "roles", None)
        
        # Admin can do it
        if "administrátor" in (roles or []):
            return True
        
        # Creator can do it (check createdby_id from kwargs)
        if kwargs.get("createdby_id") == user.get("id"):
            return True
        
        return False
```

## Performance Considerations

- **Minimal overhead** - Single context lookup + role list check
- **No database queries** - Uses pre-loaded user data from context
- **Cached roles** - User roles typically loaded once per request
- **Scales well** - O(1) per user, scales linearly with role count (typically 1-5 roles)

## Testing

### Unit Test Example

```python
import pytest
from strawberry.permission import BasePermission
from .rbac_simple import AnyRole

def test_anyrole_allows_user_with_roles():
    permission = AnyRole()
    
    # Mock info with user that has roles
    mock_info = MagicMock()
    mock_info.context = {
        "user": {
            "id": "user-123",
            "roles": ["editor"]
        }
    }
    
    assert permission.has_permission(None, mock_info) is True

def test_anyrole_denies_user_without_roles():
    permission = AnyRole()
    
    # Mock info with user that has no roles
    mock_info = MagicMock()
    mock_info.context = {
        "user": {
            "id": "user-456",
            "roles": []  # Empty roles
        }
    }
    
    assert permission.has_permission(None, mock_info) is False

def test_anyrole_denies_no_user():
    permission = AnyRole()
    
    # Mock info with no user
    mock_info = MagicMock()
    mock_info.context = {}
    
    assert permission.has_permission(None, mock_info) is False
```

## Future Enhancements

1. **Specific Role Requirements** - Allow specifying required role(s)
   ```python
   permission_classes=[AnyRole(required=["editor", "administrátor"])]
   ```

2. **Role Caching** - Cache role lookups per request
   ```python
   @cache_per_request
   def get_user_roles(info):
       ...
   ```

3. **Role Hierarchy** - Support role inheritance
   ```python
   ROLE_HIERARCHY = {
       "administrátor": ["editor", "viewer"],
       "editor": ["viewer"]
   }
   ```

4. **Group-Based Access** - Combine with RBAC for group permissions
   ```python
   permission_classes=[OnlyForAuthentized, AnyRole, GroupAccess]
   ```

## Comparison: Simple RBAC vs Unified RBAC

| Feature | Simple RBAC | Unified RBAC |
|---------|------------|--------------|
| **Complexity** | Minimal | Advanced |
| **Setup time** | <5 minutes | 1-2 hours |
| **Role requirement** | Any role OK | Specific roles per operation |
| **Creator ownership** | ❌ Not automatic | ✅ Automatic |
| **Group-based control** | ❌ No | ✅ Yes |
| **Best for** | MVP, prototypes | Production systems |
| **Migration path** | → Unified RBAC | (Final system) |
| **File size** | 65 lines | 500+ lines |

## FAQ

**Q: What if a user has no roles but is admin?**  
A: Simple RBAC doesn't distinguish admin status. Use `OnlyForAuthentized` alone if you want no role requirement, or implement a custom permission class.

**Q: Can I combine AnyRole with other permissions?**  
A: Yes! Use multiple classes: `permission_classes=[OnlyForAuthentized, AnyRole, CustomCheck]`. All must pass.

**Q: How do I exclude certain roles?**  
A: Write a custom permission class that checks for role exclusion. SimpleRBAC doesn't support negative conditions.

**Q: Does this check groups or scopes?**  
A: No. Simple RBAC only checks role existence. For group-based access, migrate to Unified RBAC or implement custom logic.

**Q: What happens if roles is None vs empty list?**  
A: Both are denied. No difference in behavior.

## Related Files

- **Implementation**: `src/GraphTypeDefinitions/rbac_simple.py`
- **Usage Example**: `src/GraphTypeDefinitions/AdmissionApplicationGQLModel.py`
- **Advanced RBAC**: `UNIFIED_RBAC_SYSTEM.md` (group-based, creator ownership)
- **Tests**: `tests/test_rbac_simple.py` (when created)

## Migration to Unified RBAC

When your system grows and needs:
- Group-based permissions
- Creator ownership
- Hierarchical access control

**Migration steps:**

1. Install/import `unified_rbac_extensions`
2. Replace `AnyRole` with group-based extensions
3. Update mutations to use new extension types
4. Add `rbacobject_id` to data model (if not present)
5. Test thoroughly - permissions will be more restrictive

See `UNIFIED_RBAC_SYSTEM.md` for details.

## Support & Troubleshooting

**Permission denied but user should have access?**
1. Check user has non-empty `roles` field
2. Verify context contains `user` or `current_user`
3. Check for typos in role names
4. Add logging to `has_permission()` to debug

**How to add debug logging?**
```python
def has_permission(self, source, info, **kwargs) -> bool:
    ctx = getattr(info, "context", None)
    user = ctx.get("user") if isinstance(ctx, dict) else getattr(ctx, "user", None)
    roles = user.get("roles") if isinstance(user, dict) else getattr(user, "roles", None)
    
    print(f"[AnyRole] User: {user}, Roles: {roles}")  # Debug
    
    if roles is None:
        return False
    return len(roles) > 0 if isinstance(roles, (list, tuple)) else bool(roles.strip())
```

---

**Last Updated:** January 2026  
**Maintainer:** Development Team  
**Status:** ✅ Production Ready

