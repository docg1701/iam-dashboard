"""Database seeding utilities for development and testing."""

import asyncio
import sys
from collections import Counter

from sqlmodel import Session, delete, select

from src.core.database import engine
from src.models.audit import AuditLog
from src.models.client import Client
from src.models.user import User
from src.tests.factories import (
    create_complete_audit_trail,
    create_seed_clients,
    create_seed_users,
    create_test_audit_log,
)


async def seed_database() -> None:
    """Seed the database with initial development data."""
    print("🌱 Starting database seeding...")

    with Session(engine) as session:
        # Check if database is already seeded
        existing_users = session.exec(select(User)).all()
        if existing_users:
            print("⚠️  Database already contains users. Skipping seeding.")
            print(f"   Found {len(existing_users)} existing users.")
            return

        try:
            # Create seed users
            print("👥 Creating seed users...")
            seed_users = create_seed_users()

            for user in seed_users:
                session.add(user)

            session.commit()
            print(f"   ✅ Created {len(seed_users)} users")

            # Get admin user for client creation
            admin_user = session.exec(select(User).where(User.email == "admin@company.com")).first()

            if not admin_user:
                print("   ❌ Admin user not found, cannot create clients")
                return

            # Create seed clients
            print("👤 Creating seed clients...")
            seed_clients = create_seed_clients(admin_user.user_id)

            for client in seed_clients:
                session.add(client)

            session.commit()
            print(f"   ✅ Created {len(seed_clients)} clients")

            # Create audit logs for demonstration
            print("📝 Creating audit trail examples...")
            audit_count = 0

            # Create audit logs for each client
            for client in seed_clients:
                audit_logs = create_complete_audit_trail(
                    table_name="agent1_clients", record_id=str(client.client_id)
                )

                for audit_log in audit_logs:
                    audit_log.user_id = admin_user.user_id
                    session.add(audit_log)
                    audit_count += 1

            # Create some user audit logs
            for user in seed_users[:3]:  # First 3 users
                user_audit = create_test_audit_log(
                    table_name="users", record_id=str(user.user_id), user_id=admin_user.user_id
                )
                session.add(user_audit)
                audit_count += 1

            session.commit()
            print(f"   ✅ Created {audit_count} audit log entries")

            print("🎉 Database seeding completed successfully!")
            print_seed_summary(session)

        except Exception as e:
            session.rollback()
            print(f"❌ Error during seeding: {e}")
            raise


def print_seed_summary(session: Session) -> None:
    """Print a summary of seeded data."""
    users = session.exec(select(User)).all()
    clients = session.exec(select(Client)).all()
    audit_logs = session.exec(select(AuditLog)).all()

    print("\n📊 Seed Data Summary:")
    print(f"   Users: {len(users)}")
    print("   Roles breakdown:")

    role_counts = Counter(user.role for user in users)
    for role, count in role_counts.items():
        print(f"     - {role.value}: {count}")

    print(f"   Clients: {len(clients)}")
    print("   Status breakdown:")
    status_counts = Counter(client.status for client in clients)
    for status, count in status_counts.items():
        print(f"     - {status.value}: {count}")

    print(f"   Audit Logs: {len(audit_logs)}")
    print("   Action breakdown:")
    action_counts = Counter(audit.action for audit in audit_logs)
    for action, count in action_counts.items():
        print(f"     - {action.value}: {count}")

    print("\n🔑 Default Login Credentials:")
    print("   Sysadmin: sysadmin@company.com / password")
    print("   Admin:    admin@company.com / password")
    print("   User:     user1@company.com / password")
    print("   User:     user2@company.com / password")
    print("   Note: Admin and Sysadmin accounts have 2FA enabled")


async def clear_database() -> None:
    """Clear all data from the database (for testing)."""
    print("🧹 Clearing database...")

    with Session(engine) as session:
        try:
            # Delete in correct order due to foreign key constraints
            session.connection().execute(delete(AuditLog))
            session.connection().execute(delete(Client))
            session.connection().execute(delete(User))

            session.commit()
            print("   ✅ Database cleared successfully")

        except Exception as e:
            session.rollback()
            print(f"   ❌ Error clearing database: {e}")
            raise


async def reset_database() -> None:
    """Clear and reseed the database."""
    await clear_database()
    await seed_database()


def seed_for_testing() -> tuple[list[User], list[Client], list[AuditLog]]:
    """Create test data and return it (for use in tests)."""
    with Session(engine) as session:
        # Create minimal test data
        test_users = create_seed_users()
        for user in test_users:
            session.add(user)
        session.commit()

        # Get admin for client creation
        admin = next(user for user in test_users if user.email == "admin@company.com")

        test_clients = create_seed_clients(admin.user_id)
        for client in test_clients:
            session.add(client)
        session.commit()

        # Create some audit logs
        test_audit_logs = []
        for client in test_clients[:2]:  # First 2 clients
            audit_logs = create_complete_audit_trail(
                table_name="agent1_clients", record_id=str(client.client_id)
            )
            for audit_log in audit_logs:
                audit_log.user_id = admin.user_id
                session.add(audit_log)
                test_audit_logs.extend(audit_logs)

        session.commit()

        return test_users, test_clients, test_audit_logs


# CLI commands for manual seeding


async def main() -> None:
    """Main CLI interface for seeding operations."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.seed_data [seed|clear|reset]")
        return

    command = sys.argv[1].lower()

    if command == "seed":
        await seed_database()
    elif command == "clear":
        await clear_database()
    elif command == "reset":
        await reset_database()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: seed, clear, reset")


if __name__ == "__main__":
    asyncio.run(main())
