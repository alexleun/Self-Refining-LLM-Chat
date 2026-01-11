import json
import logging
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS
from langchain_core.prompts import PromptTemplate

class Editor:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

        # Define a reusable prompt template
        self.prompt_template = PromptTemplate.from_template(
            "You are the Editor. Your task is to refine the section '{title}' for the overall query.\n\n"
            "Evidence snippets:\n{sources}\n\n"
            "Previous draft:\n{prev_draft}\n\n"
            "Audit feedback:\n{prev_audit}\n\n"
            "Critical questions:\n{prev_critical}\n\n"
            "Guidelines:\n"
            "- Begin with a Markdown heading for the section title\n"
            "- Improve clarity, completeness, and logical flow\n"
            "- Address issues flagged in the audit feedback\n"
            "- Incorporate answers or expansions suggested by critical questions\n"
            "- Use evidence snippets to strengthen arguments\n"
            "- Avoid repeating text verbatim; synthesize into a polished narrative\n"
            "- Write 2–3 well‑developed paragraphs"
        )

    def draft_section(self, section, sources, language_hint,
                      prev_draft="", prev_audit="", prev_critical="", max_tokens=None):
        """
        Refine or draft a section using evidence and previous round artifacts.
        Returns: Markdown draft string
        """
        sec_title = section.get("title")
        logging.info(f"[Editor] Drafting/refining section: {sec_title}")

        # Fill the template with values
        prompt = self.prompt_template.format(
            title=sec_title,
            sources=sources,
            prev_draft=prev_draft,
            prev_audit=prev_audit,
            prev_critical=prev_critical
        )

        try:
            # Keep the original LLM call unchanged
            draft = self.llm.query(prompt, role="editor", max_tokens=max_tokens)
        except Exception as e:
            logging.error(f"[Editor] LLM query failed: {e}")
            draft = f"### {sec_title}\n\n[Editor failed to generate draft]"

        return draft