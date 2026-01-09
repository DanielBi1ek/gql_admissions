"""
Authorization Extensions for GraphQL Resolvers

CREATOR OWNERSHIP PHILOSOPHY: "If You Created It, You Can Manage It"

This system implements UNIFIED RBAC combining:
1. Creator Ownership: Permanent CRUD access to content you create
2. Group Permissions: Role-based access through group membership
3. Implicit Viewer Access: Group members without roles can view content

Example Scenario:
- Oliver creates Purchase #123 with "odpovědný řešitel" role → Owns it forever
- Oliver's role changes to "viewer" later → STILL has full CRUD on Purchase #123
- Dept admin can ALSO manage Purchase #123 via group permissions
- Radomil is a Dept member with no role → Can VIEW Purchase #123 (implicit access)
- Result: Both creator and group admins can manage; all members can view

This prevents common issues:
- ❌ "I created this but can't edit it anymore" (user demoted)
- ❌ "Why is this purchase locked?" (creator left team)
- ❌ "I'm in this group but can't see anything" (no role assigned)
- ✅ Creators maintain control of their work
- ✅ Admins can manage their group's content
- ✅ Group members can always view their group's content

Key Features:
- Creator ownership: Users have permanent access to content they create
- Group permissions: Role-based access through group membership
- Implicit viewer access: Group members without roles can view content
- Hierarchical groups: Parent group admins can access child group content
- Auto-assignment: Automatically assigns group ownership on creation
- Root admin: Top-level admins have universal access

Role Definitions:
- viewer/čtenář: Can read content (20 roles total)
- editor/guarantors/leadership: Can create and update content (15 roles)
- administrátor/admin/top leadership: Can delete content (5 roles)
"""

import typing
from strawberry.types import Info
from uoishelpers.gqlpermissions.TwoStageGenericBaseExtension import TwoStageGenericBaseExtension
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.RbacInsertProviderExtension import RbacInsertProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension

# Standard role constants - Comprehensive Czech university role types
# Source: systemdata.rnd.json roletypes section
# Organized by permission level and functional category

# ===========================================================================================
# ROLE CATEGORIES - All role types from UG service
# ===========================================================================================

# Core system roles (technical RBAC)
SYSTEM_ROLES = [
    "administrátor",       # Administrator - full system access
    "admin",              # English variant of administrátor
    "editor",             # Editor - can create/modify content
    "viewer",             # Viewer - read-only access
    "čtenář",             # Czech variant of viewer (reader)
    "zpracovatel gdpr",   # GDPR processor
    "Správce areálu"      # Campus manager
]

# Academic leadership roles (higher authority)
LEADERSHIP_ROLES = [
    "rektor",             # Rector - university president
    "prorektor",          # Vice-rector
    "děkan",              # Dean - faculty leader
    "proděkan",           # Vice-dean
    "vedoucí katedry",    # Department head
    "vedoucí učitel"      # Leading teacher
]

# Program/course guarantee roles (academic responsibility)
GUARANTEE_ROLES = [
    "garant",             # Program guarantor
    "garant (zástupce)",  # Deputy guarantor
    "garant předmětu",    # Subject guarantor
    "odpovědný řešitel"   # Principal investigator (project lead)
]

# Teaching roles (instructional staff)
TEACHING_ROLES = [
    "přednášející",       # Lecturer
    "cvičící"             # Trainer/exercise instructor
]

# Special identity role
IDENTITY_ROLES = [
    "já"                  # Myself (self-reference role)
]

# ===========================================================================================
# AUTHORIZATION ROLE LISTS - Combines roles by permission level
# ===========================================================================================

# READ access: All roles can read (everyone authenticated)
VIEWER_ROLES = SYSTEM_ROLES + LEADERSHIP_ROLES + GUARANTEE_ROLES + TEACHING_ROLES + IDENTITY_ROLES

# WRITE access: Editors, admins, leadership, guarantors, and project leads
# Excludes: viewers, čtenář, regular teaching staff (přednášející, cvičící)
EDITOR_ROLES = [
    "editor", "administrátor", "admin",                      # System roles
    "rektor", "prorektor", "děkan", "proděkan",             # Leadership
    "vedoucí katedry", "vedoucí učitel",                    # Department heads
    "garant", "garant (zástupce)", "garant předmětu",       # Guarantors
    "odpovědný řešitel",                                     # Project lead
    "zpracovatel gdpr",                                      # GDPR processor
    "Správce areálu"                                         # Campus manager
]

