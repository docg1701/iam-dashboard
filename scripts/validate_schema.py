#!/usr/bin/env python3
"""Database schema validation script.

This script compares SQLAlchemy models with the actual database schema
to ensure they are in sync and validates all foreign key relationships.
"""

import asyncio
import logging
import sys
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app.core.database import async_engine
from app.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Database schema validation utility."""

    def __init__(self):
        """Initialize the schema validator."""
        self.engine = async_engine
        self.errors: list[str] = []
        self.warnings: list[str] = []

    async def validate_schema(self) -> bool:
        """
        Validate complete database schema integrity.
        
        Returns:
            True if schema is valid, False otherwise
        """
        logger.info("Starting database schema validation...")

        async with self.engine.begin() as conn:
            # Get actual database structure
            db_tables = await self._get_database_tables(conn)
            db_columns = await self._get_database_columns(conn)
            db_foreign_keys = await self._get_database_foreign_keys(conn)
            db_indexes = await self._get_database_indexes(conn)

            # Get SQLAlchemy model structure
            model_tables = self._get_model_tables()
            model_columns = self._get_model_columns()
            model_foreign_keys = self._get_model_foreign_keys()

            # Validate table existence
            await self._validate_tables(db_tables, model_tables)

            # Validate column structure
            await self._validate_columns(db_columns, model_columns)

            # Validate foreign key relationships
            await self._validate_foreign_keys(db_foreign_keys, model_foreign_keys)

            # Validate indexes
            await self._validate_indexes(db_indexes)

            # Test CRUD operations
            await self._test_crud_operations(conn)

            # Test CASCADE relationships
            await self._test_cascade_relationships(conn)

        # Report results
        self._report_results()

        return len(self.errors) == 0

    async def _get_database_tables(self, conn) -> set[str]:
        """Get all tables from the database."""
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name != 'alembic_version'
        """))
        return {row[0] for row in result}

    async def _get_database_columns(self, conn) -> dict[str, dict[str, Any]]:
        """Get all columns from the database."""
        result = await conn.execute(text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name != 'alembic_version'
            ORDER BY table_name, ordinal_position
        """))

        columns = {}
        for row in result:
            table_name = row[0]
            if table_name not in columns:
                columns[table_name] = {}
            columns[table_name][row[1]] = {
                'type': row[2],
                'nullable': row[3] == 'YES',
                'default': row[4]
            }
        return columns

    async def _get_database_foreign_keys(self, conn) -> dict[str, list[dict[str, str]]]:
        """Get all foreign key constraints from the database."""
        result = await conn.execute(text("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints rc ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """))

        foreign_keys = {}
        for row in result:
            table_name = row[0]
            if table_name not in foreign_keys:
                foreign_keys[table_name] = []
            foreign_keys[table_name].append({
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3],
                'delete_rule': row[4]
            })
        return foreign_keys

    async def _get_database_indexes(self, conn) -> dict[str, list[str]]:
        """Get all indexes from the database."""
        result = await conn.execute(text("""
            SELECT 
                t.relname AS table_name,
                i.relname AS index_name,
                a.attname AS column_name
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
            AND t.relkind = 'r'
            AND (i.relname LIKE 'idx_%' OR i.relname LIKE 'ix_%')
            ORDER BY t.relname, i.relname
        """))

        indexes = {}
        for row in result:
            table_name = row[0]
            if table_name not in indexes:
                indexes[table_name] = []
            indexes[table_name].append(row[1])
        return indexes

    def _get_model_tables(self) -> set[str]:
        """Get all table names from SQLAlchemy models."""
        return {table.name for table in Base.metadata.tables.values()}

    def _get_model_columns(self) -> dict[str, dict[str, Any]]:
        """Get all columns from SQLAlchemy models."""
        columns = {}
        for table_name, table in Base.metadata.tables.items():
            columns[table_name] = {}
            for column in table.columns:
                columns[table_name][column.name] = {
                    'type': str(column.type.compile(dialect=postgresql.dialect())),
                    'nullable': column.nullable,
                    'default': column.default
                }
        return columns

    def _get_model_foreign_keys(self) -> dict[str, list[dict[str, str]]]:
        """Get all foreign keys from SQLAlchemy models."""
        foreign_keys = {}
        for table_name, table in Base.metadata.tables.items():
            foreign_keys[table_name] = []
            for fk in table.foreign_keys:
                foreign_keys[table_name].append({
                    'column': fk.parent.name,
                    'referenced_table': fk.column.table.name,
                    'referenced_column': fk.column.name
                })
        return foreign_keys

    async def _validate_tables(self, db_tables: set[str], model_tables: set[str]):
        """Validate that all model tables exist in database."""
        missing_tables = model_tables - db_tables
        extra_tables = db_tables - model_tables

        for table in missing_tables:
            self.errors.append(f"Table '{table}' defined in models but missing from database")

        for table in extra_tables:
            self.warnings.append(f"Table '{table}' exists in database but not in models")

        if not missing_tables:
            logger.info(f"✓ All {len(model_tables)} model tables exist in database")

    async def _validate_columns(self, db_columns: dict, model_columns: dict):
        """Validate column structure matches between models and database."""
        for table_name in model_columns:
            if table_name not in db_columns:
                continue

            model_cols = model_columns[table_name]
            db_cols = db_columns[table_name]

            # Check for missing columns
            missing_cols = set(model_cols.keys()) - set(db_cols.keys())
            for col in missing_cols:
                self.errors.append(f"Column '{table_name}.{col}' defined in model but missing from database")

            # Check for extra columns
            extra_cols = set(db_cols.keys()) - set(model_cols.keys())
            for col in extra_cols:
                self.warnings.append(f"Column '{table_name}.{col}' exists in database but not in model")

            # Check column properties for matching columns
            common_cols = set(model_cols.keys()) & set(db_cols.keys())
            for col in common_cols:
                model_col = model_cols[col]
                db_col = db_cols[col]

                # Check nullable property
                if model_col['nullable'] != db_col['nullable']:
                    self.errors.append(
                        f"Column '{table_name}.{col}' nullable mismatch: "
                        f"model={model_col['nullable']}, db={db_col['nullable']}"
                    )

        logger.info("✓ Column structure validation completed")

    async def _validate_foreign_keys(self, db_fks: dict, model_fks: dict):
        """Validate foreign key relationships."""
        for table_name in model_fks:
            if table_name not in db_fks:
                continue

            model_fk_set = {(fk['column'], fk['referenced_table'], fk['referenced_column'])
                           for fk in model_fks[table_name]}
            db_fk_set = {(fk['column'], fk['referenced_table'], fk['referenced_column'])
                        for fk in db_fks[table_name]}

            missing_fks = model_fk_set - db_fk_set
            for fk in missing_fks:
                self.errors.append(
                    f"Foreign key '{table_name}.{fk[0]} -> {fk[1]}.{fk[2]}' "
                    f"defined in model but missing from database"
                )

        logger.info("✓ Foreign key validation completed")

    async def _validate_indexes(self, db_indexes: dict):
        """Validate that required indexes exist."""
        required_indexes = {
            'questionnaire_drafts': ['idx_questionnaire_drafts_client_id', 'idx_questionnaire_drafts_user_id'],
            'documents': ['ix_documents_content_hash'],
            'document_chunks': ['ix_document_chunks_document_id', 'ix_document_chunks_node_id'],
            'agent_executions': ['ix_agent_executions_agent_id', 'ix_agent_executions_status']
        }

        for table_name, expected_indexes in required_indexes.items():
            if table_name not in db_indexes:
                for index in expected_indexes:
                    self.errors.append(f"Required index '{index}' missing from table '{table_name}'")
                continue

            table_indexes = db_indexes[table_name]
            for expected_index in expected_indexes:
                if expected_index not in table_indexes:
                    self.errors.append(f"Required index '{expected_index}' missing from table '{table_name}'")

        logger.info("✓ Index validation completed")

    async def _test_crud_operations(self, conn):
        """Test basic CRUD operations don't cause constraint violations."""
        try:
            # Generate unique identifiers for test
            import random
            unique_username = f"test_user_{random.randint(1000, 9999)}"
            unique_cpf = f"{random.randint(10000000000, 99999999999)}"

            # Test creating a user (prerequisite for other tests)
            user_id = await conn.execute(text("""
                INSERT INTO users (id, username, hashed_password, role, is_active, is_2fa_enabled)
                VALUES (gen_random_uuid(), :username, 'hashed_pw', 'common_user', true, false)
                RETURNING id
            """), {'username': unique_username})
            user_id = user_id.fetchone()[0]

            # Test creating a client
            client_id = await conn.execute(text("""
                INSERT INTO clients (id, name, cpf, birth_date)
                VALUES (gen_random_uuid(), 'Test Client', :cpf, '1990-01-01')
                RETURNING id
            """), {'cpf': unique_cpf})
            client_id = client_id.fetchone()[0]

            # Test creating a questionnaire draft
            await conn.execute(text("""
                INSERT INTO questionnaire_drafts 
                (id, client_id, user_id, template_type, status, content, profession, disease, incident_date, medical_date)
                VALUES (gen_random_uuid(), :client_id, :user_id, 'standard', 'draft', 'Test content', 'Test profession', 'Test disease', '2024-01-01', '2024-01-02')
            """), {'client_id': client_id, 'user_id': user_id})

            # Clean up test data
            await conn.execute(text("DELETE FROM questionnaire_drafts WHERE content = 'Test content'"))
            await conn.execute(text("DELETE FROM clients WHERE name = 'Test Client'"))
            await conn.execute(text("DELETE FROM users WHERE username = :username"), {'username': unique_username})

            logger.info("✓ Basic CRUD operations test passed")

        except Exception as e:
            self.errors.append(f"CRUD operations test failed: {str(e)}")

    async def _test_cascade_relationships(self, conn):
        """Test CASCADE delete relationships work correctly."""
        try:
            # Generate unique CPF for test
            import random
            unique_cpf = f"{random.randint(10000000000, 99999999999)}"

            # Create test data
            user_id = await conn.execute(text("""
                INSERT INTO users (id, username, hashed_password, role, is_active, is_2fa_enabled)
                VALUES (gen_random_uuid(), 'cascade_test_user', 'hashed_pw', 'common_user', true, false)
                RETURNING id
            """))
            user_id = user_id.fetchone()[0]

            client_id = await conn.execute(text("""
                INSERT INTO clients (id, name, cpf, birth_date)
                VALUES (gen_random_uuid(), 'Cascade Test Client', :cpf, '1990-01-01')
                RETURNING id
            """), {'cpf': unique_cpf})
            client_id = client_id.fetchone()[0]

            # Create dependent records
            await conn.execute(text("""
                INSERT INTO questionnaire_drafts 
                (id, client_id, user_id, template_type, status, content, profession, disease, incident_date, medical_date)
                VALUES (gen_random_uuid(), :client_id, :user_id, 'standard', 'draft', 'Cascade test content', 'Test profession', 'Test disease', '2024-01-01', '2024-01-02')
            """), {'client_id': client_id, 'user_id': user_id})

            # Count questionnaire_drafts before deletion
            count_before = await conn.execute(text("""
                SELECT COUNT(*) FROM questionnaire_drafts WHERE content = 'Cascade test content'
            """))
            count_before = count_before.fetchone()[0]

            # Delete client - should cascade to questionnaire_drafts
            await conn.execute(text("DELETE FROM clients WHERE id = :client_id"), {'client_id': client_id})

            # Count questionnaire_drafts after deletion
            count_after = await conn.execute(text("""
                SELECT COUNT(*) FROM questionnaire_drafts WHERE content = 'Cascade test content'
            """))
            count_after = count_after.fetchone()[0]

            if count_before > 0 and count_after == 0:
                logger.info("✓ CASCADE delete test passed")
            else:
                self.errors.append(f"CASCADE delete failed: {count_before} records before, {count_after} records after client deletion")

            # Clean up remaining test data
            await conn.execute(text("DELETE FROM users WHERE username = 'cascade_test_user'"))

        except Exception as e:
            self.errors.append(f"CASCADE relationship test failed: {str(e)}")

    def _report_results(self):
        """Report validation results."""
        print("\n" + "="*60)
        print("DATABASE SCHEMA VALIDATION REPORT")
        print("="*60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ SCHEMA VALIDATION PASSED")
            print("All SQLAlchemy models match database schema perfectly!")
        elif not self.errors:
            print(f"\n✅ SCHEMA VALIDATION PASSED WITH {len(self.warnings)} WARNINGS")
            print("Critical schema issues: None")
        else:
            print("\n❌ SCHEMA VALIDATION FAILED")
            print(f"Critical errors: {len(self.errors)}")

        print("\n" + "="*60)


async def main():
    """Main function to run schema validation."""
    validator = SchemaValidator()

    try:
        is_valid = await validator.validate_schema()
        return 0 if is_valid else 1
    except Exception as e:
        logger.error(f"Schema validation failed with exception: {e}")
        return 1
    finally:
        await validator.engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
