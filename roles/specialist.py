from utils.llm_interface import LLMInterface

class Specialist:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def enrich(self, draft: str, audit: str) -> str:
        prompt = (
            "You are the Specialist.\nEnrich the draft with domain insights, trade-offs, risks, and examples.\n"
            "Add an 'Insights & Scenarios' subsection. Do not remove citations.\n\nDraft:\n" + draft + "\n\nAudit:\n" + audit
        )
        return self.llm.query(prompt, role="specialist")