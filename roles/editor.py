import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Editor:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def draft_section(self, section: dict, evidence: list, language_hint: str, max_tokens=None) -> str:
        prompt = (
            ROLE_PROMPTS['editor']+
            f"Write in {language_hint}.\n"
            "Section:\n"+ json.dumps(section, ensure_ascii=False) + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
        )
        return self.llm.query(prompt, role="editor", max_tokens=max_tokens)