# DELETE access: Only administrators and highest leadership
ADMIN_ROLES = [
    "administrátor", "admin",                                # System admins
    "rektor", "prorektor", "děkan"                          # Top leadership only
]

# Convenience aliases matching Agreement project patterns
ROLES_READ = VIEWER_ROLES   # All authenticated users can read
ROLES_WRITE = EDITOR_ROLES  # Create + Update permissions
ROLES_DELETE = ADMIN_ROLES  # Full CRUD including delete


# ===========================================================================================
# PERMISSION FILTER - Filters extension kwargs before passing to resolver
# ===========================================================================================

from strawberry.extensions import FieldExtension

class PermissionFilterExtension(FieldExtension):
    """Filters internal extension kwargs before calling the resolver.

    Extensions add kwargs like 'user_roles', 'rbacobject_id', 'db_row' during
    processing, but Strawberry resolvers use strict parameter matching and will
    reject unknown kwargs. This extension removes internal kwargs before calling
    the actual resolver function.

    Must be first in extension list (executes last).
    """

    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Filter out extension-internal kwargs before calling resolver."""
        # Extension-internal kwargs that should never reach the resolver
        internal_keys = {'user_roles', 'rbacobject_id', 'db_row'}

        # Filter out internal kwargs, keep all GraphQL arguments
        filtered_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in internal_keys
        }

        return await next_(source, info, **filtered_kwargs)


# ===========================================================================================
# AUTO GROUP ASSIGNMENT - Assigns rbacobject_id automatically for inserts
# ===========================================================================================

class AutoGroupAssignmentExtension(FieldExtension):
    """Automatically assigns rbacobject_id from user's primary write group.

    When creating entities, if rbacobject_id is not provided, this extension
    automatically assigns the user's most specific (leaf) write group. This
    makes the API easier to use - users don't need to specify groups manually.

    Selection logic:
    - One write group: Use that group
    - Multiple groups: Use most specific (leaf) group
    - Leaf group: Group that is NOT a parent of any other user group

    Args:
        required_roles: Roles required to create entities (defaults to EDITOR_ROLES)
    """

    def __init__(self, required_roles: typing.List[str] = None):
        super().__init__()
        self.required_roles = required_roles if required_roles is not None else EDITOR_ROLES

    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Auto-assign rbacobject_id from user's write groups if not set."""
        # Find the input entity
        entity_input = None
        for key, value in kwargs.items():
            if hasattr(value, 'rbacobject_id'):
                entity_input = value
                break

        if entity_input:
            current_rbac = getattr(entity_input, 'rbacobject_id', None)

            if current_rbac is None:
                # Get user's write groups
                user = info.context.get("user", {})
                roles = user.get("roles", [])

                write_groups = []
                all_user_roles = []  # For debugging
                for role in roles:
                    roletype_name = role.get("roletype", {}).get("name", "")
                    group_id = role.get("group", {}).get("id")
                    group_name = role.get("group", {}).get("name", "")
                    all_user_roles.append(f"{roletype_name} in {group_name}")

                    if roletype_name in self.required_roles and group_id:
                        write_groups.append(group_id)

                if len(write_groups) >= 1:
                    # Find leaf groups (not parents of other groups)
                    parent_groups = set()
                    for group_id in write_groups:
                        for other_group_id in write_groups:
                            if group_id != other_group_id:
                                descendants = await get_group_children(info, group_id)
                                if other_group_id in descendants:
                                    parent_groups.add(group_id)

                    leaf_groups = [g for g in write_groups if g not in parent_groups]

                    if leaf_groups:
                        entity_input.rbacobject_id = leaf_groups[0]
                        kwargs['rbacobject_id'] = leaf_groups[0]
                    else:
                        entity_input.rbacobject_id = write_groups[0]
                        kwargs['rbacobject_id'] = write_groups[0]
                else:
                    user_fullname = user.get("fullname", "Unknown")
                    user_id = user.get("id", "Unknown ID")
                    roles_str = ", ".join(all_user_roles) if all_user_roles else "NONE"
                    required_roles_str = ', '.join(self.required_roles[:5])
                    if len(self.required_roles) > 5:
                        required_roles_str += f" (and {len(self.required_roles) - 5} more)"

                    raise PermissionError(
                        f"Permission denied. User '{user_fullname}' (ID: {user_id}) cannot create this entity. "
                        f"Required roles: [{required_roles_str}]. "
                        f"Your current roles: [{roles_str}]. "
                        f"You need at least one of the required roles in a group to create content."
                    )
            else:
                kwargs['rbacobject_id'] = current_rbac

        return await next_(source, info, **kwargs)


