import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Supervisor:
    def __init__(self, llm: LLMInterface, tokens, max_tokens=None):
        self.llm = llm
        self.tokens = tokens

    def score(self, draft: str, max_tokens=None) -> dict:
        prompt = (
            ROLE_PROMPTS['supervisor'] + draft
        )
        raw = self.llm.query(prompt, role="supervisor", max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except Exception:
            return {"accuracy":0,"coherence":0,"completeness":0,"creativity":0,"format":0,"overall":0.0,
                    "strengths":[],"weaknesses":[],"improvements":[],"final_answer":raw}