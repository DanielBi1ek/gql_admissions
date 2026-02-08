"""
Centralized RBAC system for all Admission-related GraphQL operations.
This file contains all permission classes, access control logic, and decorators
to eliminate code duplication across admission models.
"""

import os
import typing
import strawberry
import uuid
from sqlalchemy import select
from uoishelpers.gqlpermissions import OnlyForAuthentized
from uoishelpers.resolvers import getUserFromInfo

# =============================================================================
# RBAC OBJECT UTILITIES
# =============================================================================

def create_rbac_object_id() -> uuid.UUID:
    """Create a new RBAC object ID for entity ownership tracking"""
    return uuid.uuid4()

async def ensure_rbac_object_id(entity, user_id: uuid.UUID = None):
    """Ensure an entity has a proper rbacobject_id for RBAC functionality"""
    if not hasattr(entity, 'rbacobject_id') or entity.rbacobject_id is None:
        entity.rbacobject_id = create_rbac_object_id()

    # Also ensure user tracking fields are set
    if user_id:
        if not hasattr(entity, 'createdby_id') or entity.createdby_id is None:
            entity.createdby_id = user_id
        if not hasattr(entity, 'changedby_id') or entity.changedby_id is None:
            entity.changedby_id = user_id

# =============================================================================
# GLOBAL ADMISSION PERMISSION CONSTANTS
# =============================================================================

# Base permission for all admission data access
ADMISSION_READ_PERMISSION = [OnlyForAuthentized]

# Admin-level permissions for mutations and admin operations
ADMISSION_ADMIN_PERMISSION = [OnlyForAuthentized]  # Will add specific admin permission class

# User-level permissions for user-specific operations
ADMISSION_USER_PERMISSION = [OnlyForAuthentized]

# =============================================================================
# ADMISSION ADMIN PERMISSION CLASS
# =============================================================================

class AdmissionsAdminPermission:
    """Permission class for admission administrative operations"""
    message = "Only admission administrators can perform this operation"

    def has_permission(self, source, info, **kwargs):
        user = getUserFromInfo(info=info)
        return is_admissions_admin(user)

    def on_unauthorized(*args, **kwargs):
        """Handle unauthorized calls.

        Strawberry (or other middleware) may call this hook either as a bound
        method (self, source, info, ...) or as an unbound function
        (source, info, ...). Accept *args and detect the signature to avoid
        missing-argument errors.
        """
        # Possible arg layouts:
        #  - bound method: (self, source, info, ...)
        #  - unbound call: (source, info, ...)
        #  - no args
        source = None
        info = None
        message = AdmissionsAdminPermission.message

        if len(args) >= 3 and isinstance(args[0], AdmissionsAdminPermission):
            # bound method: args[0]=self, args[1]=source, args[2]=info
            self = args[0]
            source = args[1]
            info = args[2]
            message = getattr(self, 'message', message)
        elif len(args) >= 2:
            # unbound call: args[0]=source, args[1]=info
            source = args[0]
            info = args[1]
        elif len(args) == 1:
            # single arg could be either self or source; try to detect
            if isinstance(args[0], AdmissionsAdminPermission):
                message = getattr(args[0], 'message', message)
            else:
                source = args[0]

        # Raise a PermissionError with the configured message so that GraphQL
        # layers produce an authorization error consistent with earlier behavior.
        raise PermissionError(message)

class AdmissionsUserPermission:
    """Permission class for user-specific admission operations"""
    message = "Only authenticated users can perform this operation on their own data"

    def has_permission(self, source, info, **kwargs):
        user = getUserFromInfo(info=info)
        if not user:
            return False
        return True  # Any authenticated user can perform user-level operations

    def on_unauthorized(*args, **kwargs):
        """Handle unauthorized calls for user operations"""
        source = None
        info = None
        message = AdmissionsUserPermission.message

        if len(args) >= 3 and isinstance(args[0], AdmissionsUserPermission):
            self = args[0]
            source = args[1]
            info = args[2]
            message = getattr(self, 'message', message)
        elif len(args) >= 2:
            source = args[0]
            info = args[1]
        elif len(args) == 1:
            if isinstance(args[0], AdmissionsUserPermission):
                message = getattr(args[0], 'message', message)
            else:
                source = args[0]

        raise PermissionError(message)

