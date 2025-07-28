"""PDF Processor Plugin registration and initialization."""

import logging
from typing import Any

from app.agents.base_agent import plugin_registry
from app.agents.pdf_processor_agent import PDFProcessorPlugin

logger = logging.getLogger(__name__)


def register_plugin() -> None:
    """Register the PDF Processor Plugin with the plugin registry."""
    try:
        plugin_registry.register_plugin(PDFProcessorPlugin)
        logger.info("Successfully registered PDFProcessorPlugin")
    except Exception as e:
        logger.error(f"Failed to register PDFProcessorPlugin: {str(e)}")
        raise


def get_plugin_info() -> dict[str, Any]:
    """Get information about the PDF Processor Plugin."""
    return {
        "name": "PDFProcessorPlugin",
        "version": "1.0.0",
        "description": "Autonomous agent for PDF document processing with OCR and vector storage",
        "capabilities": [
            "pdf_text_extraction",
            "ocr_processing",
            "vector_embedding_generation",
            "document_storage",
            "metadata_extraction"
        ],
        "dependencies": [],
        "supported_file_types": ["pdf"],
        "configuration": {
            "model": "gemini-1.5-flash",
            "max_file_size_mb": 50,
            "chunk_size": 1000,
            "perform_ocr": True
        }
    }


# Auto-register the plugin when this module is imported
register_plugin()
