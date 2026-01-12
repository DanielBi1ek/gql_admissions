import os
import typing

from strawberry.permission import BasePermission


class AdmissionsAdminPermission(BasePermission):
    message = "You must have role 'správce' in group 'Přijímací řízení'"

    GROUP_ID = os.getenv("ADMISSIONS_ADMIN_GROUP_ID", "aeb92819-7cc2-47b4-9a3e-e27462254e4d")
    ROLETYPE_ID = os.getenv("ADMISSIONS_ADMIN_ROLETYPE_ID", "90405774-7114-42af-bc43-49aa503ea661")

    def has_permission(self, source: typing.Any, info: typing.Any, **kwargs: typing.Any) -> bool:
        user = info.context.get("user", {}) or {}
        return is_admissions_admin(user)


def is_admissions_admin(user: typing.Any) -> bool:
    roles = user.get("roles", []) or []
    for role in roles:
        group = role.get("group") or {}
        roletype = role.get("roletype") or {}
        group_id = group.get("id")
        roletype_id = roletype.get("id")
        if (
            group_id == AdmissionsAdminPermission.GROUP_ID
            and roletype_id == AdmissionsAdminPermission.ROLETYPE_ID
        ):
            return True
    return False
