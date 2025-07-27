"""End-to-end tests for client details UI using Playwright."""

import uuid
from datetime import datetime

import pytest

from app.models.client import Client
from app.models.document import Document, DocumentStatus, DocumentType


class TestClientDetailsUI:
    """E2E tests for client details page functionality."""

    @pytest.mark.asyncio
    async def test_client_details_page_navigation(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test navigation from clients list to client details page."""
        client, documents = test_client_with_documents

        # Navigate to clients page
        await nicegui_page.goto("/clients")
        
        # Wait for clients table to load
        await nicegui_page.wait_for_selector("table")
        
        # Click on "View Details" button for the client
        view_details_button = nicegui_page.locator(f'[title="Ver Detalhes"]').first
        await view_details_button.click()
        
        # Verify navigation to client details page
        await nicegui_page.wait_for_url(f"/client/{client.id}")
        
        # Verify client information is displayed
        await nicegui_page.wait_for_selector("text=Informações do Cliente")
        client_name = nicegui_page.locator(f"text={client.name}")
        await expect(client_name).to_be_visible()

    @pytest.mark.asyncio
    async def test_client_details_display(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test client details information display."""
        client, documents = test_client_with_documents

        # Navigate directly to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for page to load
        await nicegui_page.wait_for_selector("text=Informações do Cliente")
        
        # Verify client information
        await expect(nicegui_page.locator(f"text=Nome: {client.name}")).to_be_visible()
        await expect(nicegui_page.locator(f"text=CPF: {client.formatted_cpf}")).to_be_visible()
        
        birth_date_str = client.birth_date.strftime("%d/%m/%Y")
        await expect(nicegui_page.locator(f"text=Data de Nascimento: {birth_date_str}")).to_be_visible()

    @pytest.mark.asyncio
    async def test_documents_list_display(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test documents list display with different statuses."""
        client, documents = test_client_with_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents section to load
        await nicegui_page.wait_for_selector("text=Documentos")
        
        # Verify document table exists
        documents_table = nicegui_page.locator("table")
        await expect(documents_table).to_be_visible()
        
        # Verify documents are displayed
        for document in documents:
            filename_cell = nicegui_page.locator(f"text={document.filename}")
            await expect(filename_cell).to_be_visible()

    @pytest.mark.asyncio
    async def test_document_status_indicators(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test document status visual indicators."""
        client, documents = test_client_with_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents to load
        await nicegui_page.wait_for_selector("table")
        
        # Check for different status chips
        processed_chip = nicegui_page.locator(".q-chip:has-text('Concluído')")
        processing_chip = nicegui_page.locator(".q-chip:has-text('Processando')")
        failed_chip = nicegui_page.locator(".q-chip:has-text('Falha')")
        
        # At least one status should be visible
        await expect(processed_chip.or_(processing_chip).or_(failed_chip)).to_be_visible()

    @pytest.mark.asyncio
    async def test_view_document_summary(self, nicegui_page, authenticated_user, test_client_with_processed_document):
        """Test viewing document summary for processed documents."""
        client, processed_document = test_client_with_processed_document

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents to load
        await nicegui_page.wait_for_selector("table")
        
        # Find and click view summary button for processed document
        view_summary_button = nicegui_page.locator('[title="Ver Resumo do Documento"]').first
        await view_summary_button.click()
        
        # Verify summary modal opens
        await nicegui_page.wait_for_selector("text=Resumo do Documento")
        await expect(nicegui_page.locator(f"text={processed_document.filename}")).to_be_visible()
        
        # Verify document information is displayed
        await expect(nicegui_page.locator("text=Informações do Documento")).to_be_visible()
        await expect(nicegui_page.locator("text=Conteúdo Extraído")).to_be_visible()

    @pytest.mark.asyncio
    async def test_document_summary_statistics(self, nicegui_page, authenticated_user, test_client_with_processed_document):
        """Test document summary statistics display."""
        client, processed_document = test_client_with_processed_document

        # Navigate to client details page and open summary
        await nicegui_page.goto(f"/client/{client.id}")
        await nicegui_page.wait_for_selector("table")
        
        view_summary_button = nicegui_page.locator('[title="Ver Resumo do Documento"]').first
        await view_summary_button.click()
        
        # Wait for summary modal
        await nicegui_page.wait_for_selector("text=Resumo do Documento")
        
        # Verify statistics section
        await expect(nicegui_page.locator("text=Estatísticas do Processamento")).to_be_visible()
        
        # Check for statistic values (should be numbers)
        stats_section = nicegui_page.locator("text=Estatísticas do Processamento").locator("..")
        await expect(stats_section.locator("text=Blocos de Texto")).to_be_visible()
        await expect(stats_section.locator("text=Caracteres")).to_be_visible()
        await expect(stats_section.locator("text=Palavras")).to_be_visible()

    @pytest.mark.asyncio
    async def test_real_time_status_updates(self, nicegui_page, authenticated_user, test_client_with_processing_document):
        """Test real-time document status updates."""
        client, processing_document = test_client_with_processing_document

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents to load
        await nicegui_page.wait_for_selector("table")
        
        # Verify initial processing status
        processing_chip = nicegui_page.locator(".q-chip:has-text('Processando')")
        await expect(processing_chip).to_be_visible()
        
        # Simulate status change (in real scenario, this would be triggered by background processing)
        # For testing, we'll wait for auto-refresh to occur
        await nicegui_page.wait_for_timeout(6000)  # Wait longer than refresh interval
        
        # Manual refresh to ensure latest status
        refresh_button = nicegui_page.locator('[icon="refresh"]')
        await refresh_button.click()
        
        # Status might have changed during the test
        status_chips = nicegui_page.locator(".q-chip")
        await expect(status_chips.first).to_be_visible()

    @pytest.mark.asyncio
    async def test_document_retry_processing(self, nicegui_page, authenticated_user, test_client_with_failed_document):
        """Test retry processing functionality for failed documents."""
        client, failed_document = test_client_with_failed_document

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents to load
        await nicegui_page.wait_for_selector("table")
        
        # Find retry button for failed document
        retry_button = nicegui_page.locator('[title="Tentar Processar Novamente"]').first
        await retry_button.click()
        
        # Wait for success notification
        await nicegui_page.wait_for_selector("text=Reprocessamento iniciado")

    @pytest.mark.asyncio
    async def test_empty_documents_state(self, nicegui_page, authenticated_user, test_client_without_documents):
        """Test display when client has no documents."""
        client = test_client_without_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for page to load
        await nicegui_page.wait_for_selector("text=Documentos")
        
        # Verify empty state message
        await expect(nicegui_page.locator("text=Nenhum documento encontrado")).to_be_visible()
        await expect(nicegui_page.locator("text=Faça upload de documentos para este cliente")).to_be_visible()

    @pytest.mark.asyncio
    async def test_back_navigation(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test navigation back to clients list."""
        client, documents = test_client_with_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for page to load
        await nicegui_page.wait_for_selector("text=Informações do Cliente")
        
        # Click back button
        back_button = nicegui_page.locator("text=← Voltar para Clientes")
        await back_button.click()
        
        # Verify navigation back to clients list
        await nicegui_page.wait_for_url("/clients")
        await expect(nicegui_page.locator("text=Gerenciamento de Clientes")).to_be_visible()

    @pytest.mark.asyncio
    async def test_document_download_placeholder(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test document download functionality (placeholder)."""
        client, documents = test_client_with_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for documents to load
        await nicegui_page.wait_for_selector("table")
        
        # Click download button
        download_button = nicegui_page.locator('[title="Baixar Documento Original"]').first
        await download_button.click()
        
        # Verify placeholder notification
        await nicegui_page.wait_for_selector("text=Funcionalidade de download será implementada")

    @pytest.mark.asyncio
    async def test_responsive_layout(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test responsive layout on different screen sizes."""
        client, documents = test_client_with_documents

        # Test desktop size
        await nicegui_page.set_viewport_size({"width": 1200, "height": 800})
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Verify all components are visible
        await expect(nicegui_page.locator("text=Informações do Cliente")).to_be_visible()
        await expect(nicegui_page.locator("text=Documentos")).to_be_visible()
        
        # Test tablet size
        await nicegui_page.set_viewport_size({"width": 768, "height": 1024})
        await nicegui_page.reload()
        
        # Components should still be visible
        await expect(nicegui_page.locator("text=Informações do Cliente")).to_be_visible()
        await expect(nicegui_page.locator("text=Documentos")).to_be_visible()

    @pytest.mark.asyncio
    async def test_client_not_found(self, nicegui_page, authenticated_user):
        """Test behavior when client is not found."""
        fake_client_id = str(uuid.uuid4())

        # Navigate to non-existent client details page
        await nicegui_page.goto(f"/client/{fake_client_id}")
        
        # Should redirect to clients page with error notification
        await nicegui_page.wait_for_url("/clients")
        await expect(nicegui_page.locator("text=Cliente não encontrado")).to_be_visible()

    @pytest.mark.asyncio
    async def test_logout_from_client_details(self, nicegui_page, authenticated_user, test_client_with_documents):
        """Test logout functionality from client details page."""
        client, documents = test_client_with_documents

        # Navigate to client details page
        await nicegui_page.goto(f"/client/{client.id}")
        
        # Wait for page to load
        await nicegui_page.wait_for_selector("text=Informações do Cliente")
        
        # Click logout button
        logout_button = nicegui_page.locator("text=Sair")
        await logout_button.click()
        
        # Verify logout and redirect to login
        await nicegui_page.wait_for_url("/login")
        await expect(nicegui_page.locator("text=Saída realizada com sucesso")).to_be_visible()


# Test fixtures for E2E tests
@pytest.fixture
async def test_client_with_documents(async_db_session):
    """Create a test client with various documents."""
    from app.repositories.client_repository import ClientRepository
    from app.repositories.document_repository import DocumentRepository
    from app.services.client_service import ClientService
    from app.services.document_service import DocumentService

    client_repo = ClientRepository(async_db_session)
    doc_repo = DocumentRepository(async_db_session)
    client_service = ClientService(client_repo)
    doc_service = DocumentService(doc_repo)

    # Create client
    client = await client_service.create_client(
        name="João Silva",
        cpf="12345678901", 
        birth_date=datetime(1990, 1, 15).date()
    )

    # Create documents with different statuses
    documents = []
    
    # Processed document
    doc1 = await doc_service.create_document(
        client.id, "documento1.pdf", b"content1", DocumentType.SIMPLE
    )
    doc1_obj = await doc_service.get_document_by_id(uuid.UUID(doc1["document_id"]))
    await doc_service.update_document_status(doc1_obj.id, DocumentStatus.PROCESSED)
    documents.append(doc1_obj)

    # Processing document
    doc2 = await doc_service.create_document(
        client.id, "documento2.pdf", b"content2", DocumentType.COMPLEX
    )
    doc2_obj = await doc_service.get_document_by_id(uuid.UUID(doc2["document_id"]))
    await doc_service.update_document_status(doc2_obj.id, DocumentStatus.PROCESSING)
    documents.append(doc2_obj)

    # Failed document
    doc3 = await doc_service.create_document(
        client.id, "documento3.pdf", b"content3", DocumentType.SIMPLE
    )
    doc3_obj = await doc_service.get_document_by_id(uuid.UUID(doc3["document_id"]))
    await doc_service.update_document_status(
        doc3_obj.id, DocumentStatus.FAILED, "Processing failed"
    )
    documents.append(doc3_obj)

    return client, documents


@pytest.fixture
async def test_client_with_processed_document(async_db_session):
    """Create a test client with a processed document containing chunks."""
    from app.repositories.client_repository import ClientRepository
    from app.repositories.document_repository import DocumentRepository
    from app.repositories.document_chunk_repository import DocumentChunkRepository
    from app.services.client_service import ClientService
    from app.services.document_service import DocumentService

    client_repo = ClientRepository(async_db_session)
    doc_repo = DocumentRepository(async_db_session)
    chunk_repo = DocumentChunkRepository(async_db_session)
    client_service = ClientService(client_repo)
    doc_service = DocumentService(doc_repo)

    # Create client and processed document
    client = await client_service.create_client(
        name="Maria Santos",
        cpf="98765432100",
        birth_date=datetime(1985, 5, 20).date()
    )

    doc = await doc_service.create_document(
        client.id, "processed_doc.pdf", b"content", DocumentType.SIMPLE
    )
    doc_obj = await doc_service.get_document_by_id(uuid.UUID(doc["document_id"]))
    await doc_service.update_document_status(doc_obj.id, DocumentStatus.PROCESSED)

    # Create chunks
    chunks = [
        DocumentChunk(
            node_id="chunk1",
            text="Primeiro bloco de texto extraído",
            metadata={"page": 1},
            document_id=doc_obj.id
        ),
        DocumentChunk(
            node_id="chunk2", 
            text="Segundo bloco de texto extraído",
            metadata={"page": 1},
            document_id=doc_obj.id
        )
    ]
    await chunk_repo.create_multiple(chunks)

    return client, doc_obj


@pytest.fixture
async def test_client_with_processing_document(async_db_session):
    """Create a test client with a processing document."""
    from app.repositories.client_repository import ClientRepository
    from app.repositories.document_repository import DocumentRepository
    from app.services.client_service import ClientService
    from app.services.document_service import DocumentService

    client_repo = ClientRepository(async_db_session)
    doc_repo = DocumentRepository(async_db_session)
    client_service = ClientService(client_repo)
    doc_service = DocumentService(doc_repo)

    client = await client_service.create_client(
        name="Pedro Costa",
        cpf="11111111111",
        birth_date=datetime(1992, 8, 10).date()
    )

    doc = await doc_service.create_document(
        client.id, "processing_doc.pdf", b"content", DocumentType.COMPLEX
    )
    doc_obj = await doc_service.get_document_by_id(uuid.UUID(doc["document_id"]))
    await doc_service.update_document_status(doc_obj.id, DocumentStatus.PROCESSING)

    return client, doc_obj


@pytest.fixture
async def test_client_with_failed_document(async_db_session):
    """Create a test client with a failed document."""
    from app.repositories.client_repository import ClientRepository
    from app.repositories.document_repository import DocumentRepository
    from app.services.client_service import ClientService
    from app.services.document_service import DocumentService

    client_repo = ClientRepository(async_db_session)
    doc_repo = DocumentRepository(async_db_session)
    client_service = ClientService(client_repo)
    doc_service = DocumentService(doc_repo)

    client = await client_service.create_client(
        name="Ana Lima",
        cpf="22222222222",
        birth_date=datetime(1988, 3, 25).date()
    )

    doc = await doc_service.create_document(
        client.id, "failed_doc.pdf", b"content", DocumentType.SIMPLE
    )
    doc_obj = await doc_service.get_document_by_id(uuid.UUID(doc["document_id"]))
    await doc_service.update_document_status(
        doc_obj.id, DocumentStatus.FAILED, "OCR processing failed"
    )

    return client, doc_obj


@pytest.fixture
async def test_client_without_documents(async_db_session):
    """Create a test client without any documents."""
    from app.repositories.client_repository import ClientRepository
    from app.services.client_service import ClientService

    client_repo = ClientRepository(async_db_session)
    client_service = ClientService(client_repo)

    client = await client_service.create_client(
        name="Carlos Ferreira",
        cpf="33333333333",
        birth_date=datetime(1975, 12, 5).date()
    )

    return client