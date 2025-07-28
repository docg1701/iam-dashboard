"""Unit tests for OCR processing tools."""

from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from app.tools.ocr_tools import OCRProcessorTool


class TestOCRProcessorTool:
    """Test OCRProcessorTool functionality."""

    @pytest.fixture
    def ocr_tool(self) -> OCRProcessorTool:
        """Create a test OCRProcessorTool instance."""
        return OCRProcessorTool(
            min_confidence=60.0,
            dpi=200,
            preprocessing=True
        )

    @pytest.fixture
    def sample_pdf_path(self, tmp_path: Path) -> str:
        """Create a sample PDF file path."""
        pdf_file = tmp_path / "test_document.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        return str(pdf_file)

    @pytest.fixture
    def sample_image(self) -> np.ndarray:
        """Create a sample image array."""
        # Create a simple 100x100 grayscale image
        return np.random.randint(0, 255, (100, 100), dtype=np.uint8)

    def test_tool_initialization(self, ocr_tool: OCRProcessorTool) -> None:
        """Test tool initialization."""
        assert ocr_tool.min_confidence == 60.0
        assert ocr_tool.dpi == 200
        assert ocr_tool.preprocessing is True
        assert ocr_tool.tesseract_config == r'--oem 3 --psm 6'

    @patch('pytesseract.get_tesseract_version')
    @patch('cv2.__version__', '4.5.0')
    def test_validate_dependencies_success(self, mock_tesseract_version: Mock, ocr_tool: OCRProcessorTool) -> None:
        """Test successful dependency validation."""
        mock_tesseract_version.return_value = "5.0.0"

        with patch('PIL.Image.__version__', '9.0.0'):
            result = ocr_tool.validate_dependencies()

            assert result["valid"] is True
            assert "tesseract" in result["dependencies"]
            assert "opencv" in result["dependencies"]
            assert "pillow" in result["dependencies"]

    @patch('pytesseract.get_tesseract_version', side_effect=Exception("Tesseract not found"))
    def test_validate_dependencies_failure(self, mock_tesseract_version: Mock, ocr_tool: OCRProcessorTool) -> None:
        """Test dependency validation failure."""
        result = ocr_tool.validate_dependencies()

        assert result["valid"] is False
        assert "OCR dependencies validation failed" in result["error"]

    @patch('cv2.fastNlMeansDenoising')
    @patch('cv2.adaptiveThreshold')
    @patch('cv2.morphologyEx')
    def test_preprocess_image_success(self, mock_morph: Mock, mock_thresh: Mock, mock_denoise: Mock, ocr_tool: OCRProcessorTool, sample_image: np.ndarray) -> None:
        """Test successful image preprocessing."""
        # Mock OpenCV functions
        mock_denoise.return_value = sample_image
        mock_thresh.return_value = sample_image
        mock_morph.return_value = sample_image

        result = ocr_tool.preprocess_image(sample_image)

        assert isinstance(result, np.ndarray)
        assert result.shape == sample_image.shape
        mock_denoise.assert_called_once()
        mock_thresh.assert_called_once()

    def test_preprocess_image_failure(self, ocr_tool: OCRProcessorTool, sample_image: np.ndarray) -> None:
        """Test image preprocessing failure (returns original image)."""
        with patch('cv2.fastNlMeansDenoising', side_effect=Exception("OpenCV error")):
            result = ocr_tool.preprocess_image(sample_image)

            # Should return original image on failure
            assert np.array_equal(result, sample_image)

    @patch('fitz.open')
    def test_extract_page_image_success(self, mock_fitz_open: Mock, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test successful page image extraction."""
        # Mock PyMuPDF objects
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()

        mock_pix.width = 800
        mock_pix.height = 600
        mock_pix.tobytes.return_value = b"fake image data"

        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.load_page.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        # Mock PIL Image
        with patch('PIL.Image.open') as mock_image_open, \
             patch('numpy.array') as mock_np_array:

            mock_pil_image = Mock()
            mock_image_open.return_value = mock_pil_image
            mock_np_array.return_value = np.zeros((600, 800, 3), dtype=np.uint8)

            result = ocr_tool.extract_page_image(mock_doc, 0)

            assert result["success"] is True
            assert result["width"] == 800
            assert result["height"] == 600
            assert result["page_number"] == 1

    @patch('fitz.open')
    def test_extract_page_image_failure(self, mock_fitz_open: Mock, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test page image extraction failure."""
        mock_doc = Mock()
        mock_doc.load_page.side_effect = Exception("Page load failed")
        mock_fitz_open.return_value = mock_doc

        result = ocr_tool.extract_page_image(mock_doc, 0)

        assert result["success"] is False
        assert "Failed to extract image" in result["error"]

    @patch('pytesseract.image_to_string')
    @patch('pytesseract.image_to_data')
    def test_perform_ocr_on_image_success(self, mock_image_to_data: Mock, mock_image_to_string: Mock, ocr_tool: OCRProcessorTool, sample_image: np.ndarray) -> None:
        """Test successful OCR on image."""
        # Mock Tesseract responses
        mock_image_to_string.return_value = "Extracted text from image"
        mock_image_to_data.return_value = {
            'conf': ['75', '80', '85', '70'],
            'text': ['Extracted', 'text', 'from', 'image']
        }

        with patch.object(ocr_tool, 'preprocess_image', return_value=sample_image), \
             patch('PIL.Image.fromarray') as mock_from_array:

            mock_pil_image = Mock()
            mock_from_array.return_value = mock_pil_image

            result = ocr_tool.perform_ocr_on_image(sample_image, 1)

            assert result["success"] is True
            assert result["page_number"] == 1
            assert "Extracted text from" in result["ocr_text"]
            assert result["average_confidence"] > 0
            assert result["word_count"] > 0

    @patch('pytesseract.image_to_string', side_effect=Exception("Tesseract failed"))
    def test_perform_ocr_on_image_failure(self, mock_image_to_string: Mock, ocr_tool: OCRProcessorTool, sample_image: np.ndarray) -> None:
        """Test OCR failure on image."""
        result = ocr_tool.perform_ocr_on_image(sample_image, 1)

        assert result["success"] is False
        assert "OCR processing failed" in result["error"]

    def test_detect_low_text_pages(self, ocr_tool: OCRProcessorTool) -> None:
        """Test detection of pages needing OCR."""
        text_content = [
            {"page_number": 1, "char_count": 150},  # Above threshold
            {"page_number": 2, "char_count": 50},   # Below threshold
            {"page_number": 3, "char_count": 200},  # Above threshold
            {"page_number": 4, "char_count": 25},   # Below threshold
        ]

        low_text_pages = ocr_tool.detect_low_text_pages(text_content, threshold=100)

        assert low_text_pages == [2, 4]

    @patch('fitz.open')
    def test_process_pdf_pages_success(self, mock_fitz_open: Mock, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test successful PDF pages OCR processing."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)  # 2 pages
        mock_fitz_open.return_value = mock_doc

        # Mock methods
        with patch.object(ocr_tool, 'extract_page_image') as mock_extract, \
             patch.object(ocr_tool, 'perform_ocr_on_image') as mock_ocr:

            # Mock successful image extraction
            mock_extract.return_value = {
                "success": True,
                "image": np.zeros((100, 100), dtype=np.uint8),
                "width": 100,
                "height": 100,
                "dpi": ocr_tool.dpi
            }

            # Mock successful OCR
            mock_ocr.return_value = {
                "success": True,
                "page_number": 1,
                "ocr_text": "Page text",
                "average_confidence": 85.0,
                "char_count": 9
            }

            result = ocr_tool.process_pdf_pages(sample_pdf_path, [1, 2])

            assert result["success"] is True
            assert result["successful_pages"] == 2
            assert result["total_pages_processed"] == 2
            assert len(result["ocr_results"]) == 2

    @patch('fitz.open')
    def test_process_pdf_pages_partial_success(self, mock_fitz_open: Mock, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test PDF pages processing with partial success."""
        # Mock PyMuPDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_fitz_open.return_value = mock_doc

        with patch.object(ocr_tool, 'extract_page_image') as mock_extract, \
             patch.object(ocr_tool, 'perform_ocr_on_image') as mock_ocr:

            # Mock mixed results
            def side_effect_extract(doc, page_num):
                if page_num == 0:  # First page succeeds
                    return {
                        "success": True,
                        "image": np.zeros((100, 100), dtype=np.uint8),
                        "width": 100,
                        "height": 100,
                        "dpi": ocr_tool.dpi
                    }
                else:  # Second page fails
                    return {
                        "success": False,
                        "error": "Image extraction failed"
                    }

            mock_extract.side_effect = side_effect_extract
            mock_ocr.return_value = {
                "success": True,
                "page_number": 1,
                "ocr_text": "Page text",
                "average_confidence": 85.0,
                "char_count": 9
            }

            result = ocr_tool.process_pdf_pages(sample_pdf_path, [1, 2])

            assert result["success"] is True
            assert result["successful_pages"] == 1
            assert result["failed_pages"] == 1

    def test_process_pdf_pages_invalid_pages(self, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test PDF processing with invalid page numbers."""
        with patch('fitz.open') as mock_fitz_open:
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=2)  # Only 2 pages
            mock_fitz_open.return_value = mock_doc

            # Request processing of pages that don't exist
            result = ocr_tool.process_pdf_pages(sample_pdf_path, [1, 2, 5, 10])

            # Should process only valid pages (1, 2)
            assert result["total_pages_processed"] == 2

    @patch('fitz.open', side_effect=Exception("PDF open failed"))
    def test_process_pdf_pages_failure(self, mock_fitz_open: Mock, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test PDF pages processing failure."""
        result = ocr_tool.process_pdf_pages(sample_pdf_path, [1])

        assert result["success"] is False
        assert "OCR processing failed" in result["error"]

    def test_process_document_with_text_analysis_no_ocr_needed(self, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test document processing when no OCR is needed."""
        # All pages have sufficient text
        text_content = [
            {"page_number": 1, "char_count": 500},
            {"page_number": 2, "char_count": 300}
        ]

        result = ocr_tool.process_document_with_text_analysis(sample_pdf_path, text_content)

        assert result["success"] is True
        assert result["ocr_performed"] is False
        assert result["pages_needing_ocr"] == []
        assert "not needed" in result["message"]

    def test_process_document_with_text_analysis_ocr_needed(self, ocr_tool: OCRProcessorTool, sample_pdf_path: str) -> None:
        """Test document processing when OCR is needed."""
        # Some pages have low text content
        text_content = [
            {"page_number": 1, "char_count": 500},  # Above threshold
            {"page_number": 2, "char_count": 50}    # Below threshold
        ]

        with patch.object(ocr_tool, 'process_pdf_pages') as mock_process:
            mock_process.return_value = {
                "success": True,
                "successful_pages": 1,
                "ocr_results": [{"page_number": 2, "ocr_text": "OCR text"}]
            }

            result = ocr_tool.process_document_with_text_analysis(sample_pdf_path, text_content, char_threshold=100)

            assert result["success"] is True
            assert result["ocr_performed"] is True
            assert result["pages_needing_ocr"] == [2]
            assert result["char_threshold_used"] == 100
