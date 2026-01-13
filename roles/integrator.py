import os
import json
import logging
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS
from utils.normalizer import normalize_section_draft


class Integrator:
    def __init__(self, llm: LLMInterface, tokens: int):
        self.llm = llm
        self.tokens = tokens

    def write_summary(self, sections: list, language_hint: str, max_tokens=None) -> str:
        """
        Generate an executive summary from all section drafts.
        """
        drafts = [s["draft"] for s in sections]
        prompt = (
            ROLE_PROMPTS['integrate_summary'] +
            f"Use {language_hint} write：\n" +
            json.dumps(drafts, ensure_ascii=False, indent=2)
        )
        return self.llm.query(prompt, role="executive", max_tokens=max_tokens)

    def integrate(self, sections: list, executive_summary: str,
                  language_hint: str, max_tokens=None) -> str:
        """
        Assemble the final report section by section.
        Each section draft is handled individually to avoid token overload.
        """
        logging.info("[Integrator] Integrating final report section by section")

        # Start with executive summary
        report_parts = ["# Final Professional Report\n", "## Executive Summary\n", executive_summary, "\n"]

        # Process each section separately
        for idx, sec in enumerate(sections, start=1):
            title = sec.get("title", f"Section {idx}")
            draft = sec.get("draft", "")
            critical = sec.get("critical", "")

            # Optional: refine each section draft individually with LLM
            prompt = (
                ROLE_PROMPTS['integrate'] +
                f"Section Title: {title}\n\n"
                f"Draft:\n{draft}\n\n"
                f"Critical points:\n{critical}\n\n"
                f"Please write in {language_hint}, and keep it clear and professional."
            )

            try:
                refined = self.llm.query(prompt, role="integrator", max_tokens=max_tokens)
            except Exception as e:
                logging.error(f"[Integrator] LLM failed for section {title}: {e}")
                refined = draft

            # Append to report
            # Normalize before joining
            normalized = normalize_section_draft(refined, title)
            report_parts.append(normalized)

        return "\n\n".join(report_parts)
