import typing

import strawberry
from strawberry.permission import BasePermission


# Role IDs from systemdata.rnd.json
ADMIN_ROLE_IDS = {
    "ced46aa4-3217-4fc1-b79d-f6be7d21c6b6",  # administrátor
    "b87aed46-dfc3-40f8-ad49-03f4138c7478",  # zpracovatel gdpr
    "ae3f0d74-6159-11ed-b753-0242ac120003",  # rektor
    "ae3f2886-6159-11ed-b753-0242ac120003",  # prorektor
    "ae3f2912-6159-11ed-b753-0242ac120003",  # děkan
    "ae3f2980-6159-11ed-b753-0242ac120003",  # proděkan
}

VIEWER_ROLE_IDS = {
    "ae3f29ee-6159-11ed-b753-0242ac120003",  # vedoucí katedry
    "ae3f2a5c-6159-11ed-b753-0242ac120003",  # vedoucí učitel
    "5f0c247e-931f-11ed-9b95-0242ac110002",  # garant
}

EDITOR_ROLE_IDS = {
    "0eb35718-615b-11ed-b753-0242ac120003",  # studenti (group)
}

# Mapping of role names to IDs for easy lookup
ROLE_NAME_TO_ID = {
    "administrátor": "ced46aa4-3217-4fc1-b79d-f6be7d21c6b6",
    "zpracovatel gdpr": "b87aed46-dfc3-40f8-ad49-03f4138c7478",
    "rektor": "ae3f0d74-6159-11ed-b753-0242ac120003",
    "prorektor": "ae3f2886-6159-11ed-b753-0242ac120003",
    "děkan": "ae3f2912-6159-11ed-b753-0242ac120003",
    "proděkan": "ae3f2980-6159-11ed-b753-0242ac120003",
    "vedoucí katedry": "ae3f29ee-6159-11ed-b753-0242ac120003",
    "vedoucí učitel": "ae3f2a5c-6159-11ed-b753-0242ac120003",
    "garant": "5f0c247e-931f-11ed-9b95-0242ac110002",
    "studenti": "0eb35718-615b-11ed-b753-0242ac120003",
}


def _extract_user_from_context(info: strawberry.types.Info) -> typing.Optional[typing.Dict]:
    """Helper function to extract user from info context."""
    try:
        ctx = getattr(info, "context", None)
        if ctx is None:
            return None

        user = None
        if isinstance(ctx, dict):
            user = ctx.get("user") or ctx.get("current_user")
        else:
            user = getattr(ctx, "user", None) or getattr(ctx, "current_user", None)

        return user
    except Exception:
        return None


def _extract_roles(user: typing.Any) -> typing.Optional[typing.List]:
    """Helper function to extract roles from user object."""
    if user is None:
        return None

    try:
        if isinstance(user, dict):
            roles = user.get("roles")
        else:
            roles = getattr(user, "roles", None)

        if roles is None:
            return None

        # Convert to list if it's a different type
        if isinstance(roles, (list, tuple)):
            return list(roles)
        elif isinstance(roles, str):
            return [roles] if roles.strip() else None
        else:
            try:
                return list(roles)
            except TypeError:
                return [roles] if roles else None
    except Exception:
        return None


def enrich_user_with_roles(user: typing.Dict, systemdata: typing.Optional[typing.Dict] = None) -> typing.Dict:
    """
    Enrich user dictionary with full role objects containing ID fields.

    This function takes a user dict with role names/IDs and ensures roles are
    proper objects with 'id' fields that RBAC checks can use.

    Args:
        user: User dictionary potentially with role data
        systemdata: Optional systemdata dict containing roletypes for lookup

    Returns:
        User dict with enriched roles containing proper ID fields
    """
    if not user or not isinstance(user, dict):
        return user

    roles = user.get("roles", [])
    if not roles:
        return user

    # Build role mapping from systemdata if provided
    role_mapping = {}
    if systemdata and isinstance(systemdata, dict):
        for role_type in systemdata.get("roletypes", []):
            if isinstance(role_type, dict):
                role_id = role_type.get("id")
                role_name = role_type.get("name")
                if role_id and role_name:
                    role_mapping[role_name] = role_id

    # Add built-in role mapping
    role_mapping.update(ROLE_NAME_TO_ID)

    # Convert roles to proper objects with ID fields
    enriched_roles = []
    for role in roles:
        if isinstance(role, dict):
            # Already a dict, ensure it has 'id' field
            if "id" not in role and "name" in role:
                role_name = role.get("name")
                role["id"] = role_mapping.get(role_name, role_mapping.get(role_name.lower()))
            enriched_roles.append(role)
        elif isinstance(role, str):
            # String role name, convert to dict with ID
            role_id = role_mapping.get(role, role_mapping.get(role.lower()))
            if role_id:
                enriched_roles.append({"id": role_id, "name": role})
            else:
                # Keep original if can't map
                enriched_roles.append({"id": role, "name": role})
        else:
            # Object with attributes, wrap it
            role_id = getattr(role, "id", None)
            role_name = getattr(role, "name", str(role))
            enriched_roles.append({"id": role_id, "name": role_name})

    user["roles"] = enriched_roles
    return user


