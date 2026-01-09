"""
User Role and Permission Query Endpoints

Allows users to query:
- Their current role level
- Whether they're an admin, editor, or viewer
- What permissions they have
"""

import typing
import strawberry

from uoishelpers.resolvers import getUserFromInfo
from .rbac_db_level import RBACQueryHelper, get_user_info_for_rbac


@strawberry.type(description="User role and permissions information")
class UserRoleInfo:
    """Current user's role and permissions."""

    user_id: str = strawberry.field(description="Current user ID")
    user_name: typing.Optional[str] = strawberry.field(description="Current user name")
    role_level: str = strawberry.field(
        description="User's role level: 'admin', 'editor', 'viewer', or 'none'"
    )
    is_admin: bool = strawberry.field(description="Is user an administrator?")
    is_editor: bool = strawberry.field(description="Is user an editor?")
    is_viewer: bool = strawberry.field(description="Is user a viewer?")
    has_role: bool = strawberry.field(description="Does user have any role?")

    can_create_applications: bool = strawberry.field(
        description="Can user create admission applications?"
    )
    can_update_own_applications: bool = strawberry.field(
        description="Can user update their own applications?"
    )
    can_delete_own_applications: bool = strawberry.field(
        description="Can user delete their own applications?"
    )
    can_manage_exams: bool = strawberry.field(
        description="Can user create/update/delete exams? (Admin only)"
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
        user, rbac = await get_user_info_for_rbac(info)

        if not user:
            return None

        return UserRoleInfo(
            user_id=user.get("id", "unknown"),
            user_name=user.get("name") or user.get("firstname") or "Unknown User",
            role_level=rbac.role,
            is_admin=rbac.is_admin(),
            is_editor=rbac.is_editor(),
            is_viewer=rbac.is_viewer(),
            has_role=rbac.has_role(),
            can_create_applications=rbac.is_editor() or rbac.is_admin(),
            can_update_own_applications=rbac.is_editor() or rbac.is_admin(),
            can_delete_own_applications=rbac.is_editor() or rbac.is_admin(),
            can_manage_exams=rbac.is_admin(),
        )

