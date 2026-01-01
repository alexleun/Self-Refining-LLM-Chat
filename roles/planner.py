import json
from utils.llm_interface import LLMInterface

class Planner:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def plan(self, user_query: str) -> dict:
        prompt = (
            "You are the Planner. Create a concise JSON plan with:\n"
            "- goals: [..]\n- milestones: [{id, name, deliverables, target_date}],\n"
            "- risks: [..]\n- success_criteria: [..]\n\nQuery:\n" + user_query + "\nReturn STRICT JSON."
        )
        raw = self.llm.query(prompt, role="planner")
        try:
            return json.loads(raw)
        except Exception:
            return {"goals": [], "milestones": [], "risks": [], "success_criteria": [], "raw": raw}