class AdmissionsOwnershipPermission:
    """Permission class for operations requiring ownership or admin rights"""
    message = "You can only perform this operation on your own data or if you are an administrator"

    def has_permission(self, source, info, **kwargs):
        user = getUserFromInfo(info=info)
        if not user:
            return False

        # Admins can do anything
        if is_admissions_admin(user):
            return True

        # For user operations, we'll check ownership at the resolver level
        # This base permission just ensures the user is authenticated
        return True

    def on_unauthorized(*args, **kwargs):
        """Handle unauthorized calls for ownership operations"""
        source = None
        info = None
        message = AdmissionsOwnershipPermission.message

        if len(args) >= 3 and isinstance(args[0], AdmissionsOwnershipPermission):
            self = args[0]
            source = args[1]
            info = args[2]
            message = getattr(self, 'message', message)
        elif len(args) >= 2:
            source = args[0]
            info = args[1]
        elif len(args) == 1:
            if isinstance(args[0], AdmissionsOwnershipPermission):
                message = getattr(args[0], 'message', message)
            else:
                source = args[0]

        raise PermissionError(message)

# Update the permission constants to include the new classes
ADMISSION_ADMIN_PERMISSION = [OnlyForAuthentized, AdmissionsAdminPermission]
ADMISSION_USER_PERMISSION = [OnlyForAuthentized, AdmissionsUserPermission]
ADMISSION_OWNERSHIP_PERMISSION = [OnlyForAuthentized, AdmissionsOwnershipPermission]

# =============================================================================
# ADMIN CHECK FUNCTION
# =============================================================================

def is_admissions_admin(user: typing.Dict) -> bool:
    """
    Check if user has admission administrator privileges.

    Args:
        user: User dict from getUserFromInfo()

    Returns:
        True if user is admission admin, False otherwise
    """
    if not user:
        return False

    # Check for admin roles (adjust role names as needed)
    roles = user.get("roles", [])
    admin_role_names = {
        "admin", "administrator", "administrátor", "rektor", "prorektor",
        "admission_admin", "study_office", "admission_officer"
    }

    for role in roles:
        role_type = role.get("roletype", {})
        role_name = role_type.get("name", "").lower()
        if role_name in admin_role_names:
            return True

    return False

# =============================================================================
# ACCESS CONTROL MIXINS
# =============================================================================

class AdmissionAccessControlMixin:
    """Reusable access control logic for all admission entities"""

    @staticmethod
    async def check_user_access(info, entity_id, user_field="applicant_user_id"):
        """
        Centralized user access logic for admission entities.

        Args:
            info: GraphQL info object
            entity_id: ID of the entity to check access for
            user_field: Field name that links entity to user

        Returns:
            Tuple of (has_access: bool, error_message: str|None)
        """
        user = getUserFromInfo(info=info) or {}

        # Admins can access everything
        if is_admissions_admin(user):
            return True, None

        user_id = user.get("id")
        if not user_id:
            return False, "User not authenticated"

        return True, None  # For now, authenticated users can access

    @staticmethod
    async def filter_by_user_access(info, query_stmt, user_field="applicant_user_id"):
        """
        Filter query results based on user access rights.

        Args:
            info: GraphQL info object
            query_stmt: SQLAlchemy query statement
            user_field: Field name that links entity to user

        Returns:
            Modified query statement with user-specific filters
        """
        user = getUserFromInfo(info=info) or {}

        # Admins can see everything - no additional filtering
        if is_admissions_admin(user):
            return query_stmt

        user_id = user.get("id")
        if not user_id:
            return query_stmt.where(False)  # No access for unauthenticated users

        # Add user-specific filtering logic here
        # This is a placeholder - actual implementation depends on entity structure
        return query_stmt

# =============================================================================
# PERMISSION DECORATORS
# =============================================================================

def admission_admin_required(description: str = None):
    """Decorator for admin-only operations"""
    def decorator(func):
        # Apply admin permissions
        if hasattr(func, '__annotations__'):
            func = strawberry.field(
                description=description or func.__doc__,
                permission_classes=ADMISSION_ADMIN_PERMISSION
            )(func)
        return func
    return decorator

