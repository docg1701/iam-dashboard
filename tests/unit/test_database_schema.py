"""Unit tests for database schema integrity and CRUD operations."""

from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Client, QuestionnaireDraft, User, UserRole


@pytest_asyncio.fixture
async def db_session(async_session: AsyncSession) -> AsyncSession:
    """Provide a database session for testing."""
    return async_session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        username="test_user_schema",
        hashed_password="hashed_password",
        role=UserRole.COMMON_USER,
        is_active=True,
        is_2fa_enabled=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession) -> Client:
    """Create a test client."""
    client = Client(
        name="Test Client Schema",
        cpf="12345678901",
        birth_date=date(1990, 1, 1)
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


class TestClientCRUD:
    """Test client CRUD operations end-to-end."""

    @pytest.mark.asyncio
    async def test_create_client(self, db_session: AsyncSession):
        """Test creating a client."""
        client = Client(
            name="Create Test Client",
            cpf="98765432109",
            birth_date=date(1985, 5, 15)
        )

        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)

        assert client.id is not None
        assert client.name == "Create Test Client"
        assert client.cpf == "98765432109"
        assert client.birth_date == date(1985, 5, 15)
        assert client.created_at is not None
        assert client.updated_at is not None

    @pytest.mark.asyncio
    async def test_read_client(self, db_session: AsyncSession, test_client: Client):
        """Test reading a client."""
        result = await db_session.get(Client, test_client.id)

        assert result is not None
        assert result.id == test_client.id
        assert result.name == test_client.name
        assert result.cpf == test_client.cpf

    @pytest.mark.asyncio
    async def test_update_client(self, db_session: AsyncSession, test_client: Client):
        """Test updating a client."""
        test_client.name = "Updated Client Name"

        await db_session.commit()
        await db_session.refresh(test_client)

        assert test_client.name == "Updated Client Name"
        assert test_client.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_client(self, db_session: AsyncSession, test_client: Client):
        """Test deleting a client."""
        client_id = test_client.id

        await db_session.delete(test_client)
        await db_session.commit()

        result = await db_session.get(Client, client_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_client_cpf_unique_constraint(self, db_session: AsyncSession):
        """Test that CPF unique constraint is enforced."""
        client1 = Client(
            name="Client 1",
            cpf="11111111111",
            birth_date=date(1990, 1, 1)
        )

        client2 = Client(
            name="Client 2",
            cpf="11111111111",  # Same CPF
            birth_date=date(1991, 1, 1)
        )

        db_session.add(client1)
        await db_session.commit()

        db_session.add(client2)
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()


class TestQuestionnaireDraftCRUD:
    """Test questionnaire_drafts CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_questionnaire_draft(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_client: Client
    ):
        """Test creating a questionnaire draft."""
        draft = QuestionnaireDraft(
            client_id=test_client.id,
            user_id=test_user.id,
            template_type="standard",
            status="draft",
            content="Test questionnaire content",
            profession="Doctor",
            disease="Test Disease",
            incident_date="2024-01-01",
            medical_date="2024-01-02",
            metadata_={"test": "data"}
        )

        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        assert draft.id is not None
        assert draft.client_id == test_client.id
        assert draft.user_id == test_user.id
        assert draft.template_type == "standard"
        assert draft.status == "draft"
        assert draft.content == "Test questionnaire content"
        assert draft.profession == "Doctor"
        assert draft.disease == "Test Disease"
        assert draft.incident_date == "2024-01-01"
        assert draft.medical_date == "2024-01-02"
        assert draft.metadata_ == {"test": "data"}
        assert draft.created_at is not None
        assert draft.updated_at is not None

    @pytest.mark.asyncio
    async def test_read_questionnaire_draft(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_client: Client
    ):
        """Test reading a questionnaire draft."""
        draft = QuestionnaireDraft(
            client_id=test_client.id,
            user_id=test_user.id,
            template_type="standard",
            status="draft",
            content="Read test content",
            profession="Lawyer",
            disease="Test Condition",
            incident_date="2024-02-01",
            medical_date="2024-02-02"
        )

        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        result = await db_session.get(QuestionnaireDraft, draft.id)

        assert result is not None
        assert result.id == draft.id
        assert result.content == "Read test content"
        assert result.profession == "Lawyer"

    @pytest.mark.asyncio
    async def test_update_questionnaire_draft(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_client: Client
    ):
        """Test updating a questionnaire draft."""
        draft = QuestionnaireDraft(
            client_id=test_client.id,
            user_id=test_user.id,
            template_type="standard",
            status="draft",
            content="Original content",
            profession="Engineer",
            disease="Test Issue",
            incident_date="2024-03-01",
            medical_date="2024-03-02"
        )

        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        draft.content = "Updated content"
        draft.status = "published"

        await db_session.commit()
        await db_session.refresh(draft)

        assert draft.content == "Updated content"
        assert draft.status == "published"
        assert draft.updated_at is not None

    @pytest.mark.asyncio
    async def test_delete_questionnaire_draft(
        self,
        db_session: AsyncSession,
        test_user: User,
        test_client: Client
    ):
        """Test deleting a questionnaire draft."""
        draft = QuestionnaireDraft(
            client_id=test_client.id,
            user_id=test_user.id,
            template_type="standard",
            status="draft",
            content="Delete test content",
            profession="Teacher",
            disease="Test Problem",
            incident_date="2024-04-01",
            medical_date="2024-04-02"
        )

        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        draft_id = draft.id

        await db_session.delete(draft)
        await db_session.commit()

        result = await db_session.get(QuestionnaireDraft, draft_id)
        assert result is None


class TestCascadeDeletion:
    """Test CASCADE deletion scenarios."""

    @pytest.mark.asyncio
    async def test_client_deletion_cascades_to_questionnaire_drafts(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test that deleting a client cascades to questionnaire_drafts."""
        # Create client
        client = Client(
            name="Cascade Test Client",
            cpf="55555555555",
            birth_date=date(1992, 6, 15)
        )
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)

        # Create questionnaire draft
        draft = QuestionnaireDraft(
            client_id=client.id,
            user_id=test_user.id,
            template_type="standard",
            status="draft",
            content="Cascade test content",
            profession="Architect",
            disease="Test Cascade Disease",
            incident_date="2024-05-01",
            medical_date="2024-05-02"
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        draft_id = draft.id

        # Verify draft exists
        result = await db_session.get(QuestionnaireDraft, draft_id)
        assert result is not None

        # Delete client
        await db_session.delete(client)
        await db_session.commit()

        # Verify questionnaire draft was CASCADE deleted
        result = await db_session.get(QuestionnaireDraft, draft_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_user_deletion_cascades_to_questionnaire_drafts(
        self,
        db_session: AsyncSession,
        test_client: Client
    ):
        """Test that deleting a user cascades to questionnaire_drafts."""
        # Create user
        user = User(
            username="cascade_test_user",
            hashed_password="hashed_password",
            role=UserRole.COMMON_USER,
            is_active=True,
            is_2fa_enabled=False
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create questionnaire draft
        draft = QuestionnaireDraft(
            client_id=test_client.id,
            user_id=user.id,
            template_type="standard",
            status="draft",
            content="User cascade test content",
            profession="Designer",
            disease="Test User Cascade Disease",
            incident_date="2024-06-01",
            medical_date="2024-06-02"
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        draft_id = draft.id

        # Verify draft exists
        result = await db_session.get(QuestionnaireDraft, draft_id)
        assert result is not None

        # Delete user
        await db_session.delete(user)
        await db_session.commit()

        # Verify questionnaire draft was CASCADE deleted
        result = await db_session.get(QuestionnaireDraft, draft_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_constraint_violations_during_crud(self, db_session: AsyncSession):
        """Test that normal CRUD operations don't cause PostgreSQL constraint violations."""
        # Create user
        user = User(
            username="constraint_test_user",
            hashed_password="hashed_password",
            role=UserRole.COMMON_USER,
            is_active=True,
            is_2fa_enabled=False
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create client
        client = Client(
            name="Constraint Test Client",
            cpf="77777777777",
            birth_date=date(1993, 7, 20)
        )
        db_session.add(client)
        await db_session.commit()
        await db_session.refresh(client)

        # Create questionnaire draft
        draft = QuestionnaireDraft(
            client_id=client.id,
            user_id=user.id,
            template_type="custom",
            status="in_review",
            content="Constraint test content",
            profession="Consultant",
            disease="Test Constraint Disease",
            incident_date="2024-07-01",
            medical_date="2024-07-02",
            metadata_={"test": "constraint"}
        )
        db_session.add(draft)
        await db_session.commit()
        await db_session.refresh(draft)

        # Update operations
        draft.status = "approved"
        client.name = "Updated Constraint Test Client"
        user.is_active = False

        await db_session.commit()

        # Verify updates worked
        await db_session.refresh(draft)
        await db_session.refresh(client)
        await db_session.refresh(user)

        assert draft.status == "approved"
        assert client.name == "Updated Constraint Test Client"
        assert user.is_active is False

        # Clean up (test deletion in proper order)
        await db_session.delete(draft)
        await db_session.delete(client)
        await db_session.delete(user)
        await db_session.commit()


class TestSchemaIntegrity:
    """Test database schema integrity."""

    @pytest.mark.asyncio
    async def test_questionnaire_drafts_table_structure(self, db_session: AsyncSession):
        """Test that questionnaire_drafts table has correct structure."""
        result = await db_session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'questionnaire_drafts'
            ORDER BY ordinal_position
        """))

        columns = {row[0]: {'type': row[1], 'nullable': row[2] == 'YES', 'default': row[3]}
                  for row in result}

        # Verify required columns exist
        required_columns = [
            'id', 'client_id', 'user_id', 'template_type', 'status',
            'content', 'profession', 'disease', 'incident_date', 'medical_date',
            'metadata', 'created_at', 'updated_at'
        ]

        for col in required_columns:
            assert col in columns, f"Required column '{col}' missing from questionnaire_drafts table"

        # Verify specific column properties
        assert columns['id']['type'] == 'uuid'
        assert not columns['id']['nullable']

        assert columns['client_id']['type'] == 'uuid'
        assert not columns['client_id']['nullable']

        assert columns['user_id']['type'] == 'uuid'
        assert not columns['user_id']['nullable']

        assert columns['template_type']['type'] == 'character varying'
        assert not columns['template_type']['nullable']
        assert "'standard'" in str(columns['template_type']['default'])

        assert columns['status']['type'] == 'character varying'
        assert not columns['status']['nullable']
        assert "'draft'" in str(columns['status']['default'])

    @pytest.mark.asyncio
    async def test_foreign_key_constraints_exist(self, db_session: AsyncSession):
        """Test that foreign key constraints are properly configured."""
        result = await db_session.execute(text("""
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
            WHERE tc.table_name = 'questionnaire_drafts' AND tc.constraint_type = 'FOREIGN KEY'
        """))

        constraints = [(row[0], row[1], row[2], row[3], row[4]) for row in result]

        # Check client_id foreign key
        client_fk = [c for c in constraints if c[1] == 'client_id']
        assert len(client_fk) == 1
        assert client_fk[0][2] == 'clients'
        assert client_fk[0][3] == 'id'
        assert client_fk[0][4] == 'CASCADE'

        # Check user_id foreign key
        user_fk = [c for c in constraints if c[1] == 'user_id']
        assert len(user_fk) == 1
        assert user_fk[0][2] == 'users'
        assert user_fk[0][3] == 'id'
        assert user_fk[0][4] == 'CASCADE'

    @pytest.mark.asyncio
    async def test_performance_indexes_exist(self, db_session: AsyncSession):
        """Test that performance indexes are created."""
        result = await db_session.execute(text("""
            SELECT i.relname AS index_name
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
            AND t.relname = 'questionnaire_drafts'
            AND i.relname LIKE 'idx_%'
        """))

        indexes = [row[0] for row in result]

        # Verify required indexes exist
        assert 'idx_questionnaire_drafts_client_id' in indexes
        assert 'idx_questionnaire_drafts_user_id' in indexes