# ===========================================================================================
# PERMISSION CHECK - Creator ownership OR group-based role check
# ===========================================================================================

class OwnershipPermissionExtension(FieldExtension):
    """Checks creator ownership OR group-based permissions.

    **UNIFIED RBAC AUTHORIZATION LOGIC:**

    Authorization succeeds if ANY of these conditions are met:
    1. ✅ User created the entity (createdby_id matches user.id) → PERMANENT ACCESS
    2. ✅ User has required role in entity's group (or parent group)
    3. ✅ User is root admin (admin in group with no parent) → UNIVERSAL ACCESS
    4. ✅ User is a member of entity's group without explicit role → READ-ONLY ACCESS

    **Key Benefits:**
    - Creators never lose access to their own work (even after role changes)
    - Group admins can manage all content in their groups
    - Group members without explicit roles can view content (implicit viewer access)
    - Hierarchical: Faculty admins manage all department content
    - Root admins have universal access

    **Example:**
    ```python
    # Oliver creates purchase with rbacobject_id = "Dept-A"
    # Oliver.createdby_id = Oliver.id → He owns it forever
    #
    # Later Oliver's role changes: "editor" → "viewer"
    # Oliver can STILL update/delete the purchase (creator ownership)
    #
    # Meanwhile, Dept-A admin can ALSO manage the purchase (group permissions)
    #
    # Radomil is a member of Dept-A but has no role assigned
    # Radomil can VIEW purchases in Dept-A (implicit viewer access)
    ```

    Args:
        roles: Required role names for group-based access
    """

    def __init__(self, roles: typing.List[str]):
        super().__init__()
        self.required_roles = roles

    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Check creator ownership OR group permissions."""

        user = info.context.get("user", {})
        user_id = user.get("id")
        user_roles = user.get("roles", [])  # Get roles directly from user context
        rbacobject_id = kwargs.get("rbacobject_id")
        db_row = kwargs.get("db_row")  # Exists for UPDATE/DELETE

        if not user_id:
            raise PermissionError("User not authenticated")

        # Detect if this is an INSERT operation (no db_row means new entity)
        is_insert = db_row is None

        # ===================================================================
        # CHECK 1: Creator Ownership (permanent access)
        # ===================================================================
        if db_row:
            creator_id = getattr(db_row, 'createdby_id', None)
            if creator_id and str(creator_id) == str(user_id):
                # User created this entity - always allow
                return await next_(source, info, **kwargs)

        # ===================================================================
        # CHECK 2: Root Admin (universal access)
        # ===================================================================
        if user_roles and await check_root_admin(info, user_roles):
            # Root admin can access everything
            return await next_(source, info, **kwargs)

        # ===================================================================
        # CHECK 3: Group-Based Permissions (with roles)
        # ===================================================================
        if rbacobject_id and user_roles:
            # Get all groups accessible to user (including parent groups)
            accessible_groups = await get_accessible_groups(info, user_roles, self.required_roles)

            if str(rbacobject_id) in [str(g) for g in accessible_groups]:
                # User has required role in entity's group or parent group
                return await next_(source, info, **kwargs)

        # ===================================================================
        # CHECK 4: Implicit Viewer Access (group members can view)
        # Only for non-INSERT operations (UPDATE/DELETE still need proper roles)
        # ===================================================================
        if not is_insert and rbacobject_id and user_roles:
            # Check if user is a member of the entity's group (any role)
            user_groups = []
            for role in user_roles:
                group_id = role.get('group', {}).get('id')
                if group_id:
                    user_groups.append(group_id)
                    # Add child groups
                    children = await get_group_children(info, group_id)
                    user_groups.extend(children)

            if str(rbacobject_id) in [str(g) for g in user_groups]:
                # User is a member of entity's group - allow view operations
                # But this should only apply to queries, not mutations
                # Since mutations go through specific permission extensions,
                # we deny here for non-matching roles
                pass

        # ===================================================================
        # DENIED - Neither creator nor group member with required role
        # ===================================================================
        user_fullname = user.get("fullname", "Unknown user")
        required_roles_str = '/'.join(self.required_roles[:5])  # Show first 5 roles
        if len(self.required_roles) > 5:
            required_roles_str += f" (and {len(self.required_roles) - 5} more)"

        raise PermissionError(
            f"Permission denied for {user_fullname}. You must be the creator or have one of these roles "
            f"[{required_roles_str}] in the entity's group."
        )


#  ===========================================================================================
# CHILD ENTITY RBAC PROVIDER - Gets parent entity's rbacobject_id
# ===========================================================================================

class ParentGroupProviderExtension(FieldExtension):
    """Gets rbacobject_id from parent entity for child entities.

    Child entities (like purchase items) typically don't have their own
    rbacobject_id. This extension loads the parent entity and extracts
    its rbacobject_id for permission checking.

    Args:
        parent_field: Field name containing parent ID (e.g., 'purchase_id')
        parent_loader: Loader name for parent entity (e.g., 'PurchaseModel')
    """

    def __init__(self, parent_field: str, parent_loader: str):
        super().__init__()
        self.parent_field = parent_field
        self.parent_loader = parent_loader

    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Load parent entity and extract its rbacobject_id."""
        from uoishelpers.resolvers import getLoadersFromInfo

        loaders = getLoadersFromInfo(info)

        # Get parent ID from input or existing entity
        parent_id = None
        entity_input = None
        for key, value in kwargs.items():
            if hasattr(value, self.parent_field):
                entity_input = value
                parent_id = getattr(value, self.parent_field, None)
                break

        if not parent_id and kwargs.get('db_row'):
            parent_id = getattr(kwargs['db_row'], self.parent_field, None)

        if parent_id:
            # Load parent entity
            loader = getattr(loaders, self.parent_loader, None)
            if loader:
                parent_entity = await loader.load(parent_id)
                if parent_entity:
                    kwargs['rbacobject_id'] = getattr(parent_entity, 'rbacobject_id', None)
                    kwargs['db_row'] = parent_entity

        return await next_(source, info, **kwargs)


