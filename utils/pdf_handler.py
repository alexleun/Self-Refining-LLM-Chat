import os
import re
import requests
from pdfminer.high_level import extract_text
from utils.helpers import sanitize_filename

def fetch_and_split_pdf(url: str, project_id: str, chunk_size: int = 5000) -> list:
    """
    Download a PDF, save locally, extract text, and split into chunks.
    Returns a list of evidence dicts, one per chunk.
    """
    try:
        # Safe filename from URL
        base = url.split("/")[-1] or "document"
        safe_base = sanitize_filename(base, max_len=80)
        pdf_path = os.path.join(project_id, "evidence", safe_base)

        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Download PDF
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(pdf_path, "wb") as f:
            f.write(resp.content)

        # Extract text
        text = extract_text(pdf_path)

        # Split into chunks
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            chunk_id = f"{safe_base}_chunk{i//chunk_size+1}.json"
            chunk_path = os.path.join(project_id, "evidence", chunk_id)

            evidence = {
                "type": "pdf",
                "url": url,
                "path": pdf_path,
                "chunk_index": i//chunk_size+1,
                "text": chunk_text,
                "length": len(chunk_text)
            }

            # Save chunk as JSON
            with open(chunk_path, "w", encoding="utf-8") as f:
                import json
                json.dump(evidence, f, ensure_ascii=False, indent=2)

            chunks.append(evidence)

        return chunks

    except Exception as e:
        return [{
            "type": "pdf",
            "url": url,
            "error": str(e)
        }]