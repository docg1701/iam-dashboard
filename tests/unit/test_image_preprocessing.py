"""Unit tests for OpenCV preprocessing functions."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.document_preprocessing import (
    DocumentPreprocessor,
    get_document_preprocessor,
)


class TestDocumentPreprocessor:
    """Unit tests for document preprocessing service."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance for testing."""
        return DocumentPreprocessor()

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a simple grayscale image
        return np.random.randint(0, 255, (400, 600), dtype=np.uint8)

    @pytest.fixture
    def sample_color_image(self):
        """Create a sample color image for testing."""
        # Create a simple color image (BGR format)
        return np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)

    def test_preprocess_image_grayscale_input(self, preprocessor, sample_image):
        """Test preprocessing with grayscale input image."""
        # Act
        result = preprocessor.preprocess_image_for_ocr(sample_image)

        # Assert
        assert result is not None
        assert len(result.shape) == 2  # Should be grayscale
        # Note: Dimensions may change due to DPI normalization (upscaling for better OCR)
        assert result.shape[0] >= sample_image.shape[0]  # Height may increase
        assert result.shape[1] >= sample_image.shape[1]  # Width may increase

    @patch("app.services.document_preprocessing.cv2.cvtColor")
    @patch("app.services.document_preprocessing.cv2.GaussianBlur")
    @patch("app.services.document_preprocessing.cv2.threshold")
    @patch("app.services.document_preprocessing.cv2.morphologyEx")
    def test_preprocess_image_color_input(
        self,
        mock_morph,
        mock_threshold,
        mock_blur,
        mock_cvt,
        preprocessor,
        sample_color_image,
    ):
        """Test preprocessing with color input image."""
        # Arrange
        mock_cvt.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_blur.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_threshold.return_value = (127, np.ones((400, 600), dtype=np.uint8))
        mock_morph.return_value = np.ones((400, 600), dtype=np.uint8)

        # Act
        preprocessor.preprocess_image_for_ocr(sample_color_image)

        # Assert
        mock_cvt.assert_called_once()
        mock_blur.assert_called_once()
        mock_threshold.assert_called_once()
        mock_morph.assert_called_once()

    @patch("app.services.document_preprocessing.cv2.GaussianBlur")
    @patch("app.services.document_preprocessing.cv2.threshold")
    @patch("app.services.document_preprocessing.cv2.morphologyEx")
    @patch("app.services.document_preprocessing.cv2.resize")
    def test_gaussian_blur_applied(
        self,
        mock_resize,
        mock_morph,
        mock_threshold,
        mock_blur,
        preprocessor,
        sample_image,
    ):
        """Test that Gaussian blur is applied for noise reduction."""
        # Arrange
        mock_blur.return_value = sample_image
        mock_threshold.return_value = (127, sample_image)
        mock_morph.return_value = sample_image
        mock_resize.return_value = sample_image

        # Act
        preprocessor.preprocess_image_for_ocr(sample_image)

        # Assert
        mock_blur.assert_called_once()
        # Verify it was called with correct parameters (kernel size and sigma)
        args, kwargs = mock_blur.call_args
        assert args[1] == (5, 5)  # kernel size
        assert args[2] == 0  # sigma

    @patch("app.services.document_preprocessing.cv2.threshold")
    def test_otsu_thresholding_applied(
        self, mock_threshold, preprocessor, sample_image
    ):
        """Test that THRESH_BINARY + THRESH_OTSU thresholding is applied."""
        # Arrange
        import cv2

        mock_threshold.return_value = (127, sample_image)

        # Act
        with patch(
            "app.services.document_preprocessing.cv2.GaussianBlur",
            return_value=sample_image,
        ):
            preprocessor.preprocess_image_for_ocr(sample_image)

        # Assert
        mock_threshold.assert_called_once()
        args, kwargs = mock_threshold.call_args
        assert args[1] == 0  # threshold value
        assert args[2] == 255  # max value
        assert args[3] == cv2.THRESH_BINARY + cv2.THRESH_OTSU

    @patch("app.services.document_preprocessing.cv2.morphologyEx")
    @patch("app.services.document_preprocessing.cv2.getStructuringElement")
    def test_morphological_operations_applied(
        self, mock_get_kernel, mock_morph, preprocessor, sample_image
    ):
        """Test that morphological operations are applied for character connection."""
        # Arrange
        import cv2

        mock_kernel = np.ones((2, 2), np.uint8)
        mock_get_kernel.return_value = mock_kernel
        mock_morph.return_value = sample_image

        # Act
        with patch(
            "app.services.document_preprocessing.cv2.GaussianBlur",
            return_value=sample_image,
        ):
            with patch(
                "app.services.document_preprocessing.cv2.threshold",
                return_value=(127, sample_image),
            ):
                preprocessor.preprocess_image_for_ocr(sample_image)

        # Assert
        mock_get_kernel.assert_called_once_with(cv2.MORPH_RECT, (2, 2))
        mock_morph.assert_called_once_with(sample_image, cv2.MORPH_CLOSE, mock_kernel)

    @patch("app.services.document_preprocessing.cv2.resize")
    def test_dpi_normalization_upscaling(self, mock_resize, preprocessor):
        """Test DPI normalization when image needs upscaling."""
        # Arrange
        # Create a small image that would need upscaling
        small_image = np.ones((100, 150), dtype=np.uint8)
        mock_resize.return_value = np.ones((300, 450), dtype=np.uint8)

        # Act
        with patch(
            "app.services.document_preprocessing.cv2.GaussianBlur",
            return_value=small_image,
        ):
            with patch(
                "app.services.document_preprocessing.cv2.threshold",
                return_value=(127, small_image),
            ):
                with patch(
                    "app.services.document_preprocessing.cv2.morphologyEx",
                    return_value=small_image,
                ):
                    preprocessor.preprocess_image_for_ocr(small_image)

        # Assert - resize should be called for upscaling
        mock_resize.assert_called_once()

    def test_estimate_dpi_calculation(self, preprocessor):
        """Test DPI estimation logic."""
        # Arrange
        test_image = np.ones((2479, 1753), dtype=np.uint8)  # Roughly A4 at 300 DPI

        # Act
        dpi = preprocessor._estimate_dpi(test_image)

        # Assert
        assert dpi > 200  # Should estimate reasonable DPI
        assert dpi < 400

    def test_estimate_dpi_minimum_threshold(self, preprocessor):
        """Test that DPI estimation has minimum threshold."""
        # Arrange
        tiny_image = np.ones((50, 50), dtype=np.uint8)

        # Act
        dpi = preprocessor._estimate_dpi(tiny_image)

        # Assert
        assert dpi >= 72  # Minimum DPI threshold

    @patch("app.services.document_preprocessing.fitz.open")
    @patch("app.services.document_preprocessing.pytesseract.image_to_string")
    def test_extract_text_from_complex_document(
        self, mock_tesseract, mock_fitz_open, preprocessor, tmp_path
    ):
        """Test OCR text extraction from complex documents."""
        # Arrange
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pix = MagicMock()
        mock_pix.tobytes.return_value = b"fake_png_data"
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        mock_tesseract.return_value = "Extracted text from PDF"

        # Act
        with patch("app.services.document_preprocessing.Image.open"):
            with patch("app.services.document_preprocessing.cv2.cvtColor"):
                result = preprocessor.extract_text_from_complex_document(pdf_path)

        # Assert
        assert "Extracted text from PDF" in result
        mock_tesseract.assert_called()

    @patch("app.services.document_preprocessing.fitz.open")
    def test_is_complex_document_simple_case(
        self, mock_fitz_open, preprocessor, tmp_path
    ):
        """Test document complexity classification for simple documents."""
        # Arrange
        pdf_path = tmp_path / "simple.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "A" * 1500  # Lots of extractable text
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        # Act
        result = preprocessor.is_complex_document(pdf_path)

        # Assert
        assert result is False  # Should be classified as simple

    @patch("app.services.document_preprocessing.fitz.open")
    def test_is_complex_document_complex_case(
        self, mock_fitz_open, preprocessor, tmp_path
    ):
        """Test document complexity classification for complex documents."""
        # Arrange
        pdf_path = tmp_path / "complex.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")

        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""  # No extractable text (scanned image)
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        # Act
        result = preprocessor.is_complex_document(pdf_path)

        # Assert
        assert result is True  # Should be classified as complex

    def test_preprocessing_error_handling(self, preprocessor):
        """Test that preprocessing handles errors gracefully."""
        # Arrange
        invalid_image = "not an image"

        # Act
        result = preprocessor.preprocess_image_for_ocr(invalid_image)

        # Assert
        assert result == invalid_image  # Should return original on error

    def test_factory_function(self):
        """Test factory function returns DocumentPreprocessor instance."""
        # Act
        result = get_document_preprocessor()

        # Assert
        assert isinstance(result, DocumentPreprocessor)

    def test_tesseract_portuguese_configuration(self, preprocessor, tmp_path):
        """Test that Tesseract is configured for Portuguese legal documents."""
        # This test would verify OCR configuration
        # Implementation depends on actual OCR integration
        pass
