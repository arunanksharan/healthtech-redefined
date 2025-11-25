"""
Role-Based Access Control (RBAC) Service

Provides permission evaluation, role management, and access control.
EPIC-021: Security Hardening
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from uuid import UUID
from functools import lru_cache
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from modules.security.models import (
    Role,
    Permission,
    RolePermission,
    UserRole,
    BreakTheGlassAccess,
    RoleType,
    PermissionAction,
    ResourceType,
)


# Predefined healthcare role configurations
HEALTHCARE_ROLES = {
    RoleType.SUPER_ADMIN: {
        "display_name": "Super Administrator",
        "description": "Full platform access across all tenants",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.PRACTITIONER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.ORGANIZATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.ENCOUNTER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.CONDITION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.MEDICATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.PROCEDURE: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.APPOINTMENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.BILLING: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.REPORT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.EXPORT],
            ResourceType.AUDIT_LOG: [PermissionAction.READ, PermissionAction.EXPORT],
            ResourceType.CONFIGURATION: [PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.ADMIN],
            ResourceType.USER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
            ResourceType.ROLE: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE, PermissionAction.ADMIN],
        },
    },
    RoleType.ORG_ADMIN: {
        "display_name": "Organization Administrator",
        "description": "Full access within organization",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.PRACTITIONER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.ORGANIZATION: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.ENCOUNTER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.CONDITION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.MEDICATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.PROCEDURE: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.APPOINTMENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.BILLING: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.REPORT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.EXPORT],
            ResourceType.AUDIT_LOG: [PermissionAction.READ],
            ResourceType.CONFIGURATION: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.USER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.ROLE: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
        },
    },
    RoleType.PHYSICIAN: {
        "display_name": "Physician",
        "description": "Full clinical access for treating patients",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.PRACTITIONER: [PermissionAction.READ],
            ResourceType.ENCOUNTER: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.CONDITION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.MEDICATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.PROCEDURE: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.APPOINTMENT: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.REPORT: [PermissionAction.CREATE, PermissionAction.READ],
        },
    },
    RoleType.NURSE: {
        "display_name": "Nurse",
        "description": "Care team clinical access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.PRACTITIONER: [PermissionAction.READ],
            ResourceType.ENCOUNTER: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.CONDITION: [PermissionAction.READ],
            ResourceType.MEDICATION: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.PROCEDURE: [PermissionAction.READ],
            ResourceType.APPOINTMENT: [PermissionAction.READ],
        },
    },
    RoleType.MEDICAL_ASSISTANT: {
        "display_name": "Medical Assistant",
        "description": "Support clinical documentation",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],
            ResourceType.ENCOUNTER: [PermissionAction.READ],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ],
            ResourceType.APPOINTMENT: [PermissionAction.READ, PermissionAction.UPDATE],
        },
    },
    RoleType.FRONT_DESK: {
        "display_name": "Front Desk Staff",
        "description": "Scheduling and demographics access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.APPOINTMENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE, PermissionAction.DELETE],
            ResourceType.PRACTITIONER: [PermissionAction.READ],
        },
    },
    RoleType.BILLING_SPECIALIST: {
        "display_name": "Billing Specialist",
        "description": "Financial and billing access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],
            ResourceType.ENCOUNTER: [PermissionAction.READ],
            ResourceType.BILLING: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.REPORT: [PermissionAction.READ, PermissionAction.EXPORT],
        },
    },
    RoleType.LAB_TECHNICIAN: {
        "display_name": "Lab Technician",
        "description": "Laboratory results access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],
            ResourceType.OBSERVATION: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
        },
    },
    RoleType.PHARMACIST: {
        "display_name": "Pharmacist",
        "description": "Medication management access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],
            ResourceType.MEDICATION: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.CONDITION: [PermissionAction.READ],
        },
    },
    RoleType.CARE_COORDINATOR: {
        "display_name": "Care Coordinator",
        "description": "Care coordination and population health",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.ENCOUNTER: [PermissionAction.READ],
            ResourceType.CONDITION: [PermissionAction.READ],
            ResourceType.APPOINTMENT: [PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE],
            ResourceType.REPORT: [PermissionAction.READ],
        },
    },
    RoleType.PATIENT_PORTAL: {
        "display_name": "Patient Portal User",
        "description": "Patient self-service access",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],  # Own data only
            ResourceType.APPOINTMENT: [PermissionAction.CREATE, PermissionAction.READ],
            ResourceType.OBSERVATION: [PermissionAction.READ],
            ResourceType.MEDICATION: [PermissionAction.READ],
        },
    },
    RoleType.READ_ONLY: {
        "display_name": "Read Only",
        "description": "View-only access for auditing",
        "permissions": {
            ResourceType.PATIENT: [PermissionAction.READ],
            ResourceType.ENCOUNTER: [PermissionAction.READ],
            ResourceType.OBSERVATION: [PermissionAction.READ],
            ResourceType.CONDITION: [PermissionAction.READ],
            ResourceType.MEDICATION: [PermissionAction.READ],
            ResourceType.APPOINTMENT: [PermissionAction.READ],
        },
    },
}


class RBACService:
    """Role-Based Access Control Service"""

    def __init__(self, db: Session):
        self.db = db
        self._permission_cache: Dict[str, Set[str]] = {}

    # =========================================================================
    # Role Management
    # =========================================================================

    def create_role(
        self,
        tenant_id: Optional[UUID],
        name: str,
        display_name: str,
        created_by: UUID,
        description: Optional[str] = None,
        role_type: RoleType = RoleType.CUSTOM,
        parent_role_id: Optional[UUID] = None,
    ) -> Role:
        """Create a new role"""

        # Verify unique name within tenant
        existing = self.db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.name == name,
        ).first()

        if existing:
            raise ValueError(f"Role '{name}' already exists")

        # Calculate hierarchy level
        hierarchy_level = 0
        if parent_role_id:
            parent = self.db.query(Role).filter(Role.id == parent_role_id).first()
            if parent:
                hierarchy_level = parent.hierarchy_level + 1

        role = Role(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            role_type=role_type,
            is_system_role=False,
            parent_role_id=parent_role_id,
            hierarchy_level=hierarchy_level,
            created_by=created_by,
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def get_role(
        self,
        role_id: UUID,
    ) -> Optional[Role]:
        """Get role by ID"""

        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_role_by_name(
        self,
        tenant_id: UUID,
        name: str,
    ) -> Optional[Role]:
        """Get role by name within tenant"""

        return self.db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.name == name,
        ).first()

    def list_roles(
        self,
        tenant_id: UUID,
        include_system: bool = True,
    ) -> List[Role]:
        """List roles for tenant"""

        query = self.db.query(Role).filter(
            or_(
                Role.tenant_id == tenant_id,
                Role.tenant_id == None,  # System roles
            ),
            Role.is_active == True,
        )

        if not include_system:
            query = query.filter(Role.is_system_role == False)

        return query.order_by(Role.hierarchy_level, Role.name).all()

    def update_role(
        self,
        role_id: UUID,
        **kwargs,
    ) -> Optional[Role]:
        """Update role properties"""

        role = self.get_role(role_id)
        if not role:
            return None

        if role.is_system_role:
            raise ValueError("Cannot modify system roles")

        for key, value in kwargs.items():
            if hasattr(role, key) and key not in ["id", "is_system_role", "created_at"]:
                setattr(role, key, value)

        role.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(role)

        # Clear permission cache
        self._clear_cache()

        return role

    def delete_role(
        self,
        role_id: UUID,
    ) -> bool:
        """Delete a role"""

        role = self.get_role(role_id)
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        # Check for assigned users
        user_count = self.db.query(UserRole).filter(
            UserRole.role_id == role_id,
            UserRole.is_active == True,
        ).count()

        if user_count > 0:
            raise ValueError(f"Cannot delete role with {user_count} assigned users")

        self.db.delete(role)
        self.db.commit()

        self._clear_cache()

        return True

    # =========================================================================
    # Permission Management
    # =========================================================================

    def create_permission(
        self,
        name: str,
        display_name: str,
        resource_type: ResourceType,
        action: PermissionAction,
        scope: Optional[str] = "all",
        description: Optional[str] = None,
        conditions: Optional[Dict] = None,
    ) -> Permission:
        """Create a new permission"""

        permission = Permission(
            name=name,
            display_name=display_name,
            resource_type=resource_type,
            action=action,
            scope=scope,
            description=description,
            conditions=conditions,
        )

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def get_permission(
        self,
        permission_id: UUID,
    ) -> Optional[Permission]:
        """Get permission by ID"""

        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def find_permission(
        self,
        resource_type: ResourceType,
        action: PermissionAction,
        scope: str = "all",
    ) -> Optional[Permission]:
        """Find permission by resource, action, scope"""

        return self.db.query(Permission).filter(
            Permission.resource_type == resource_type,
            Permission.action == action,
            Permission.scope == scope,
        ).first()

    def list_permissions(
        self,
        resource_type: Optional[ResourceType] = None,
    ) -> List[Permission]:
        """List all permissions"""

        query = self.db.query(Permission).filter(Permission.is_active == True)

        if resource_type:
            query = query.filter(Permission.resource_type == resource_type)

        return query.order_by(Permission.resource_type, Permission.action).all()

    def assign_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID,
        granted_by: UUID,
        conditions_override: Optional[Dict] = None,
    ) -> RolePermission:
        """Assign permission to role"""

        # Check if already assigned
        existing = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        ).first()

        if existing:
            raise ValueError("Permission already assigned to role")

        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            is_granted=True,
            conditions_override=conditions_override,
            granted_by=granted_by,
        )

        self.db.add(role_permission)
        self.db.commit()
        self.db.refresh(role_permission)

        self._clear_cache()

        return role_permission

    def revoke_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> bool:
        """Remove permission from role"""

        deleted = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        ).delete()

        self.db.commit()
        self._clear_cache()

        return deleted > 0

    # =========================================================================
    # User-Role Assignment
    # =========================================================================

    def assign_role_to_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
        scope_type: Optional[str] = None,
        scope_id: Optional[UUID] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
    ) -> UserRole:
        """Assign role to user"""

        # Check for existing assignment
        existing = self.db.query(UserRole).filter(
            UserRole.tenant_id == tenant_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.scope_type == scope_type,
            UserRole.scope_id == scope_id,
            UserRole.is_active == True,
        ).first()

        if existing:
            raise ValueError("Role already assigned to user in this scope")

        user_role = UserRole(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            valid_from=valid_from or datetime.utcnow(),
            valid_until=valid_until,
            assigned_by=assigned_by,
        )

        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)

        self._clear_cache()

        return user_role

    def revoke_role_from_user(
        self,
        user_role_id: UUID,
    ) -> bool:
        """Revoke role from user"""

        user_role = self.db.query(UserRole).filter(
            UserRole.id == user_role_id,
        ).first()

        if not user_role:
            return False

        user_role.is_active = False
        self.db.commit()

        self._clear_cache()

        return True

    def get_user_roles(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all roles for user"""

        user_roles = self.db.query(UserRole).filter(
            UserRole.tenant_id == tenant_id,
            UserRole.user_id == user_id,
            UserRole.is_active == True,
        ).all()

        now = datetime.utcnow()
        result = []

        for ur in user_roles:
            # Check validity period
            if ur.valid_from and ur.valid_from > now:
                continue
            if ur.valid_until and ur.valid_until < now:
                continue

            role = ur.role
            result.append({
                "id": str(ur.id),
                "role_id": str(role.id),
                "role_name": role.name,
                "role_display_name": role.display_name,
                "role_type": role.role_type.value,
                "scope_type": ur.scope_type,
                "scope_id": str(ur.scope_id) if ur.scope_id else None,
                "valid_from": ur.valid_from.isoformat() if ur.valid_from else None,
                "valid_until": ur.valid_until.isoformat() if ur.valid_until else None,
            })

        return result

    # =========================================================================
    # Permission Evaluation
    # =========================================================================

    def check_permission(
        self,
        tenant_id: UUID,
        user_id: UUID,
        resource_type: ResourceType,
        action: PermissionAction,
        resource_id: Optional[UUID] = None,
        scope_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Check if user has permission for action on resource"""

        # Get user's effective permissions
        permissions = self._get_effective_permissions(tenant_id, user_id)

        # Build permission key
        permission_key = f"{resource_type.value}:{action.value}"

        # Check direct permission
        if permission_key in permissions:
            return {
                "allowed": True,
                "reason": "Direct permission granted",
                "permission": permission_key,
            }

        # Check for admin permission on resource
        admin_key = f"{resource_type.value}:admin"
        if admin_key in permissions:
            return {
                "allowed": True,
                "reason": "Admin permission on resource",
                "permission": admin_key,
            }

        # Check for super admin
        super_admin_key = f"{ResourceType.CONFIGURATION.value}:admin"
        if super_admin_key in permissions:
            return {
                "allowed": True,
                "reason": "Super admin access",
                "permission": super_admin_key,
            }

        return {
            "allowed": False,
            "reason": "Permission denied",
            "required": permission_key,
        }

    def _get_effective_permissions(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> Set[str]:
        """Get all effective permissions for user (with caching)"""

        cache_key = f"{tenant_id}:{user_id}"

        if cache_key in self._permission_cache:
            return self._permission_cache[cache_key]

        permissions = set()
        now = datetime.utcnow()

        # Get user's active roles
        user_roles = self.db.query(UserRole).filter(
            UserRole.tenant_id == tenant_id,
            UserRole.user_id == user_id,
            UserRole.is_active == True,
        ).all()

        for user_role in user_roles:
            # Check validity period
            if user_role.valid_from and user_role.valid_from > now:
                continue
            if user_role.valid_until and user_role.valid_until < now:
                continue

            # Get role permissions (including inherited)
            role_permissions = self._get_role_permissions(user_role.role_id)
            permissions.update(role_permissions)

        self._permission_cache[cache_key] = permissions

        return permissions

    def _get_role_permissions(
        self,
        role_id: UUID,
        visited: Optional[Set[UUID]] = None,
    ) -> Set[str]:
        """Get all permissions for role (including parent roles)"""

        if visited is None:
            visited = set()

        if role_id in visited:
            return set()

        visited.add(role_id)
        permissions = set()

        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role or not role.is_active:
            return permissions

        # Get direct permissions
        role_permissions = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.is_granted == True,
        ).all()

        for rp in role_permissions:
            perm = rp.permission
            if perm and perm.is_active:
                permissions.add(f"{perm.resource_type.value}:{perm.action.value}")

        # Get inherited permissions from parent
        if role.parent_role_id:
            parent_permissions = self._get_role_permissions(role.parent_role_id, visited)
            permissions.update(parent_permissions)

        return permissions

    def get_user_permissions(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get list of all permissions for user (for UI display)"""

        permissions = self._get_effective_permissions(tenant_id, user_id)

        result = []
        for perm_key in sorted(permissions):
            parts = perm_key.split(":")
            result.append({
                "resource": parts[0],
                "action": parts[1],
                "key": perm_key,
            })

        return result

    # =========================================================================
    # Break the Glass
    # =========================================================================

    def create_break_glass_access(
        self,
        tenant_id: UUID,
        user_id: UUID,
        patient_id: UUID,
        reason: str,
        emergency_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BreakTheGlassAccess:
        """Create emergency break-the-glass access record"""

        access = BreakTheGlassAccess(
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=patient_id,
            reason=reason,
            emergency_type=emergency_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(access)
        self.db.commit()
        self.db.refresh(access)

        return access

    def end_break_glass_access(
        self,
        access_id: UUID,
        resources_accessed: Optional[Dict] = None,
    ) -> bool:
        """End break-the-glass access session"""

        access = self.db.query(BreakTheGlassAccess).filter(
            BreakTheGlassAccess.id == access_id,
        ).first()

        if not access:
            return False

        access.access_ended_at = datetime.utcnow()
        if resources_accessed:
            access.resources_accessed = resources_accessed

        self.db.commit()

        return True

    def review_break_glass_access(
        self,
        access_id: UUID,
        reviewed_by: UUID,
        outcome: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Review break-the-glass access"""

        access = self.db.query(BreakTheGlassAccess).filter(
            BreakTheGlassAccess.id == access_id,
        ).first()

        if not access:
            return False

        access.reviewed_by = reviewed_by
        access.reviewed_at = datetime.utcnow()
        access.review_outcome = outcome
        access.review_notes = notes

        self.db.commit()

        return True

    def get_pending_break_glass_reviews(
        self,
        tenant_id: UUID,
    ) -> List[BreakTheGlassAccess]:
        """Get break-the-glass accesses pending review"""

        return self.db.query(BreakTheGlassAccess).filter(
            BreakTheGlassAccess.tenant_id == tenant_id,
            BreakTheGlassAccess.reviewed_at == None,
        ).order_by(BreakTheGlassAccess.access_started_at.desc()).all()

    def has_break_glass_access(
        self,
        tenant_id: UUID,
        user_id: UUID,
        patient_id: UUID,
    ) -> bool:
        """Check if user has active break-the-glass access to patient"""

        access = self.db.query(BreakTheGlassAccess).filter(
            BreakTheGlassAccess.tenant_id == tenant_id,
            BreakTheGlassAccess.user_id == user_id,
            BreakTheGlassAccess.patient_id == patient_id,
            BreakTheGlassAccess.access_ended_at == None,
        ).first()

        return access is not None

    # =========================================================================
    # System Role Initialization
    # =========================================================================

    def initialize_system_roles(self) -> int:
        """Initialize predefined healthcare roles (run once)"""

        count = 0

        for role_type, config in HEALTHCARE_ROLES.items():
            # Check if role already exists
            existing = self.db.query(Role).filter(
                Role.role_type == role_type,
                Role.is_system_role == True,
            ).first()

            if existing:
                continue

            # Create role
            role = Role(
                tenant_id=None,  # System-wide
                name=role_type.value,
                display_name=config["display_name"],
                description=config["description"],
                role_type=role_type,
                is_system_role=True,
            )

            self.db.add(role)
            self.db.flush()

            # Create and assign permissions
            for resource_type, actions in config["permissions"].items():
                for action in actions:
                    # Find or create permission
                    permission = self.find_permission(resource_type, action)

                    if not permission:
                        permission = Permission(
                            name=f"{resource_type.value}:{action.value}",
                            display_name=f"{action.value.title()} {resource_type.value.title()}",
                            resource_type=resource_type,
                            action=action,
                        )
                        self.db.add(permission)
                        self.db.flush()

                    # Assign to role
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                        is_granted=True,
                    )
                    self.db.add(role_permission)

            count += 1

        self.db.commit()

        return count

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _clear_cache(self) -> None:
        """Clear permission cache"""
        self._permission_cache.clear()

    def clear_user_cache(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        """Clear cache for specific user"""
        cache_key = f"{tenant_id}:{user_id}"
        self._permission_cache.pop(cache_key, None)
