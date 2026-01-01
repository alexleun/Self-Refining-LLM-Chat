from utils.llm_interface import LLMInterface

class CriticalThinker:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def questions(self, draft: str) -> str:
        prompt = (
            "You are the Critical Thinker.\nGenerate 2–3 probing questions that challenge assumptions and broaden angles.\n"
            "Return questions only.\n\nDraft:\n" + draft
        )
        return self.llm.query(prompt, role="critical")