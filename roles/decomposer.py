import json
from utils.llm_interface import LLMInterface

class Decomposer:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def decompose(self, plan: dict) -> dict:
        prompt = (
            "You are the Decomposer. Given this plan JSON, produce a task graph JSON with:\n"
            "sections: [{id, title, query, deliverables}],\n"
            "dependencies: [{from, to}],\n"
            "metrics: [{name, how_to_measure}].\nReturn STRICT JSON.\n\nPlan:\n" + json.dumps(plan, ensure_ascii=False)
        )
        raw = self.llm.query(prompt, role="decomposer")
        try:
            return json.loads(raw)
        except Exception:
            return {"sections": [], "dependencies": [], "metrics": [], "raw": raw}