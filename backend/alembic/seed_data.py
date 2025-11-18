"""
Seed data script for initial database setup
Creates default tenants, roles, permissions, and admin users
"""
import sys
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime

# Add parent directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from shared.database.connection import get_db_session
from shared.database.models import (
    Tenant, User, Role, Permission,
    Organization, Location
)
from shared.security.password import hash_password
from loguru import logger


# Default tenant ID (use consistent UUID for development)
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


def create_default_tenant(db: Session) -> Tenant:
    """Create default tenant for development"""
    logger.info("Creating default tenant...")

    tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()

    if tenant:
        logger.info(f"Tenant already exists: {tenant.name}")
        return tenant

    tenant = Tenant(
        id=DEFAULT_TENANT_ID,
        name="Default Hospital",
        code="DEF001",
        is_active=True,
        database_name="healthtech",
        created_at=datetime.utcnow()
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    logger.info(f"Created tenant: {tenant.name} ({tenant.id})")
    return tenant


def create_permissions(db: Session) -> dict:
    """Create default permissions"""
    logger.info("Creating permissions...")

    permissions_data = [
        # Patient permissions
        ("patient:read", "View patient records", "patient", "read"),
        ("patient:write", "Create and update patient records", "patient", "write"),
        ("patient:delete", "Delete patient records", "patient", "delete"),
        ("patient:merge", "Merge patient records", "patient", "merge"),

        # Practitioner permissions
        ("practitioner:read", "View practitioner records", "practitioner", "read"),
        ("practitioner:write", "Create and update practitioner records", "practitioner", "write"),
        ("practitioner:delete", "Delete practitioner records", "practitioner", "delete"),

        # Appointment permissions
        ("appointment:read", "View appointments", "appointment", "read"),
        ("appointment:write", "Create and update appointments", "appointment", "write"),
        ("appointment:cancel", "Cancel appointments", "appointment", "cancel"),

        # Clinical permissions
        ("encounter:read", "View encounters", "encounter", "read"),
        ("encounter:write", "Create and update encounters", "encounter", "write"),
        ("observation:read", "View observations", "observation", "read"),
        ("observation:write", "Create and update observations", "observation", "write"),
        ("order:read", "View orders", "order", "read"),
        ("order:write", "Create and update orders", "order", "write"),
        ("order:approve", "Approve orders", "order", "approve"),

        # FHIR permissions
        ("fhir:read", "View FHIR resources", "fhir", "read"),
        ("fhir:write", "Create and update FHIR resources", "fhir", "write"),
        ("fhir:delete", "Delete FHIR resources", "fhir", "delete"),

        # Consent permissions
        ("consent:read", "View consents", "consent", "read"),
        ("consent:write", "Create and update consents", "consent", "write"),
        ("consent:revoke", "Revoke consents", "consent", "revoke"),

        # User management permissions
        ("user:read", "View users", "user", "read"),
        ("user:write", "Create and update users", "user", "write"),
        ("user:delete", "Delete users", "user", "delete"),

        # Role management permissions
        ("role:read", "View roles", "role", "read"),
        ("role:write", "Create and update roles", "role", "write"),
        ("role:delete", "Delete roles", "role", "delete"),

        # System permissions
        ("system:admin", "System administrator access", "system", "admin"),
        ("tenant:manage", "Manage tenant settings", "tenant", "manage"),
        ("audit:read", "View audit logs", "audit", "read"),
    ]

    permissions_map = {}

    for name, description, resource, action in permissions_data:
        perm = db.query(Permission).filter(Permission.name == name).first()

        if not perm:
            perm = Permission(
                name=name,
                description=description,
                resource=resource,
                action=action,
                created_at=datetime.utcnow()
            )
            db.add(perm)
            db.flush()
            logger.info(f"Created permission: {name}")
        else:
            logger.info(f"Permission already exists: {name}")

        permissions_map[name] = perm

    db.commit()
    logger.info(f"Created/verified {len(permissions_map)} permissions")
    return permissions_map


def create_roles(db: Session, tenant_id: UUID, permissions_map: dict) -> dict:
    """Create default roles"""
    logger.info("Creating roles...")

    roles_data = {
        "system_admin": {
            "description": "System administrator with full access",
            "permissions": ["system:admin", "tenant:manage", "audit:read"]
        },
        "tenant_admin": {
            "description": "Tenant administrator",
            "permissions": [
                "user:read", "user:write", "user:delete",
                "role:read", "role:write",
                "patient:read", "patient:write", "patient:delete",
                "practitioner:read", "practitioner:write",
                "appointment:read", "appointment:write", "appointment:cancel",
                "consent:read", "consent:write", "consent:revoke"
            ]
        },
        "doctor": {
            "description": "Doctor with clinical access",
            "permissions": [
                "patient:read", "patient:write",
                "practitioner:read",
                "appointment:read", "appointment:write",
                "encounter:read", "encounter:write",
                "observation:read", "observation:write",
                "order:read", "order:write", "order:approve",
                "fhir:read", "fhir:write",
                "consent:read"
            ]
        },
        "nurse": {
            "description": "Nurse with patient care access",
            "permissions": [
                "patient:read",
                "appointment:read",
                "encounter:read",
                "observation:read", "observation:write",
                "order:read",
                "fhir:read", "fhir:write",
                "consent:read"
            ]
        },
        "receptionist": {
            "description": "Receptionist with scheduling access",
            "permissions": [
                "patient:read", "patient:write",
                "appointment:read", "appointment:write",
                "practitioner:read",
                "consent:read"
            ]
        },
        "patient": {
            "description": "Patient with limited self-service access",
            "permissions": [
                "patient:read",
                "appointment:read",
                "encounter:read",
                "observation:read",
                "consent:read", "consent:write", "consent:revoke"
            ]
        }
    }

    roles_map = {}

    for role_name, role_data in roles_data.items():
        role = db.query(Role).filter(
            Role.name == role_name,
            Role.tenant_id == tenant_id
        ).first()

        if not role:
            role = Role(
                tenant_id=tenant_id,
                name=role_name,
                description=role_data["description"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(role)
            db.flush()

            # Assign permissions
            role_permissions = [
                permissions_map[perm_name]
                for perm_name in role_data["permissions"]
                if perm_name in permissions_map
            ]
            role.permissions = role_permissions

            logger.info(
                f"Created role: {role_name} with {len(role_permissions)} permissions"
            )
        else:
            logger.info(f"Role already exists: {role_name}")

        roles_map[role_name] = role

    db.commit()
    logger.info(f"Created/verified {len(roles_map)} roles")
    return roles_map


def create_admin_user(db: Session, tenant_id: UUID, roles_map: dict) -> User:
    """Create default admin user"""
    logger.info("Creating admin user...")

    admin_email = "admin@healthtech.local"

    user = db.query(User).filter(
        User.email == admin_email,
        User.tenant_id == tenant_id
    ).first()

    if user:
        logger.info(f"Admin user already exists: {admin_email}")
        return user

    # Create admin user
    user = User(
        tenant_id=tenant_id,
        email=admin_email,
        password_hash=hash_password("Admin@123"),  # Change in production!
        first_name="System",
        last_name="Administrator",
        full_name="System Administrator",
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.flush()

    # Assign system_admin role
    if "system_admin" in roles_map:
        user.roles = [roles_map["system_admin"]]

    db.commit()
    db.refresh(user)

    logger.info(f"Created admin user: {admin_email} (password: Admin@123)")
    logger.warning("⚠️  IMPORTANT: Change the admin password immediately in production!")
    return user


def create_default_organization(db: Session, tenant_id: UUID) -> Organization:
    """Create default organization"""
    logger.info("Creating default organization...")

    org = db.query(Organization).filter(
        Organization.tenant_id == tenant_id,
        Organization.name == "Default Hospital"
    ).first()

    if org:
        logger.info(f"Organization already exists: {org.name}")
        return org

    org = Organization(
        tenant_id=tenant_id,
        name="Default Hospital",
        type="prov",
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    logger.info(f"Created organization: {org.name} ({org.id})")
    return org


def create_default_location(db: Session, tenant_id: UUID, org_id: UUID) -> Location:
    """Create default location"""
    logger.info("Creating default location...")

    loc = db.query(Location).filter(
        Location.tenant_id == tenant_id,
        Location.name == "Main Building"
    ).first()

    if loc:
        logger.info(f"Location already exists: {loc.name}")
        return loc

    loc = Location(
        tenant_id=tenant_id,
        organization_id=org_id,
        name="Main Building",
        type="HOSP",
        operational_status="active",
        created_at=datetime.utcnow()
    )

    db.add(loc)
    db.commit()
    db.refresh(loc)

    logger.info(f"Created location: {loc.name} ({loc.id})")
    return loc


def seed_database():
    """Main seed function"""
    logger.info("=" * 60)
    logger.info("Starting database seeding...")
    logger.info("=" * 60)

    db = next(get_db_session())

    try:
        # 1. Create default tenant
        tenant = create_default_tenant(db)

        # 2. Create permissions
        permissions_map = create_permissions(db)

        # 3. Create roles
        roles_map = create_roles(db, tenant.id, permissions_map)

        # 4. Create admin user
        admin_user = create_admin_user(db, tenant.id, roles_map)

        # 5. Create default organization
        org = create_default_organization(db, tenant.id)

        # 6. Create default location
        loc = create_default_location(db, tenant.id, org.id)

        logger.info("=" * 60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Tenant ID: {tenant.id}")
        logger.info(f"Admin Email: {admin_user.email}")
        logger.info(f"Admin Password: Admin@123")
        logger.info(f"Organization ID: {org.id}")
        logger.info(f"Location ID: {loc.id}")
        logger.info("=" * 60)
        logger.warning("⚠️  Change admin password in production!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
