import json
import logging
from utils.config import ROLE_PROMPTS
from utils.llm_interface import LLMInterface

class Planner:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def plan(self, user_query: str, max_tokens=None):
        # Build prompt from config
        prompt = f"{ROLE_PROMPTS['planner']}\n\nUser query: {user_query}"

        raw_reply = self.llm.query(prompt, role="planner", max_tokens=max_tokens)

        # --- Step 1: Try to parse JSON error ---
        try:
            parsed = json.loads(raw_reply)
            if "error" in parsed:
                logging.warning(f"[Planner] LLM returned error: {parsed['error']}")
                # Fallback: create generic sections
                return self._fallback_sections(user_query, parsed["error"])
        except Exception:
            pass  # Not JSON, continue

        # --- Step 2: Parse Markdown sections ---
        sections = self._parse_sections(raw_reply)
        if not sections:
            logging.warning("[Planner] No sections found, using fallback.")
            return self._fallback_sections(user_query, "No sections parsed")

        logging.info(f"[Planner] Parsed {len(sections)} sections.")
        return sections

    def _parse_sections(self, text: str):
        """Extract sections from Markdown-style planner output."""
        import re
        sections = []
        for match in re.finditer(r"##\s*(sec-\d+):?\s*(.+)", text):
            sec_id, title = match.groups()
            sections.append({
                "id": sec_id.strip(),
                "title": title.strip(),
                "content": text  # you may want to slice per-section content
            })
        return sections

    def _fallback_sections(self, user_query: str, reason: str):
        """Generate generic sections if LLM reply is unusable."""
        logging.info(f"[Planner] Fallback sections due to: {reason}")
        return [
            {"id": "sec-1", "title": "Context & Objective", "content": user_query},
            {"id": "sec-2", "title": "Evidence Gathering", "content": ""},
            {"id": "sec-3", "title": "Draft Development", "content": ""},
            {"id": "sec-4", "title": "Review & Audit", "content": ""},
        ]