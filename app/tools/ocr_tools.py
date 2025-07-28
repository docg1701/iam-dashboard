"""OCR processing tools for image-based PDF documents using PyTesseract and OpenCV."""

import io
import logging
from typing import Any

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRProcessorTool:
    """Tool for performing OCR on image-based PDF documents."""

    def __init__(
        self,
        min_confidence: float = 50.0,
        dpi: int = 300,
        preprocessing: bool = True
    ) -> None:
        """Initialize the OCR processor tool.

        Args:
            min_confidence: Minimum confidence score for OCR results
            dpi: DPI for image rendering from PDF
            preprocessing: Whether to apply image preprocessing
        """
        self.min_confidence = min_confidence
        self.dpi = dpi
        self.preprocessing = preprocessing

        # OCR configuration
        self.tesseract_config = r'--oem 3 --psm 6'

    def validate_dependencies(self) -> dict[str, Any]:
        """Validate that required OCR dependencies are available.

        Returns:
            Dictionary containing validation results
        """
        try:
            # Check Tesseract
            tesseract_version = pytesseract.get_tesseract_version()

            # Check OpenCV
            opencv_version = cv2.__version__

            # Check PIL
            pil_version = Image.__version__

            return {
                "valid": True,
                "dependencies": {
                    "tesseract": str(tesseract_version),
                    "opencv": opencv_version,
                    "pillow": pil_version
                }
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"OCR dependencies validation failed: {str(e)}"
            }

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Apply preprocessing to improve OCR accuracy.

        Args:
            image: Input image as numpy array

        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

            return processed

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}, using original image")
            return image

    def extract_page_image(self, doc: fitz.Document, page_num: int) -> dict[str, Any]:
        """Extract page as image from PDF document.

        Args:
            doc: PyMuPDF document object
            page_num: Page number (0-indexed)

        Returns:
            Dictionary containing page image and metadata
        """
        try:
            page = doc.load_page(page_num)

            # Create transformation matrix for high DPI
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)

            # Render page as image
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(img_data))

            # Convert to numpy array for OpenCV processing
            np_image = np.array(pil_image)

            result = {
                "success": True,
                "image": np_image,
                "pil_image": pil_image,
                "width": pix.width,
                "height": pix.height,
                "page_number": page_num + 1,
                "dpi": self.dpi
            }

            pix = None  # Free memory
            return result

        except Exception as e:
            error_msg = f"Failed to extract image from page {page_num + 1}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "page_number": page_num + 1
            }

    def perform_ocr_on_image(self, image: np.ndarray, page_number: int) -> dict[str, Any]:
        """Perform OCR on a single image.

        Args:
            image: Image as numpy array
            page_number: Page number for logging

        Returns:
            Dictionary containing OCR results
        """
        try:
            # Apply preprocessing if enabled
            if self.preprocessing:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image

            # Convert numpy array to PIL Image for Tesseract
            if processed_image.dtype != np.uint8:
                processed_image = processed_image.astype(np.uint8)

            pil_image = Image.fromarray(processed_image)

            # Perform OCR with confidence scores
            ocr_data = pytesseract.image_to_data(
                pil_image,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )

            # Extract text with confidence filtering
            filtered_text = []
            word_confidences = []

            for i, confidence in enumerate(ocr_data['conf']):
                if int(confidence) >= self.min_confidence:
                    text = ocr_data['text'][i].strip()
                    if text:
                        filtered_text.append(text)
                        word_confidences.append(int(confidence))

            # Get full text without confidence filtering for backup
            full_text = pytesseract.image_to_string(pil_image, config=self.tesseract_config)

            # Calculate statistics
            avg_confidence = sum(word_confidences) / len(word_confidences) if word_confidences else 0

            result = {
                "success": True,
                "page_number": page_number,
                "ocr_text": " ".join(filtered_text),
                "full_text": full_text,
                "average_confidence": avg_confidence,
                "word_count": len(filtered_text),
                "total_words": len([w for w in ocr_data['text'] if w.strip()]),
                "confidence_threshold": self.min_confidence,
                "char_count": len(" ".join(filtered_text)),
                "preprocessing_applied": self.preprocessing
            }

            logger.info(f"OCR completed for page {page_number}: {len(filtered_text)} words, {avg_confidence:.1f}% avg confidence")
            return result

        except Exception as e:
            error_msg = f"OCR processing failed for page {page_number}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "page_number": page_number
            }

    def detect_low_text_pages(self, text_content: list[dict[str, Any]], threshold: int = 100) -> list[int]:
        """Detect pages that likely need OCR based on low text content.

        Args:
            text_content: List of page text data from PDFReaderTool
            threshold: Character count threshold for "low text" pages

        Returns:
            List of page numbers (1-indexed) that need OCR
        """
        low_text_pages = []

        for page_data in text_content:
            char_count = page_data.get("char_count", 0)
            page_number = page_data.get("page_number", 0)

            if char_count < threshold:
                low_text_pages.append(page_number)

        logger.info(f"Detected {len(low_text_pages)} pages needing OCR (< {threshold} chars)")
        return low_text_pages

    def process_pdf_pages(
        self,
        file_path: str,
        pages_to_process: list[int] | None = None
    ) -> dict[str, Any]:
        """Process specified PDF pages with OCR.

        Args:
            file_path: Path to the PDF file
            pages_to_process: List of page numbers to process (1-indexed), None for all pages

        Returns:
            Dictionary containing OCR results for all processed pages
        """
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)

            # Determine which pages to process
            if pages_to_process is None:
                pages_to_process = list(range(1, total_pages + 1))

            # Filter out invalid page numbers
            valid_pages = [p for p in pages_to_process if 1 <= p <= total_pages]

            if len(valid_pages) != len(pages_to_process):
                logger.warning(f"Some page numbers were invalid and skipped: {file_path}")

            ocr_results = []
            successful_pages = 0

            for page_num in valid_pages:
                # Extract page as image
                image_result = self.extract_page_image(doc, page_num - 1)  # Convert to 0-indexed

                if not image_result["success"]:
                    ocr_results.append({
                        "success": False,
                        "page_number": page_num,
                        "error": image_result["error"]
                    })
                    continue

                # Perform OCR on the image
                ocr_result = self.perform_ocr_on_image(image_result["image"], page_num)

                # Add image metadata to OCR result
                if ocr_result["success"]:
                    ocr_result.update({
                        "image_width": image_result["width"],
                        "image_height": image_result["height"],
                        "image_dpi": image_result["dpi"]
                    })
                    successful_pages += 1

                ocr_results.append(ocr_result)

            doc.close()

            # Calculate summary statistics
            total_ocr_text = ""
            total_confidence_scores = []

            for result in ocr_results:
                if result.get("success"):
                    total_ocr_text += " " + result.get("ocr_text", "")
                    if result.get("average_confidence", 0) > 0:
                        total_confidence_scores.append(result["average_confidence"])

            overall_confidence = sum(total_confidence_scores) / len(total_confidence_scores) if total_confidence_scores else 0

            final_result = {
                "success": True,
                "file_path": file_path,
                "total_pages_processed": len(valid_pages),
                "successful_pages": successful_pages,
                "failed_pages": len(valid_pages) - successful_pages,
                "ocr_results": ocr_results,
                "summary": {
                    "total_ocr_chars": len(total_ocr_text.strip()),
                    "overall_confidence": overall_confidence,
                    "confidence_threshold_used": self.min_confidence,
                    "preprocessing_enabled": self.preprocessing
                }
            }

            logger.info(f"OCR processing completed for {file_path}: {successful_pages}/{len(valid_pages)} pages successful")
            return final_result

        except Exception as e:
            error_msg = f"OCR processing failed for {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path
            }

    def process_document_with_text_analysis(
        self,
        file_path: str,
        existing_text_content: list[dict[str, Any]],
        char_threshold: int = 100
    ) -> dict[str, Any]:
        """Process document with OCR based on existing text analysis.

        Args:
            file_path: Path to the PDF file
            existing_text_content: Text content from PDFReaderTool
            char_threshold: Character threshold for detecting low-text pages

        Returns:
            Dictionary containing OCR results and analysis
        """
        logger.info(f"Starting OCR analysis for document: {file_path}")

        # Detect pages that need OCR
        pages_needing_ocr = self.detect_low_text_pages(existing_text_content, char_threshold)

        if not pages_needing_ocr:
            logger.info(f"No pages need OCR in document: {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "pages_needing_ocr": [],
                "ocr_performed": False,
                "message": "All pages have sufficient text content, OCR not needed"
            }

        # Process pages with OCR
        ocr_result = self.process_pdf_pages(file_path, pages_needing_ocr)

        if ocr_result["success"]:
            ocr_result.update({
                "pages_needing_ocr": pages_needing_ocr,
                "ocr_performed": True,
                "char_threshold_used": char_threshold
            })

        return ocr_result
