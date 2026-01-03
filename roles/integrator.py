import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Integrator:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def write_summary(self, sections: list, language_hint: str, max_tokens=None) -> str:
        drafts = [s["draft"] for s in sections]
        prompt = (
    ROLE_PROMPTS['integrate_summary']+
            f"請以{language_hint}撰寫：\n" +
            json.dumps(drafts, ensure_ascii=False, indent=2)
        )
        return self.llm.query(prompt, role="executive", max_tokens=max_tokens)

    def integrate(self, sections: list, executive_summary: str, language_hint: str, max_tokens=None) -> str:
        drafts = [s["draft"] for s in sections]
        criticals = [s["critical"] for s in sections]

        prompt = (
            ROLE_PROMPTS['integrate']+
            f"Executive Summary:\n{executive_summary}\n\n"
            "Chapter Drafts:\n" + json.dumps(drafts, ensure_ascii=False, indent=2) + "\n\n"
            "Situational analysis:\n" + json.dumps(criticals, ensure_ascii=False, indent=2)
        )
        return self.llm.query(prompt, role="integrator", max_tokens=max_tokens)