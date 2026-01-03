import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Decomposer:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def decompose(self, plan: dict, max_tokens=None) -> dict:
        prompt = (
            ROLE_PROMPTS['decompose'] + json.dumps(plan, ensure_ascii=False)
        )
        raw = self.llm.query(prompt, role="decomposer", max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except Exception:
            return {"sections": [], "dependencies": [], "metrics": [], "raw": raw}