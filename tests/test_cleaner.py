"""
Unit tests for text cleaner: repeated headers/footers, OCR edge cases, unicode normalization.
"""

from src.ingestion.cleaner import clean_text


def test_repeated_headers_and_footers():
    page1 = "HIGH COURT OF DELHI\nPage 1 of 2\n\nJUDGMENT\nThis is the content of page 1.\n\nConfidential Document"
    page2 = "HIGH COURT OF DELHI\nPage 2 of 2\n\nJUDGMENT\nThis is the content of page 2.\n\nConfidential Document"
    raw_text = page1 + "\n\n" + page2

    cleaned, log = clean_text(raw_text, page_texts=[page1, page2])
    assert "HIGH COURT OF DELHI" not in cleaned
    assert "Confidential Document" not in cleaned
    assert "This is the content of page 1." in cleaned
    assert "This is the content of page 2." in cleaned
    assert any("Removed repeating header" in entry for entry in log)
    assert any("Removed repeating footer" in entry for entry in log)


def test_unicode_normalization_and_quotes():
    raw_text = "Section 73 – Indian Contract Act… “Damages” & ‘Breach’"
    cleaned, log = clean_text(raw_text)
    assert "-" in cleaned
    assert '"Damages"' in cleaned
    assert "'Breach'" in cleaned
    assert any("Normalized quote and dash" in entry for entry in log)


def test_ocr_correction_numeric_context():
    # OCR 'O' and 'l' inside numeric sequences
    raw_text = "F.I.R. No. 2O24 under Section 7l of Act 1O0"
    cleaned, log = clean_text(raw_text)
    assert "2024" in cleaned
    assert "71" in cleaned
    assert "100" in cleaned
    assert any("OCR" in entry for entry in log)


def test_ocr_correction_does_not_corrupt_legitimate_words():
    # Legitimate English words containing 'l', 'O', 'rn' must NOT be altered!
    raw_text = "The court will learn from previous orders in this room and legal opinion."
    cleaned, log = clean_text(raw_text)
    assert "learn" in cleaned
    assert "orders" in cleaned
    assert "room" in cleaned
    assert "legal" in cleaned
    assert "opinion" in cleaned
