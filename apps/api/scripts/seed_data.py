"""
Database seeding script for initial system setup.

Creates initial data for development and testing environments including
sysadmin user, sample clients, and permission scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from datetime import datetime

from database import get_async_session
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.audit import AuditLog
from models.client import Client
from models.permission import AgentName, UserAgentPermission
from models.user import User, UserRole

# Import factories
sys.path.append(str(Path(__file__).parent.parent / "tests"))
from factories import (
    AuditLogFactory,
    ClientFactory,
    UserAgentPermissionFactory,
    UserFactory,
)


class DatabaseSeeder:
    """Database seeding utility for initial data creation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_initial_users(self) -> dict:
        """Create initial system users."""
        print("🔧 Creating initial system users...")

        users = {}

        # Create sysadmin user
        sysadmin = UserFactory.create_sysadmin(
            email="sysadmin@iam-dashboard.local", password="AdminPass@2025"
        )
        self.session.add(sysadmin)
        users["sysadmin"] = sysadmin
        print(f"  ✅ Created sysadmin: {sysadmin.email}")

        # Create admin user
        admin = UserFactory.create_admin(
            email="admin@iam-dashboard.local", password="AdminUser@2025"
        )
        self.session.add(admin)
        users["admin"] = admin
        print(f"  ✅ Created admin: {admin.email}")

        # Create regular users for testing
        regular_users = UserFactory.create_multiple_users(
            count=5,
            role_distribution={
                UserRole.USER: 1.0  # All regular users
            },
        )

        for i, user in enumerate(regular_users):
            user.email = f"user{i + 1}@iam-dashboard.local"
            user.password_hash = UserFactory.get_default_password_hash("UserPass@2025")
            self.session.add(user)
            users[f"user{i + 1}"] = user
            print(f"  ✅ Created user: {user.email}")

        await self.session.commit()
        print(f"  📊 Total users created: {len(users)}")
        return users

    async def seed_sample_clients(self, users: dict) -> list[Client]:
        """Create sample clients for testing."""
        print("👥 Creating sample clients...")

        clients = []

        # Create clients using different user creators
        admin_id = users["admin"].id
        user1_id = users["user1"].id
        user2_id = users["user2"].id

        # Admin creates some clients
        admin_clients = ClientFactory.create_client_batch(
            count=10,
            created_by=admin_id,
            age_distribution={
                "young": 0.3,  # 30% young adults
                "middle": 0.5,  # 50% middle-aged
                "senior": 0.2,  # 20% seniors
            },
        )

        # User1 creates some clients
        user1_clients = ClientFactory.create_clients_for_user(user_id=user1_id, count=5)

        # User2 creates some clients
        user2_clients = ClientFactory.create_clients_for_user(user_id=user2_id, count=3)

        all_clients = admin_clients + user1_clients + user2_clients

        for client in all_clients:
            self.session.add(client)
            clients.append(client)

        await self.session.commit()
        print(f"  📊 Total clients created: {len(clients)}")
        return clients

    async def seed_permissions(self, users: dict) -> list[UserAgentPermission]:
        """Create permission scenarios for testing."""
        print("🔐 Creating permission scenarios...")

        permissions = []
        admin_id = users["admin"].id

        # Give admin full access to all agents
        admin_permissions = (
            UserAgentPermissionFactory.create_agent_permissions_for_user(
                user_id=admin_id,
                granted_by=users["sysadmin"].id,
                permission_type="full",
            )
        )
        permissions.extend(admin_permissions)

        # Give user1 read/write access to client management and reports
        user1_permissions = [
            UserAgentPermissionFactory.create_full_access_permission(
                user_id=users["user1"].id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                granted_by=admin_id,
            ),
            UserAgentPermissionFactory.create_read_write_permission(
                user_id=users["user1"].id,
                agent_name=AgentName.REPORTS_ANALYSIS,
                granted_by=admin_id,
            ),
            UserAgentPermissionFactory.create_read_only_permission(
                user_id=users["user1"].id,
                agent_name=AgentName.PDF_PROCESSING,
                granted_by=admin_id,
            ),
        ]
        permissions.extend(user1_permissions)

        # Give user2 limited access
        user2_permissions = [
            UserAgentPermissionFactory.create_read_only_permission(
                user_id=users["user2"].id,
                agent_name=AgentName.CLIENT_MANAGEMENT,
                granted_by=admin_id,
            ),
            UserAgentPermissionFactory.create_read_only_permission(
                user_id=users["user2"].id,
                agent_name=AgentName.PDF_PROCESSING,
                granted_by=admin_id,
            ),
        ]
        permissions.extend(user2_permissions)

        # Create some expired permissions for testing
        expired_permission = UserAgentPermissionFactory.create_expired_permission(
            user_id=users["user3"].id,
            agent_name=AgentName.AUDIO_RECORDING,
            granted_by=admin_id,
            days_expired=5,
        )
        permissions.append(expired_permission)

        for permission in permissions:
            self.session.add(permission)

        await self.session.commit()
        print(f"  📊 Total permissions created: {len(permissions)}")
        return permissions

    async def seed_audit_logs(
        self, users: dict, clients: list[Client]
    ) -> list[AuditLog]:
        """Create sample audit logs for testing."""
        print("📜 Creating audit logs...")

        audit_logs = []

        # Create user creation audit logs
        for user in users.values():
            if user.role != UserRole.SYSADMIN:  # Don't audit sysadmin creation
                audit_log = AuditLogFactory.create_user_creation_audit(
                    actor_id=users["sysadmin"].id,
                    user_id=user.id,
                    user_email=user.email,
                    user_role=user.role.value,
                )
                audit_logs.append(audit_log)

        # Create client creation audit logs
        for client in clients[:5]:  # Just first 5 to avoid too many logs
            audit_log = AuditLogFactory.create_client_creation_audit(
                actor_id=client.created_by,
                client_id=client.id,
                client_name=client.name,
                client_cpf=client.cpf,
            )
            audit_logs.append(audit_log)

        # Create some login/logout sessions
        user_session_logs = AuditLogFactory.create_audit_trail_for_user_session(
            user_id=users["admin"].id, session_duration_hours=3, actions_count=10
        )
        audit_logs.extend(user_session_logs)

        # Create security audit logs
        security_logs = AuditLogFactory.create_security_audit_logs()
        audit_logs.extend(security_logs)

        for audit_log in audit_logs:
            self.session.add(audit_log)

        await self.session.commit()
        print(f"  📊 Total audit logs created: {len(audit_logs)}")
        return audit_logs

    async def verify_seeded_data(self) -> dict:
        """Verify that seeded data was created successfully."""
        print("✅ Verifying seeded data...")

        # Count users
        user_count = await self.session.scalar(select(func.count(User.id)))

        # Count clients
        client_count = await self.session.scalar(select(func.count(Client.id)))

        # Count permissions
        permission_count = await self.session.scalar(
            select(func.count(UserAgentPermission.id))
        )

        # Count audit logs
        audit_count = await self.session.scalar(select(func.count(AuditLog.id)))

        stats = {
            "users": user_count,
            "clients": client_count,
            "permissions": permission_count,
            "audit_logs": audit_count,
        }

        print(f"  👥 Users: {stats['users']}")
        print(f"  👤 Clients: {stats['clients']}")
        print(f"  🔐 Permissions: {stats['permissions']}")
        print(f"  📜 Audit Logs: {stats['audit_logs']}")

        return stats

    async def run_full_seed(self) -> dict:
        """Run the complete seeding process."""
        print("🌱 Starting database seeding process...")
        start_time = datetime.now()

        try:
            # Seed users first
            users = await self.seed_initial_users()

            # Seed clients
            clients = await self.seed_sample_clients(users)

            # Seed permissions
            await self.seed_permissions(users)

            # Seed audit logs
            await self.seed_audit_logs(users, clients)

            # Verify seeded data
            stats = await self.verify_seeded_data()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(
                f"🎉 Database seeding completed successfully in {duration:.2f} seconds!"
            )
            return stats

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await self.session.rollback()
            raise


async def main():
    """Main seeding function."""
    print("🚀 IAM Dashboard Database Seeder")
    print("=" * 50)

    # Get database session
    async for session in get_async_session():
        seeder = DatabaseSeeder(session)

        try:
            stats = await seeder.run_full_seed()

            print("\n📋 Seed Data Summary:")
            print("-" * 30)
            print(f"Users created: {stats['users']}")
            print(f"Clients created: {stats['clients']}")
            print(f"Permissions created: {stats['permissions']}")
            print(f"Audit logs created: {stats['audit_logs']}")

            print("\n🔑 Default Login Credentials:")
            print("-" * 30)
            print("Sysadmin: sysadmin@iam-dashboard.local / AdminPass@2025")
            print("Admin: admin@iam-dashboard.local / AdminUser@2025")
            print("Users: user1@iam-dashboard.local / UserPass@2025")
            print("       user2@iam-dashboard.local / UserPass@2025")
            print("       ... (user3-user5 with same pattern)")

            print("\n✨ Ready for development and testing!")

        except Exception as e:
            print(f"💥 Seeding failed: {e}")
            return 1

        break  # Exit after first session

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
