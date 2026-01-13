import re
import logging

def normalize_section_draft(draft: str, section_title: str) -> str:
    """
    Normalize a section draft before integration:
    - Remove duplicate executive summaries
    - Strip per-section table of contents
    - Ensure consistent heading style
    - Trim excessive whitespace
    """
    if not draft:
        return f"## {section_title}\n\n[No draft available]"

    text = draft

    # Remove any "Executive Summary" headings
    text = re.sub(r"#* *Executive Summary.*", "", text, flags=re.IGNORECASE)

    # Remove "Table of Contents" blocks
    text = re.sub(r"#* *Table of Contents.*?(---|\n#)", "\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Ensure section heading at the top
    if not text.strip().startswith("##"):
        text = f"## {section_title}\n\n{text.strip()}"

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    logging.debug(f"[Normalizer] Normalized draft for section: {section_title}")
    return text.strip()