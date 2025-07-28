"""PDF processing tools for document text extraction and metadata parsing."""

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFReaderTool:
    """Tool for extracting text and metadata from PDF documents using PyMuPDF."""

    def __init__(self, max_file_size_mb: int = 50) -> None:
        """Initialize the PDF reader tool.

        Args:
            max_file_size_mb: Maximum file size to process in megabytes
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def validate_file(self, file_path: str) -> dict[str, Any]:
        """Validate PDF file before processing.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing validation results
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return {
                    "valid": False,
                    "error": f"File does not exist: {file_path}"
                }

            if not path.is_file():
                return {
                    "valid": False,
                    "error": f"Path is not a file: {file_path}"
                }

            if path.suffix.lower() != '.pdf':
                return {
                    "valid": False,
                    "error": f"File is not a PDF: {file_path}"
                }

            file_size = path.stat().st_size
            if file_size > self.max_file_size_bytes:
                return {
                    "valid": False,
                    "error": f"File too large: {file_size / 1024 / 1024:.1f}MB > {self.max_file_size_mb}MB"
                }

            # Try to open with PyMuPDF to check if it's a valid PDF
            try:
                doc = fitz.open(file_path)
                page_count = len(doc)
                doc.close()

                return {
                    "valid": True,
                    "file_size": file_size,
                    "page_count": page_count
                }
            except Exception as pdf_error:
                return {
                    "valid": False,
                    "error": f"Invalid PDF file: {str(pdf_error)}"
                }

        except Exception as e:
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata
        """
        try:
            doc = fitz.open(file_path)

            metadata = doc.metadata
            page_count = len(doc)

            # Get additional document information
            doc_info = {
                "page_count": page_count,
                "is_encrypted": doc.needs_pass,
                "has_toc": len(doc.get_toc()) > 0,
                "file_size": Path(file_path).stat().st_size
            }

            # Analyze page sizes and orientations
            page_info = []
            for page_num in range(min(page_count, 10)):  # Analyze first 10 pages
                page = doc.load_page(page_num)
                rect = page.rect
                page_info.append({
                    "page_number": page_num + 1,
                    "width": rect.width,
                    "height": rect.height,
                    "rotation": page.rotation
                })

            doc.close()

            result = {
                "success": True,
                "metadata": metadata,
                "document_info": doc_info,
                "page_info": page_info,
                "file_path": file_path
            }

            logger.info(f"Successfully extracted metadata from PDF: {file_path}")
            return result

        except Exception as e:
            error_msg = f"Failed to extract metadata from {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path
            }

    def extract_text_content(self, file_path: str, include_annotations: bool = True) -> dict[str, Any]:
        """Extract text content from PDF document.

        Args:
            file_path: Path to the PDF file
            include_annotations: Whether to include annotations and comments

        Returns:
            Dictionary containing extracted text content
        """
        try:
            doc = fitz.open(file_path)

            text_content = []
            total_chars = 0

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Extract main text
                text = page.get_text()
                char_count = len(text)
                total_chars += char_count

                page_data = {
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": char_count,
                    "has_images": len(page.get_images()) > 0,
                    "has_tables": self._detect_tables(page),
                }

                # Extract annotations if requested
                if include_annotations:
                    annotations = []
                    for annot in page.annots():
                        try:
                            annotation_data = {
                                "type": annot.type[1],  # Get type name
                                "content": annot.content,
                                "author": annot.info.get("title", ""),
                                "rect": list(annot.rect)
                            }
                            annotations.append(annotation_data)
                        except Exception as annot_error:
                            logger.warning(f"Failed to extract annotation: {str(annot_error)}")
                            continue

                    page_data["annotations"] = annotations

                text_content.append(page_data)

            doc.close()

            result = {
                "success": True,
                "text_content": text_content,
                "total_pages": len(text_content),
                "total_chars": total_chars,
                "average_chars_per_page": total_chars / len(text_content) if text_content else 0,
                "file_path": file_path
            }

            logger.info(f"Successfully extracted text from PDF: {file_path} ({len(text_content)} pages, {total_chars} chars)")
            return result

        except Exception as e:
            error_msg = f"Failed to extract text from {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path
            }

    def _detect_tables(self, page: fitz.Page) -> bool:
        """Simple table detection based on text arrangement.

        Args:
            page: PyMuPDF page object

        Returns:
            True if tables are likely present
        """
        try:
            # Get text blocks with positions
            blocks = page.get_text("dict")["blocks"]

            # Simple heuristic: look for aligned text blocks
            y_positions = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        y_positions.append(line["bbox"][1])  # y-coordinate

            # If many text elements share similar y-coordinates, likely a table
            if len(y_positions) > 10:
                # Count how many elements share similar y-positions (within 5 points)
                alignment_count = 0
                for i, y1 in enumerate(y_positions):
                    similar_count = sum(1 for y2 in y_positions[i+1:] if abs(y1 - y2) < 5)
                    if similar_count > 2:
                        alignment_count += 1

                return alignment_count > 3

            return False

        except Exception:
            return False

    def extract_images_info(self, file_path: str) -> dict[str, Any]:
        """Extract information about images in the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing image information
        """
        try:
            doc = fitz.open(file_path)

            images_info = []
            total_images = 0

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                images = page.get_images()

                page_images = []
                for img_index, img in enumerate(images):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)

                        image_info = {
                            "image_index": img_index,
                            "xref": xref,
                            "width": pix.width,
                            "height": pix.height,
                            "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                            "bpp": pix.n,  # bits per pixel
                            "size_estimate": pix.width * pix.height * pix.n
                        }

                        page_images.append(image_info)
                        pix = None  # Free memory

                    except Exception as img_error:
                        logger.warning(f"Failed to analyze image {img_index} on page {page_num + 1}: {str(img_error)}")
                        continue

                if page_images:
                    images_info.append({
                        "page_number": page_num + 1,
                        "image_count": len(page_images),
                        "images": page_images
                    })
                    total_images += len(page_images)

            doc.close()

            result = {
                "success": True,
                "total_images": total_images,
                "images_by_page": images_info,
                "file_path": file_path
            }

            logger.info(f"Successfully analyzed images in PDF: {file_path} ({total_images} images)")
            return result

        except Exception as e:
            error_msg = f"Failed to extract image info from {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "file_path": file_path
            }

    def process_document(self, file_path: str, include_annotations: bool = True) -> dict[str, Any]:
        """Complete PDF processing workflow.

        Args:
            file_path: Path to the PDF file
            include_annotations: Whether to include annotations

        Returns:
            Dictionary containing all extracted information
        """
        logger.info(f"Starting PDF processing for: {file_path}")

        # Step 1: Validate file
        validation = self.validate_file(file_path)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "file_path": file_path
            }

        # Step 2: Extract metadata
        metadata_result = self.extract_metadata(file_path)
        if not metadata_result["success"]:
            return metadata_result

        # Step 3: Extract text content
        text_result = self.extract_text_content(file_path, include_annotations)
        if not text_result["success"]:
            return text_result

        # Step 4: Extract image information
        images_result = self.extract_images_info(file_path)
        # Don't fail if image extraction fails, just log and continue
        if not images_result["success"]:
            logger.warning(f"Failed to extract image info: {images_result.get('error', 'Unknown error')}")
            images_result = {"success": True, "total_images": 0, "images_by_page": []}

        # Combine all results
        result = {
            "success": True,
            "file_path": file_path,
            "validation": validation,
            "metadata": metadata_result["metadata"],
            "document_info": metadata_result["document_info"],
            "page_info": metadata_result["page_info"],
            "text_content": text_result["text_content"],
            "text_summary": {
                "total_pages": text_result["total_pages"],
                "total_chars": text_result["total_chars"],
                "average_chars_per_page": text_result["average_chars_per_page"]
            },
            "images_info": {
                "total_images": images_result["total_images"],
                "images_by_page": images_result["images_by_page"]
            }
        }

        logger.info(f"PDF processing completed successfully for: {file_path}")
        return result
