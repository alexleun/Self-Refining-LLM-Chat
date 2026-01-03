import json
from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class Planner:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def plan(self, user_query: str, max_tokens=None) -> dict:
        prompt = (
            ROLE_PROMPTS['planner'] + user_query + "\nReturn STRICT JSON."
        )
        raw = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except Exception:
            return {"goals": [], "milestones": [], "risks": [], "success_criteria": [], "raw": raw}