def admission_read_required(description: str = None):
    """Decorator for read operations requiring authentication"""
    def decorator(func):
        # Apply read permissions
        if hasattr(func, '__annotations__'):
            func = strawberry.field(
                description=description or func.__doc__,
                permission_classes=ADMISSION_READ_PERMISSION
            )(func)
        return func
    return decorator

def admission_user_required(description: str = None):
    """Decorator for user-specific operations"""
    def decorator(func):
        # Apply user permissions
        if hasattr(func, '__annotations__'):
            func = strawberry.field(
                description=description or func.__doc__,
                permission_classes=ADMISSION_USER_PERMISSION
            )(func)
        return func
    return decorator

# =============================================================================
# FIELD PERMISSION HELPERS
# =============================================================================

def admission_field(
    default=strawberry.UNSET,
    description: str = None,
    resolver=None,
    permission_level: str = "read"
):
    """
    Helper function to create strawberry fields with appropriate admission permissions.

    Args:
        default: Default value for the field
        description: Field description
        resolver: Custom resolver function
        permission_level: "read", "admin", or "user"

    Returns:
        strawberry.field with appropriate permissions
    """
    permission_map = {
        "read": ADMISSION_READ_PERMISSION,
        "admin": ADMISSION_ADMIN_PERMISSION,
        "user": ADMISSION_USER_PERMISSION
    }

    permissions = permission_map.get(permission_level, ADMISSION_READ_PERMISSION)

    kwargs = {
        "description": description,
        "permission_classes": permissions
    }

    # Always set default if provided (including None)
    if default is not strawberry.UNSET:
        kwargs["default"] = default
    if resolver is not None:
        kwargs["resolver"] = resolver

    return strawberry.field(**kwargs)

# =============================================================================
# QUERY ACCESS CONTROL HELPERS
# =============================================================================

async def get_admission_entity_by_id(info, entity_class, entity_id):
    """
    Generic function to get admission entity by ID with proper access control.

    Args:
        info: GraphQL info object
        entity_class: The GQL model class
        entity_id: ID of the entity to retrieve

    Returns:
        Entity instance or None if no access/not found
    """
    user = getUserFromInfo(info=info) or {}

    # Admins can access any entity
    if is_admissions_admin(user):
        return await entity_class.load_with_loader(info=info, id=entity_id)

    # For regular users, implement user-specific filtering
    # This is a simplified version - actual implementation depends on entity relationships
    user_id = user.get("id")
    if not user_id:
        return None

    # Try to load the entity and check access
    entity = await entity_class.load_with_loader(info=info, id=entity_id)
    if not entity:
        return None

    # Add user-specific access checking logic here
    # For now, allow access to authenticated users
    return entity

async def get_admission_entities_page(
    info, entity_class, where=None, skip=0, limit=10,
    orderby=None, desc=None, offset=None
):
    """
    Generic function to get paginated admission entities with proper access control.

    Args:
        info: GraphQL info object
        entity_class: The GQL model class
        where: Filter conditions
        skip: Number of records to skip
        limit: Maximum records to return
        orderby: Field to order by
        desc: Descending order if True
        offset: Alias for skip

    Returns:
        List of entity instances with appropriate filtering
    """
    from .pagination import resolve_page

    if offset is not None:
        skip = offset

    user = getUserFromInfo(info=info) or {}

    # Admins can see all entities
    if is_admissions_admin(user):
        return await resolve_page(
            info, entity_class, where, skip, limit, orderby, desc, offset
        )

    # For regular users, add user-specific filtering
    user_id = user.get("id")
    if not user_id:
        return []

    # Add extended filter for user-specific access
    # This is a simplified version - actual implementation depends on entity relationships
    return await resolve_page(
        info, entity_class, where, skip, limit, orderby, desc, offset,
        extendedfilter={"createdby_id": user_id}  # Example filter
    )

# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# Keep existing exports for backward compatibility
__all__ = [
    'AdmissionsAdminPermission',
    'is_admissions_admin',
    'ADMISSION_READ_PERMISSION',
    'ADMISSION_ADMIN_PERMISSION',
    'ADMISSION_USER_PERMISSION',
    'AdmissionAccessControlMixin',
    'admission_admin_required',
    'admission_read_required',
    'admission_user_required',
    'admission_field',
    'get_admission_entity_by_id',
    'get_admission_entities_page'
]
