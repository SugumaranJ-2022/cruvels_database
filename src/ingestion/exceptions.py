"""
Custom exception hierarchy for document ingestion and processing pipeline.
"""


class IngestionPipelineError(Exception):
    """Base exception for all ingestion pipeline errors."""
    pass


class UnsupportedFileTypeError(IngestionPipelineError):
    """Raised when an unsupported or non-PDF file type is encountered."""
    pass


class EmptyDocumentError(IngestionPipelineError):
    """Raised when a document contains no readable text content."""
    pass


class DuplicateDocumentError(IngestionPipelineError):
    """Raised when a document with identical content hash already exists."""
    def __init__(self, message: str, existing_document_id: str):
        super().__init__(message)
        self.existing_document_id = existing_document_id


class ExtractionFailedError(IngestionPipelineError):
    """Raised when structured LLM extraction fails after max retries."""
    pass
