"""
Text cleaning and normalization pipeline with provenance logging and OCR error correction.
"""

from collections import Counter
import re
from typing import List, Tuple, Optional
import unicodedata


def clean_text(raw_text: str, page_texts: Optional[List[str]] = None) -> Tuple[str, List[str]]:
    """
    Clean raw text by stripping repeating headers/footers, normalizing unicode/whitespace,
    and performing context-sensitive OCR correction with audit logging.
    """
    cleaning_log: List[str] = []

    if not raw_text or not raw_text.strip():
        return "", ["Warning: Empty text input provided to cleaner"]

    # 1. Strip repeating headers/footers across pages
    pages = page_texts if page_texts else raw_text.split("\n\n")
    if len(pages) > 1:
        header_candidates: Counter = Counter()
        footer_candidates: Counter = Counter()

        for page in pages:
            lines = [line.strip() for line in page.split("\n") if line.strip()]
            if lines:
                header_candidates[lines[0]] += 1
                if len(lines) > 1:
                    footer_candidates[lines[-1]] += 1

        min_occurrences = max(2, int(len(pages) * 0.5))
        repeating_headers = {line for line, count in header_candidates.items() if count >= min_occurrences}
        repeating_footers = {line for line, count in footer_candidates.items() if count >= min_occurrences}

        cleaned_pages = []
        for idx, page in enumerate(pages):
            page_lines = page.split("\n")
            filtered_lines = []
            for line in page_lines:
                stripped_line = line.strip()
                if stripped_line in repeating_headers:
                    cleaning_log.append(f"Page {idx+1}: Removed repeating header '{stripped_line}'")
                    continue
                if stripped_line in repeating_footers:
                    cleaning_log.append(f"Page {idx+1}: Removed repeating footer '{stripped_line}'")
                    continue
                filtered_lines.append(line)
            cleaned_pages.append("\n".join(filtered_lines))
        text = "\n\n".join(cleaned_pages)
    else:
        text = raw_text

    # 2. Unicode normalization (NFKC)
    nfkc_text = unicodedata.normalize("NFKC", text)
    if nfkc_text != text:
        cleaning_log.append("Applied Unicode NFKC normalization")
        text = nfkc_text

    # 3. Quote and dash normalization
    quote_normalized = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("—", "-")
        .replace("–", "-")
        .replace("−", "-")
    )
    if quote_normalized != text:
        cleaning_log.append("Normalized quote and dash punctuation marks")
        text = quote_normalized

    # 4. Contextual OCR corrections (numbers and specific numeric prefixes ONLY)
    # Correct letter 'O' or 'o' to digit '0' inside numeric sequences (e.g., 2O24 -> 2024, 1O0 -> 100)
    ocr_o_pattern = re.compile(r"(\b\d+)[O|o](\d*\b)|(\b\d+)[O|o](\b)")
    matches_o = ocr_o_pattern.findall(text)
    if matches_o:
        text = re.sub(r"(\b\d+)[O|o](\d*\b)", r"\g<1>0\g<2>", text)
        text = re.sub(r"(\b\d+)[O|o](\b)", r"\g<1>0", text)
        cleaning_log.append(f"Corrected {len(matches_o)} OCR 'O/o' substitutions to '0' within digit sequences")

    # Correct lowercase 'l' to digit '1' inside numeric sequences (e.g., 2l -> 21, 7l -> 71, S.7l -> S.71)
    ocr_l_pattern = re.compile(r"(\d+)l(\d*)|(\bSec\.\s*\d+)l(\b)|(\bS\.\s*\d+)l(\b)")
    matches_l = ocr_l_pattern.findall(text)
    if matches_l:
        text = re.sub(r"(\d+)l(\d*)", r"\g<1>1\g<2>", text)
        text = re.sub(r"(\bSec\.\s*\d+)l(\b)", r"\g<1>1\g<2>", text)
        text = re.sub(r"(\bS\.\s*\d+)l(\b)", r"\g<1>1\g<2>", text)
        cleaning_log.append(f"Corrected {len(matches_l)} OCR 'l' substitutions to '1' within numeric contexts")

    # Correct 'rn' to 'm' ONLY in explicit numeric case/file patterns (e.g. F.I.R. No. rn/2020)
    ocr_rn_pattern = re.compile(r"(\bNo\.\s*)rn(/\d+)")
    matches_rn = ocr_rn_pattern.findall(text)
    if matches_rn:
        text = ocr_rn_pattern.sub(r"\g<1>m\g<2>", text)
        cleaning_log.append(f"Corrected {len(matches_rn)} OCR 'rn' substitutions to 'm' in case reference patterns")

    # 5. Whitespace normalization
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    normalized_text = "\n".join(lines)
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text).strip()
    
    if normalized_text != text:
        cleaning_log.append("Normalized consecutive whitespace and blank line breaks")
        text = normalized_text

    return text, cleaning_log