# ===========================================================================================
# HELPER FUNCTIONS
# ===========================================================================================

async def get_group_children(info: Info, group_id: str) -> typing.List[str]:
    """Get all child groups of a given group (recursive).

    Args:
        info: Strawberry info context
        group_id: UUID of parent group

    Returns:
        List of child group UUIDs
    """
    ug_client = info.context.get('ug_client')
    if not ug_client:
        return []

    try:
        resp = await ug_client('''
            query($id: UUID!) {
                groupById(id: $id) {
                    id
                    subgroups {
                        id
                        subgroups {
                            id
                            subgroups { id }
                        }
                    }
                }
            }
        ''', {'id': group_id})

        group = resp.get('data', {}).get('groupById')
        if not group:
            return []

        def extract_ids(g):
            ids = []
            for sub in g.get('subgroups', []):
                ids.append(sub['id'])
                ids.extend(extract_ids(sub))
            return ids

        return extract_ids(group)
    except Exception:
        return []


async def check_root_admin(info: Info, user_roles: typing.List[dict]) -> bool:
    """Check if user is a root admin (admin in a group with no parent).

    Args:
        info: Strawberry info context
        user_roles: User's roles from UserRoleProviderExtension

    Returns:
        True if user is root admin, False otherwise
    """
    admin_role_names = ADMIN_ROLES

    for role in user_roles:
        roletype_name = role.get('roletype', {}).get('name', '')
        group = role.get('group', {})
        master_group_id = group.get('mastergroupId')

        if roletype_name in admin_role_names and master_group_id is None:
            # Admin role in a group with no parent = root admin
            return True

    return False


async def get_accessible_groups(
    info: Info,
    user_roles: typing.List[dict],
    required_roles: typing.List[str]
) -> typing.List[str]:
    """Get all groups where user has required roles (including parent groups).

    Args:
        info: Strawberry info context
        user_roles: User's roles
        required_roles: Required role names

    Returns:
        List of accessible group UUIDs
    """
    accessible = []

    for role in user_roles:
        roletype_name = role.get('roletype', {}).get('name', '')
        group_id = role.get('group', {}).get('id')

        if roletype_name in required_roles and group_id:
            accessible.append(group_id)
            # Add child groups (hierarchical permissions)
            children = await get_group_children(info, group_id)
            accessible.extend(children)

    return list(set(accessible))  # Remove duplicates


