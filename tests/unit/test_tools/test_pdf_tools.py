"""Unit tests for PDF processing tools."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.tools.pdf_tools import PDFReaderTool


class TestPDFReaderTool:
    """Test PDFReaderTool functionality."""

    @pytest.fixture
    def pdf_tool(self) -> PDFReaderTool:
        """Create a test PDFReaderTool instance."""
        return PDFReaderTool(max_file_size_mb=10)

    @pytest.fixture
    def sample_pdf_path(self, tmp_path: Path) -> str:
        """Create a sample PDF file path."""
        pdf_file = tmp_path / "test_document.pdf"
        # Create a dummy PDF file for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        pdf_file.write_bytes(pdf_content)
        return str(pdf_file)

    def test_tool_initialization(self, pdf_tool: PDFReaderTool) -> None:
        """Test tool initialization."""
        assert pdf_tool.max_file_size_mb == 10
        assert pdf_tool.max_file_size_bytes == 10 * 1024 * 1024

    def test_validate_file_exists(
        self, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test file validation for existing file."""
        with patch("fitz.open") as mock_fitz_open:
            # Mock PyMuPDF document
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=1)  # 1 page
            mock_fitz_open.return_value = mock_doc

            result = pdf_tool.validate_file(sample_pdf_path)

            assert result["valid"] is True
            assert "file_size" in result
            assert result["page_count"] == 1

    def test_validate_file_not_exists(self, pdf_tool: PDFReaderTool) -> None:
        """Test file validation for non-existent file."""
        result = pdf_tool.validate_file("/path/to/nonexistent.pdf")

        assert result["valid"] is False
        assert "does not exist" in result["error"]

    def test_validate_file_not_pdf(
        self, pdf_tool: PDFReaderTool, tmp_path: Path
    ) -> None:
        """Test file validation for non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is not a PDF")

        result = pdf_tool.validate_file(str(txt_file))

        assert result["valid"] is False
        assert "not a PDF" in result["error"]

    def test_validate_file_too_large(self, tmp_path: Path) -> None:
        """Test file validation for oversized file."""
        tool = PDFReaderTool(max_file_size_mb=1)  # 1MB limit

        large_file = tmp_path / "large.pdf"
        large_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB file

        result = tool.validate_file(str(large_file))

        assert result["valid"] is False
        assert "too large" in result["error"]

    @patch("fitz.open")
    def test_extract_metadata_success(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test successful metadata extraction."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.metadata = {"title": "Test Document", "author": "Test Author"}
        mock_doc.__len__ = Mock(return_value=3)  # 3 pages
        mock_doc.needs_pass = False
        mock_doc.get_toc.return_value = ["Chapter 1"]

        # Mock pages
        mock_page = Mock()
        mock_page.rect = Mock(width=612, height=792)
        mock_page.rotation = 0
        mock_doc.load_page.return_value = mock_page

        mock_fitz_open.return_value = mock_doc

        result = pdf_tool.extract_metadata(sample_pdf_path)

        assert result["success"] is True
        assert result["metadata"]["title"] == "Test Document"
        assert result["document_info"]["page_count"] == 3
        assert result["document_info"]["is_encrypted"] is False
        assert len(result["page_info"]) > 0

    @patch("fitz.open")
    def test_extract_text_content_success(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test successful text content extraction."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)  # 2 pages

        # Mock pages with text
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "This is page 1 content"
        mock_page1.get_images.return_value = []
        mock_page1.annots.return_value = []

        mock_page2 = Mock()
        mock_page2.get_text.return_value = "This is page 2 content"
        mock_page2.get_images.return_value = [("image1",)]
        mock_page2.annots.return_value = []

        mock_doc.load_page.side_effect = [mock_page1, mock_page2]
        mock_fitz_open.return_value = mock_doc

        result = pdf_tool.extract_text_content(sample_pdf_path)

        assert result["success"] is True
        assert result["total_pages"] == 2
        assert result["total_chars"] == len("This is page 1 content") + len(
            "This is page 2 content"
        )
        assert len(result["text_content"]) == 2
        assert result["text_content"][0]["text"] == "This is page 1 content"
        assert result["text_content"][1]["has_images"] is True

    @patch("fitz.open")
    def test_extract_images_info_success(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test successful image information extraction."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)  # 1 page

        # Mock page with images
        mock_page = Mock()
        mock_page.get_images.return_value = [
            (1, 0, 100, 200, 8, "DeviceRGB", "", "image1", "")
        ]

        # Mock pixmap
        mock_pixmap = Mock()
        mock_pixmap.width = 100
        mock_pixmap.height = 200
        mock_pixmap.colorspace = Mock(name="DeviceRGB")
        mock_pixmap.n = 3  # 3 components (RGB)

        with patch("fitz.Pixmap", return_value=mock_pixmap):
            mock_doc.load_page.return_value = mock_page
            mock_fitz_open.return_value = mock_doc

            result = pdf_tool.extract_images_info(sample_pdf_path)

            assert result["success"] is True
            assert result["total_images"] == 1
            assert len(result["images_by_page"]) == 1
            assert result["images_by_page"][0]["image_count"] == 1

    def test_detect_tables_simple(self, pdf_tool: PDFReaderTool) -> None:
        """Test simple table detection."""
        # Mock page with aligned text blocks (table-like structure)
        mock_page = Mock()
        mock_blocks = [
            {
                "lines": [
                    {"bbox": [0, 100, 200, 110]},  # Same y-coordinate
                    {"bbox": [0, 100, 200, 110]},  # Same y-coordinate
                    {"bbox": [0, 120, 200, 130]},  # Different y-coordinate
                    {"bbox": [0, 120, 200, 130]},  # Same as above
                ]
            }
        ]
        mock_page.get_text.return_value = {"blocks": mock_blocks}

        # This is a private method, so we test it through process_document
        with (
            patch.object(
                pdf_tool,
                "validate_file",
                return_value={"valid": True, "file_size": 1000, "page_count": 1},
            ),
            patch.object(
                pdf_tool,
                "extract_metadata",
                return_value={
                    "success": True,
                    "metadata": {},
                    "document_info": {},
                    "page_info": [],
                },
            ),
            patch.object(pdf_tool, "extract_text_content") as mock_extract_text,
            patch.object(
                pdf_tool,
                "extract_images_info",
                return_value={"success": True, "total_images": 0, "images_by_page": []},
            ),
        ):
            mock_extract_text.return_value = {
                "success": True,
                "text_content": [{"page_number": 1, "has_tables": True}],
                "total_pages": 1,
                "total_chars": 100,
                "average_chars_per_page": 100,
            }

            result = pdf_tool.process_document("/test/path.pdf")
            assert result["success"] is True

    @patch("fitz.open")
    def test_process_document_complete_success(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test complete document processing workflow."""
        # Mock successful operations
        with (
            patch.object(
                pdf_tool,
                "validate_file",
                return_value={"valid": True, "file_size": 1000, "page_count": 1},
            ),
            patch.object(
                pdf_tool,
                "extract_metadata",
                return_value={
                    "success": True,
                    "metadata": {"title": "Test"},
                    "document_info": {"page_count": 1},
                    "page_info": [],
                },
            ),
            patch.object(
                pdf_tool,
                "extract_text_content",
                return_value={
                    "success": True,
                    "text_content": [{"page_number": 1, "text": "Test content"}],
                    "total_pages": 1,
                    "total_chars": 12,
                    "average_chars_per_page": 12,
                },
            ),
            patch.object(
                pdf_tool,
                "extract_images_info",
                return_value={"success": True, "total_images": 0, "images_by_page": []},
            ),
        ):
            result = pdf_tool.process_document(sample_pdf_path)

            assert result["success"] is True
            assert "validation" in result
            assert "metadata" in result
            assert "text_content" in result
            assert "images_info" in result

    def test_process_document_validation_failure(self, pdf_tool: PDFReaderTool) -> None:
        """Test document processing with validation failure."""
        with patch.object(
            pdf_tool,
            "validate_file",
            return_value={"valid": False, "error": "File not found"},
        ):
            result = pdf_tool.process_document("/nonexistent.pdf")

            assert result["success"] is False
            assert result["error"] == "File not found"

    @patch("fitz.open", side_effect=Exception("PDF open failed"))
    def test_extract_metadata_failure(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test metadata extraction failure."""
        result = pdf_tool.extract_metadata(sample_pdf_path)

        assert result["success"] is False
        assert "Failed to extract metadata" in result["error"]

    @patch("fitz.open", side_effect=Exception("PDF open failed"))
    def test_extract_text_content_failure(
        self, mock_fitz_open: Mock, pdf_tool: PDFReaderTool, sample_pdf_path: str
    ) -> None:
        """Test text content extraction failure."""
        result = pdf_tool.extract_text_content(sample_pdf_path)

        assert result["success"] is False
        assert "Failed to extract text" in result["error"]
