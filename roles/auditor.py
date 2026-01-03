import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Auditor:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def audit_section(self, draft: str, evidence: list, max_tokens=None) -> str:
        prompt = (
            ROLE_PROMPTS['auditor'] + draft + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
        )
        return self.llm.query(prompt, role="auditor", max_tokens=max_tokens)