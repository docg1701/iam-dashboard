"""Document preprocessing service for OCR preparation using OpenCV."""

import io
import logging
from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class DocumentPreprocessor:
    """Handles document preprocessing for OCR using OpenCV."""

    def __init__(self):
        """Initialize the document preprocessor."""
        self.min_dpi = 300
        self.target_dpi = 300

    def preprocess_image_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess an image for better OCR results using OpenCV.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image optimized for OCR
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Step 1: Noise reduction using Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Step 2: Adaptive thresholding for better binarization
            # Use THRESH_BINARY + THRESH_OTSU for automatic threshold selection
            _, binary = cv2.threshold(
                blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Step 3: Morphological operations to connect broken characters
            # Use MORPH_CLOSE to connect nearby characters
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Step 4: DPI normalization - resize if needed
            height, width = morphed.shape
            current_dpi = self._estimate_dpi(morphed)

            if current_dpi < self.min_dpi:
                scale_factor = self.target_dpi / current_dpi
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)

                # Use INTER_CUBIC for better quality when upscaling
                morphed = cv2.resize(
                    morphed, (new_width, new_height), interpolation=cv2.INTER_CUBIC
                )
                logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")

            return morphed

        except Exception as e:
            logger.error(f"Error preprocessing image for OCR: {str(e)}")
            # Return original image if preprocessing fails
            return image

    def extract_text_from_complex_document(self, pdf_path: Path) -> str:
        """
        Extract text from complex documents using OCR with preprocessing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from all pages
        """
        try:
            extracted_text = []

            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)

            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]

                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom for better quality
                img_data = pix.tobytes("png")

                # Convert to OpenCV format
                pil_image = Image.open(io.BytesIO(img_data))
                cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                # Preprocess image for better OCR
                preprocessed = self.preprocess_image_for_ocr(cv_image)

                # Perform OCR using Tesseract
                try:
                    # Configure Tesseract for legal documents (Portuguese)
                    custom_config = r'--oem 3 --psm 6 -l por'
                    text = pytesseract.image_to_string(
                        preprocessed,
                        config=custom_config
                    )

                    if text.strip():
                        extracted_text.append(f"--- Página {page_num + 1} ---\n{text}")
                        logger.debug(f"Successfully extracted text from page {page_num + 1}")
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1}")

                except Exception as ocr_error:
                    logger.error(f"OCR failed for page {page_num + 1}: {str(ocr_error)}")
                    continue

            pdf_document.close()

            return "\n\n".join(extracted_text)

        except Exception as e:
            logger.error(f"Error extracting text from complex document {pdf_path}: {str(e)}")
            raise

    def _estimate_dpi(self, image: np.ndarray) -> float:
        """
        Estimate the DPI of an image based on its dimensions.
        
        Args:
            image: Input image
            
        Returns:
            Estimated DPI
        """
        height, width = image.shape[:2]

        # Rough estimation based on typical document sizes
        # Assume A4 page (8.27 x 11.69 inches)
        a4_width_inches = 8.27
        a4_height_inches = 11.69

        # Calculate DPI based on width and height, take the average
        dpi_width = width / a4_width_inches
        dpi_height = height / a4_height_inches

        estimated_dpi = (dpi_width + dpi_height) / 2

        # Ensure a reasonable minimum
        return max(estimated_dpi, 72)  # Minimum 72 DPI

    def is_complex_document(self, pdf_path: Path) -> bool:
        """
        Determine if a document is complex (requires Gemini OCR) or simple (can be processed locally).
        
        Strategy:
        1. First, try direct text extraction (fastest)
        2. If no text found, test OCR locally with Tesseract on first page
        3. If Tesseract extracts good text, classify as "simple" (process locally)
        4. Only classify as "complex" if Tesseract fails or extracts poor quality text
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if document requires Gemini OCR, False if can be processed locally
        """
        try:
            pdf_document = fitz.open(pdf_path)

            # Step 1: Try direct text extraction first
            pages_to_check = min(3, len(pdf_document))
            text_chars_found = 0
            total_chars_possible = 0

            for page_num in range(pages_to_check):
                page = pdf_document[page_num]

                # Try to extract text directly
                text = page.get_text()
                text_chars_found += len(text.strip())

                # Estimate total possible characters based on page size
                total_chars_possible += 2000  # Assume ~2000 chars per page for full text

            # If sufficient text is found directly, it's simple
            text_ratio = text_chars_found / total_chars_possible if total_chars_possible > 0 else 0
            if text_ratio >= 0.1:
                pdf_document.close()
                logger.info(f"Document {pdf_path.name} has direct text (ratio: {text_ratio:.2f}), classified as: simple")
                return False

            # Step 2: No direct text found, test local OCR capability
            logger.info(f"Document {pdf_path.name} has no direct text (ratio: {text_ratio:.2f}), testing local OCR...")

            # Test OCR on first page only (for performance)
            if len(pdf_document) > 0:
                try:
                    ocr_success = self._test_local_ocr_capability(pdf_document[0])
                    pdf_document.close()

                    if ocr_success:
                        logger.info(f"Document {pdf_path.name} OCR test successful, classified as: simple (local OCR)")
                        return False
                    else:
                        logger.info(f"Document {pdf_path.name} OCR test failed, classified as: complex (Gemini OCR)")
                        return True

                except Exception as ocr_error:
                    logger.warning(f"OCR test failed for {pdf_path.name}: {str(ocr_error)}, defaulting to: complex")
                    pdf_document.close()
                    return True

            pdf_document.close()
            logger.info(f"Document {pdf_path.name} has no pages, classified as: complex")
            return True

        except Exception as e:
            logger.error(f"Error analyzing document complexity for {pdf_path}: {str(e)}")
            # Default to complex if we can't determine
            return True

    def _test_local_ocr_capability(self, page) -> bool:
        """
        Test if local Tesseract OCR can extract good quality text from a page.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            True if OCR extracts readable text, False otherwise
        """
        try:
            # Convert page to image with reasonable quality
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x zoom
            img_data = pix.tobytes("png")

            # Convert to OpenCV format
            pil_image = Image.open(io.BytesIO(img_data))
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Apply basic preprocessing
            preprocessed = self.preprocess_image_for_ocr(cv_image)

            # Test OCR with Portuguese configuration
            custom_config = r'--oem 3 --psm 6 -l por'
            ocr_text = pytesseract.image_to_string(preprocessed, config=custom_config)

            # Evaluate OCR quality
            ocr_chars = len(ocr_text.strip())

            # Check for readable content (at least 50 characters and some words)
            if ocr_chars >= 50:
                words = ocr_text.split()
                # Look for meaningful words (at least 3 characters each)
                meaningful_words = [w for w in words if len(w.strip()) >= 3]

                if len(meaningful_words) >= 5:  # At least 5 meaningful words
                    logger.debug(f"OCR test successful: {ocr_chars} chars, {len(meaningful_words)} meaningful words")
                    return True

            logger.debug(f"OCR test failed: {ocr_chars} chars, insufficient quality")
            return False

        except Exception as e:
            logger.debug(f"OCR test error: {str(e)}")
            return False


def get_document_preprocessor() -> DocumentPreprocessor:
    """Factory function to get DocumentPreprocessor instance."""
    return DocumentPreprocessor()
