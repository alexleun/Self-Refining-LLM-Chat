import json
from utils.llm_interface import LLMInterface

class Auditor:
    def __init__(self, llm: LLMInterface, tokens, max_tokens=None):
        self.llm = llm
        self.tokens = tokens

    def audit_section(self, draft: str, evidence: list) -> str:
        prompt = (
            "You are the Auditor.\nCheck the draft against the evidence.\n"
            "Return concise bullets: contradictions, unsupported claims, missing citations, and specific fixes.\n\n"
            "Draft:\n" + draft + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
        )
        return self.llm.query(prompt, role="auditor", max_tokens=max_tokens)