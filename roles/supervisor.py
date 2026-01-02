import json
from utils.llm_interface import LLMInterface

class Supervisor:
    def __init__(self, llm: LLMInterface, tokens, max_tokens=None):
        self.llm = llm
        self.tokens = tokens

    def score(self, draft: str) -> dict:
        prompt = (
            "You are the Supervisor.\nScore the draft across dimensions and return STRICT JSON only:\n"
            "{ \"accuracy\":0, \"coherence\":0, \"completeness\":0, \"creativity\":0, \"format\":0, "
            "\"overall\":0.0, \"strengths\":[], \"weaknesses\":[], \"improvements\":[], \"final_answer\":\"\" }.\n\n"
            "Draft:\n" + draft
        )
        raw = self.llm.query(prompt, role="supervisor", max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except Exception:
            return {"accuracy":0,"coherence":0,"completeness":0,"creativity":0,"format":0,"overall":0.0,
                    "strengths":[],"weaknesses":[],"improvements":[],"final_answer":raw}