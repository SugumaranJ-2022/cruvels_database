"""
Unit tests for document ingestor exceptions and hashing.
"""

import os
import pytest

from src.ingestion.exceptions import UnsupportedFileTypeError
from src.ingestion.ingestor import compute_content_hash, ingest_document


def test_compute_content_hash():
    text1 = "  Supreme Court  of   India \n Decision "
    text2 = "Supreme Court of India Decision"
    assert compute_content_hash(text1) == compute_content_hash(text2)


def test_non_pdf_file_raises_exception(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello World")

    with pytest.raises(UnsupportedFileTypeError):
        ingest_document(str(txt_file), source="test")
