# import json
import logging
from utils.llm_interface import LLMInterface
# from utils.config import ROLE_PROMPTS

# class Auditor:
    # def __init__(self, llm: LLMInterface, tokens):
        # self.llm = llm
        # self.tokens = tokens

    # def audit_section(self, draft: str, evidence: list, max_tokens=None) -> str:
        # prompt = (
            # ROLE_PROMPTS['auditor'] + draft + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
        # )
        # return self.llm.query(prompt, role="auditor", max_tokens=max_tokens)
        
        


import logging

class Auditor:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def audit_section(self, draft, sources, max_tokens=None):
        """
        Audit a section draft against evidence and quality criteria.
        Returns: Markdown feedback string with explicit, actionable items.
        """
        #logging.info("[Auditor] Auditing section draft")

        prompt = (
            "You are the Auditor. Review the following section draft for accuracy, clarity, "
            "completeness, and consistency against the provided evidence.\n\n"
            "Guidelines:\n"
            "- Identify specific issues (e.g., missing evidence, unclear phrasing, contradictions).\n"
            "- Provide explicit, actionable recommendations for improvement.\n"
            "- Organize feedback into categories: Clarity, Evidence, Completeness, Consistency.\n"
            "- Use concise bullet points under each category.\n"
            "- Avoid rewriting the draft; focus on what needs fixing."
            f"Evidence:\n{sources}\n\n"
            f"Draft:\n{draft}\n\n"
        )

        try:
            feedback = self.llm.query(prompt, role="auditor", max_tokens=max_tokens)
        except Exception as e:
            logging.error(f"[Auditor] LLM query failed: {e}")
            feedback = "[Auditor failed to generate feedback]"

        return feedback