def _get_role_level(user: typing.Any) -> str:
    """
    Determine the role level of a user.
    Returns: 'admin', 'editor', 'viewer', or 'none'
    """
    roles = _extract_roles(user)
    if not roles:
        return 'none'

    # Check if any role ID matches role levels (check admin first, then editor, then viewer)
    for role in roles:
        role_id = None
        if isinstance(role, dict):
            role_id = role.get("id")
        else:
            role_id = getattr(role, "id", None)

        if role_id:
            if role_id in ADMIN_ROLE_IDS:
                return 'admin'
            elif role_id in EDITOR_ROLE_IDS:
                return 'editor'
            elif role_id in VIEWER_ROLE_IDS:
                return 'viewer'

    return 'none'


class RequireRole(BasePermission):
    """Base permission: Users must have a role to access any data (queries or mutations).

    Users without any role are completely blocked from reading or writing.
    """

    message = "You must have a role to access this resource"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            user = _extract_user_from_context(info)
            if not user:
                return False

            roles = _extract_roles(user)
            return roles is not None and len(roles) > 0

        except Exception:
            return False


class AdminOnly(BasePermission):
    """Permission: Only admin users can perform this action.

    Admin roles include:
    - administrátor
    - zpracovatel gdpr (GDPR processor)
    - rektor (Rector)
    - prorektor (Vice-rector)
    - děkan (Dean)
    - proděkan (Vice-dean)
    """

    message = "Only administrators can perform this action"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            user = _extract_user_from_context(info)
            if not user:
                return False

            role_level = _get_role_level(user)
            return role_level == 'admin'

        except Exception:
            return False


class EditorAndAbove(BasePermission):
    """Permission: Only editor and admin users can perform this action.

    Allowed roles:
    - Editors: studenti (Students)
    - Admins: all admin roles

    Viewers cannot perform mutations (read-only).
    """

    message = "You must have editor role or higher to perform this action"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            user = _extract_user_from_context(info)
            if not user:
                return False

            role_level = _get_role_level(user)
            return role_level in ('editor', 'admin')

        except Exception:
            return False


class ViewerAndAbove(BasePermission):
    """Permission: Viewer, editor, and admin users can perform this action.

    All users with any role can access.
    """

    message = "You must have a role to perform this action"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            user = _extract_user_from_context(info)
            if not user:
                return False

            role_level = _get_role_level(user)
            return role_level in ('viewer', 'editor', 'admin')

        except Exception:
            return False


class OwnerOrAdmin(BasePermission):
    """Permission: User can only modify their own entries, or user is admin.

    This permission checks if the user is the creator/owner of the resource
    or is an admin.

    - Viewers: Completely blocked (no mutations allowed)
    - Editors: Permission passes, resolver validates ownership
    - Admins: Permission passes, can modify anything

    Usage: Check if createdby_id matches current user id, or user is admin.
    """

    message = "You can only modify your own entries, or you must be an admin"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            user = _extract_user_from_context(info)
            if not user:
                return False

            role_level = _get_role_level(user)

            # Admins can do anything
            if role_level == 'admin':
                return True

            # Editors can modify (ownership check happens in resolver)
            if role_level == 'editor':
                return True

            # Viewers and users without roles cannot modify
            return False

        except Exception:
            return False
