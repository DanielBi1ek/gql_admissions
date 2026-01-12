"""
User Role and Permission Query Endpoints

Allows users to query:
- Their current admin status within admissions
- Whether they can perform key admission actions
"""

import typing
import strawberry

from uoishelpers.resolvers import getUserFromInfo
from .admission_permissions import is_admissions_admin


@strawberry.type(description="User role and permissions information")
class UserRoleInfo:
    """Current user's role and permissions."""

    user_id: str = strawberry.field(description="Current user ID")
    user_name: typing.Optional[str] = strawberry.field(description="Current user name")
    role_level: str = strawberry.field(
        description="User's role level: 'admin' or 'none'"
    )
    is_admin: bool = strawberry.field(description="Is user an administrator?")
    is_editor: bool = strawberry.field(description="Is user an editor? (unused)")
    is_viewer: bool = strawberry.field(description="Is user a viewer? (unused)")
    has_role: bool = strawberry.field(description="Does user have any role?")

    can_create_applications: bool = strawberry.field(
        description="Can user submit admission applications?"
    )
    can_update_own_applications: bool = strawberry.field(
        description="Can user withdraw their own applications?"
    )
    can_delete_own_applications: bool = strawberry.field(
        description="Can user delete their own applications? (always false)"
    )
    can_manage_admission_offers: bool = strawberry.field(
        description="Can user create/update/delete admission offers? (Admin only)"
    )


@strawberry.type(description="User queries for role and permissions")
class UserPermissionQuery:
    """
    Queries to check current user's role and permissions.

    Usage:
        query {
            currentUserRole {
                userId
                roleLevel
                isAdmin
                canCreateApplications
            }
        }
    """

    @strawberry.field(description="Get current user's role and permissions")
    async def current_user_role(self, info: strawberry.types.Info) -> typing.Optional[UserRoleInfo]:
        """
        Returns current user's role information and what they can do.

        Returns None if user is not authenticated.
        """
        user = getUserFromInfo(info=info) or {}
        if not user:
            return None
        roles = user.get("roles", []) or []
        is_admin = is_admissions_admin(user)

        has_role = len(roles) > 0
        role_level = "admin" if is_admin else "none"

        return UserRoleInfo(
            user_id=user.get("id", "unknown"),
            user_name=user.get("name") or user.get("firstname") or "Unknown User",
            role_level=role_level,
            is_admin=is_admin,
            is_editor=False,
            is_viewer=False,
            has_role=has_role,
            can_create_applications=True,
            can_update_own_applications=True,
            can_delete_own_applications=False,
            can_manage_admission_offers=is_admin,
        )