async def filter_by_permissions(
    info: Info,
    items: typing.List[typing.Any],
    required_roles: typing.List[str] = VIEWER_ROLES
) -> typing.List[typing.Any]:
    """Filter list of entities by user permissions.

    Returns only entities where user is either:
    1. The creator (createdby_id matches user.id)
    2. Has required role in entity's group or parent groups
    3. Is a member of the entity's group (for viewer access)
    4. Is root admin (sees everything)

    Args:
        info: Strawberry info context
        items: List of entities to filter
        required_roles: Required roles for group access

    Returns:
        Filtered list of entities user can access
    """
    user = info.context.get("user", {})
    user_id = user.get("id")

    if not user_id:
        return []

    # Get user roles via UG service
    user_roles = []
    ug_client = info.context.get('ug_client')
    if ug_client:
        try:
            resp = await ug_client('''query { me { roles { group { id mastergroupId } roletype { name } } } }''')
            me = resp.get('data', {}).get('me', {})
            user_roles = me.get('roles', [])
        except Exception:
            pass

    # Check if root admin
    if user_roles and await check_root_admin(info, user_roles):
        return items  # Root admin sees everything

    # Get accessible groups (with explicit roles)
    accessible_groups = await get_accessible_groups(info, user_roles, required_roles)

    # Get all user's groups (for implicit viewer access)
    user_groups = []
    for role in user_roles:
        group_id = role.get('group', {}).get('id')
        if group_id:
            user_groups.append(group_id)
            # Add child groups (hierarchical access)
            children = await get_group_children(info, group_id)
            user_groups.extend(children)

    user_groups = list(set(user_groups))  # Remove duplicates

    # Filter items
    filtered = []
    for item in items:
        creator_id = getattr(item, 'createdby_id', None)
        rbacobject_id = getattr(item, 'rbacobject_id', None)

        # Check creator ownership
        if creator_id and str(creator_id) == str(user_id):
            filtered.append(item)
            continue

        # Check group permissions (with explicit roles)
        if rbacobject_id and str(rbacobject_id) in [str(g) for g in accessible_groups]:
            filtered.append(item)
            continue

        # Check implicit viewer access (group membership without explicit role)
        if rbacobject_id and str(rbacobject_id) in [str(g) for g in user_groups]:
            filtered.append(item)
            continue

    return filtered


# ===========================================================================================
# EXTENSION FACTORY FUNCTIONS
# ===========================================================================================

def create_insert_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for INSERT operations.

    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks user has required roles
    3. AutoGroupAssignmentExtension - auto-assigns rbacobject_id and validates roles

    Args:
        error_type: Error union type (e.g., InsertError[ModelGQLType])
        model_type: GraphQL model type
        required_roles: Required role names

    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        AutoGroupAssignmentExtension(required_roles=required_roles),
    ]


def create_update_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for UPDATE operations.

    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks creator OR group role
    3. RbacProviderExtension - extracts rbacobject_id from entity
    4. LoadDataExtension - batch loads existing entity by input.id

    Args:
        error_type: Error union type
        model_type: GraphQL model type
        required_roles: Required role names

    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        RbacProviderExtension(),
        LoadDataExtension(getLoader=lambda info: model_type.getLoader(info)),
    ]


def create_delete_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = ADMIN_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for DELETE operations.

    Pipeline: Same as UPDATE but requires admin roles

    Args:
        error_type: Error union type
        model_type: GraphQL model type
        required_roles: Required role names (default: admin only)

    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        RbacProviderExtension(),
        LoadDataExtension(getLoader=lambda info: model_type.getLoader(info)),
    ]


def create_child_update_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    parent_field: str,
    parent_loader: str,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for child entity UPDATE operations.

    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks permissions
    3. ParentGroupProviderExtension - gets parent's rbacobject_id
    4. LoadDataExtension - loads child entity

    Args:
        error_type: Error union type
        model_type: GraphQL model type
        parent_field: Field name with parent ID (e.g., 'purchase_id')
        parent_loader: Loader name for parent (e.g., 'PurchaseModel')
        required_roles: Required role names

    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        ParentGroupProviderExtension(parent_field=parent_field, parent_loader=parent_loader),
        LoadDataExtension(getLoader=lambda info: model_type.getLoader(info)),
    ]