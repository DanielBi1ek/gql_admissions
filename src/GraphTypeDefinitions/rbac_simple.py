import typing

import strawberry
from strawberry.permission import BasePermission


class AnyRole(BasePermission):
    """Simple RBAC permission: allow only users that have any role assigned.

    Checks the info.context for a user object/dict with roles.
    A user with no roles or an empty roles list is denied mutation access.

    Users with at least one role (editor, administrátor, viewer, etc.) are allowed.
    """

    message = "User must have at least one role to perform this action"

    def has_permission(self, source: typing.Any, info: strawberry.types.Info, **kwargs) -> bool:
        try:
            # Get context from info
            ctx = getattr(info, "context", None)
            if ctx is None:
                return False

            # Extract user from context
            user = None
            if isinstance(ctx, dict):
                # Context is dict-like (common in tests/direct calls)
                user = ctx.get("user") or ctx.get("current_user")
            else:
                # Context is object-like
                user = getattr(ctx, "user", None) or getattr(ctx, "current_user", None)

            if not user:
                return False

            # Extract roles from user object
            roles = None
            if isinstance(user, dict):
                # User is a dict
                roles = user.get("roles")
            else:
                # User is an object
                roles = getattr(user, "roles", None)

            # Check if roles exist and are not empty
            if roles is None:
                return False

            # Handle string role (single role)
            if isinstance(roles, str):
                return bool(roles.strip())

            # Handle list/tuple of roles
            if isinstance(roles, (list, tuple)):
                return len(roles) > 0

            # Handle other iterables
            try:
                return len(roles) > 0
            except TypeError:
                # Not iterable, check truthiness
                return bool(roles)

        except Exception as e:
            # Log or handle error silently
            return False
