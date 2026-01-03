from utils.llm_interface import LLMInterface

class FulfillmentChecker:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def check(self, user_query: str, draft: str, max_tokens=None) -> str:
        prompt = (
            "You are the Fulfillment Checker.\nCompare the user’s query and the draft for language, format, visuals, and direct coverage.\n"
            "Return a short checklist with Pass/Fail and 1–2 lines of rationale.\n\n"
            "User Query:\n" + user_query + "\n\nDraft:\n" + draft
        )
        return self.llm.query(prompt, role="fulfillment", max_tokens=max_tokens)