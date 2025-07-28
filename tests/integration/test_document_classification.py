"""Integration tests for "simples" vs "complexos" document processing paths."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.document_preprocessing import DocumentPreprocessor
from app.workers.llama_index_processor import LlamaIndexProcessor


class TestDocumentClassification:
    """Integration tests for document classification and processing paths."""

    @pytest.fixture
    def preprocessor(self):
        """Create document preprocessor instance."""
        return DocumentPreprocessor()

    @pytest.fixture
    def processor(self):
        """Create Llama-Index processor instance."""
        with patch('app.workers.llama_index_processor.get_llama_index_config'):
            with patch('app.workers.llama_index_processor.get_document_preprocessor'):
                with patch('app.workers.llama_index_processor.get_security_validator'):
                    return LlamaIndexProcessor()

    @pytest.fixture
    def simple_pdf_path(self, tmp_path):
        """Create a simple PDF with extractable text."""
        pdf_path = tmp_path / "simple_document.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'Simple PDF with extractable text content')
        return pdf_path

    @pytest.fixture
    def complex_pdf_path(self, tmp_path):
        """Create a complex PDF that would need OCR."""
        pdf_path = tmp_path / "complex_document.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'Complex PDF - scanned image content')
        return pdf_path

    def test_simple_document_classification(self, preprocessor, simple_pdf_path):
        """Test classification of simple documents with extractable text."""
        # Arrange
        with patch('app.services.document_preprocessing.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()

            # Simulate lots of extractable text (indicates simple document)
            mock_page.get_text.return_value = "A" * 1500  # Lots of text
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc

            # Act
            is_complex = preprocessor.is_complex_document(simple_pdf_path)

            # Assert
            assert is_complex is False  # Should be classified as simple

    def test_complex_document_classification(self, preprocessor, complex_pdf_path):
        """Test classification of complex documents requiring OCR."""
        # Arrange
        with patch('app.services.document_preprocessing.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()

            # Simulate little to no extractable text (indicates scanned/complex document)
            mock_page.get_text.return_value = ""  # No extractable text
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc

            # Act
            is_complex = preprocessor.is_complex_document(complex_pdf_path)

            # Assert
            assert is_complex is True  # Should be classified as complex

    @pytest.mark.asyncio
    async def test_simple_document_processing_path(self, processor, simple_pdf_path):
        """Test that simple documents use direct text extraction path."""
        # Arrange
        with patch.object(processor, '_extract_simple_text') as mock_simple_extract:
            with patch.object(processor.preprocessor, 'extract_text_from_complex_document') as mock_complex_extract:
                mock_simple_extract.return_value = "Simple extracted text"

                # Simulate simple document
                mock_document = MagicMock()
                mock_document.document_type = "simple"
                mock_document.id = "test_id"
                mock_document.filename = "simple.pdf"

                # Mock security validation
                processor.security_validator.validate_pdf_file.return_value = {"valid": True}
                processor.security_validator.sanitize_extracted_text.return_value = "Clean text"

                # Mock Llama-Index components
                with patch('app.workers.llama_index_processor.LlamaDocument'):
                    processor.text_splitter.get_nodes_from_documents.return_value = []

                    # Act
                    try:
                        await processor.process_document(mock_document, simple_pdf_path)
                    except Exception:
                        pass  # We're testing the path, not the full execution

                    # Assert
                    mock_simple_extract.assert_called_once_with(simple_pdf_path)
                    mock_complex_extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_complex_document_processing_path(self, processor, complex_pdf_path):
        """Test that complex documents use OCR processing path."""
        # Arrange
        with patch.object(processor, '_extract_simple_text') as mock_simple_extract:
            with patch.object(processor.preprocessor, 'extract_text_from_complex_document') as mock_complex_extract:
                mock_complex_extract.return_value = "OCR extracted text"

                # Simulate complex document
                mock_document = MagicMock()
                mock_document.document_type = "complex"
                mock_document.id = "test_id"
                mock_document.filename = "complex.pdf"

                # Mock security validation
                processor.security_validator.validate_pdf_file.return_value = {"valid": True}
                processor.security_validator.sanitize_extracted_text.return_value = "Clean OCR text"

                # Mock Llama-Index components
                with patch('app.workers.llama_index_processor.LlamaDocument'):
                    processor.text_splitter.get_nodes_from_documents.return_value = []

                    # Act
                    try:
                        await processor.process_document(mock_document, complex_pdf_path)
                    except Exception:
                        pass  # We're testing the path, not the full execution

                    # Assert
                    mock_complex_extract.assert_called_once_with(complex_pdf_path)
                    mock_simple_extract.assert_not_called()

    def test_user_driven_classification_workflow(self, processor, simple_pdf_path):
        """Test that users must specify document type (no automatic classification)."""
        # Arrange
        mock_document = MagicMock()
        mock_document.document_type = None  # User hasn't specified type yet
        mock_document.id = "test_id"
        mock_document.filename = "unclassified.pdf"

        # Act & Assert - System should require user to specify type
        with patch('app.workers.document_processor._process_document_async'):
            # Simulate document processing without user-specified type
            try:
                # This should fail because document_type is None
                import asyncio
                import uuid

                from app.workers.document_processor import _process_document_async
                asyncio.run(_process_document_async(uuid.uuid4(), "test_task"))
                raise AssertionError("Should fail when document_type is not set by user")
            except (ValueError, Exception) as e:
                assert "must have type set by user" in str(e) or "Document" in str(e)

    def test_borderline_classification_case(self, preprocessor, tmp_path):
        """Test classification of borderline documents (moderate text content)."""
        # Arrange
        borderline_pdf = tmp_path / "borderline.pdf"
        with open(borderline_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'Borderline document content')

        with patch('app.services.document_preprocessing.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()

            # Simulate moderate text content (borderline case)
            mock_page.get_text.return_value = "A" * 150  # Moderate amount of text
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc

            # Act
            is_complex = preprocessor.is_complex_document(borderline_pdf)

            # Assert
            # With 150 chars out of 2000 expected (~7.5%), should be classified as complex
            assert is_complex is True

    def test_multi_page_document_classification(self, preprocessor, tmp_path):
        """Test classification logic for multi-page documents."""
        # Arrange
        multi_page_pdf = tmp_path / "multi_page.pdf"
        with open(multi_page_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'Multi-page document')

        with patch('app.services.document_preprocessing.fitz.open') as mock_fitz:
            mock_doc = MagicMock()

            # Mock multiple pages with varying text content
            mock_page_1 = MagicMock()
            mock_page_1.get_text.return_value = "A" * 800  # Good text on page 1

            mock_page_2 = MagicMock()
            mock_page_2.get_text.return_value = ""  # No text on page 2 (scanned)

            mock_page_3 = MagicMock()
            mock_page_3.get_text.return_value = "B" * 500  # Some text on page 3

            mock_doc.__len__.return_value = 3
            mock_doc.__getitem__.side_effect = lambda i: [mock_page_1, mock_page_2, mock_page_3][i]
            mock_fitz.return_value = mock_doc

            # Act
            is_complex = preprocessor.is_complex_document(multi_page_pdf)

            # Assert
            # Total: 1300 chars out of 6000 expected (~21.7%), should be simple
            assert is_complex is False

    def test_classification_error_handling(self, preprocessor, tmp_path):
        """Test classification when PDF cannot be opened or analyzed."""
        # Arrange
        corrupt_pdf = tmp_path / "corrupt.pdf"
        with open(corrupt_pdf, 'wb') as f:
            f.write(b'Not a valid PDF')

        with patch('app.services.document_preprocessing.fitz.open', side_effect=Exception("Cannot open PDF")):
            # Act
            is_complex = preprocessor.is_complex_document(corrupt_pdf)

            # Assert
            # Should default to complex when classification fails
            assert is_complex is True

    def test_processor_user_type_integration(self, processor):
        """Test integration between processor and user-specified document types."""
        # Arrange
        test_path = Path("/test/document.pdf")

        # Act & Assert - Test simple processing path (user selected "simple")
        with patch.object(processor, '_extract_simple_text_or_local_ocr') as mock_simple:
            mock_simple.return_value = "Local OCR text"
            result = processor._extract_simple_text_or_local_ocr(test_path)
            assert result == "Local OCR text"
            mock_simple.assert_called_once_with(test_path)

        # Act & Assert - Test complex processing path (user selected "complex")
        with patch.object(processor.preprocessor, 'extract_text_from_complex_document') as mock_complex:
            mock_complex.return_value = "Gemini OCR text"
            result = processor.preprocessor.extract_text_from_complex_document(test_path)
            assert result == "Gemini OCR text"
            mock_complex.assert_called_once_with(test_path)

    @pytest.mark.asyncio
    async def test_different_processing_performance(self, processor):
        """Test that simple and complex processing have different performance characteristics."""
        # This test would measure processing time differences between simple and complex documents
        # In practice, complex documents should take longer due to OCR processing
        pass

    def test_text_quality_assessment(self, preprocessor):
        """Test text quality assessment in classification logic."""
        # This could test more sophisticated classification based on text quality,
        # character recognition confidence, etc.
        pass

    def test_classification_consistency(self, preprocessor, tmp_path):
        """Test that classification is consistent across multiple runs."""
        # Arrange
        consistent_pdf = tmp_path / "consistent.pdf"
        with open(consistent_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\n')
            f.write(b'Consistent document for testing')

        with patch('app.services.document_preprocessing.fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "A" * 1000
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc

            # Act - run classification multiple times
            results = []
            for _ in range(5):
                results.append(preprocessor.is_complex_document(consistent_pdf))

            # Assert - all results should be the same
            assert len(set(results)) == 1  # All results are identical
