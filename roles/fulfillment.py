from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class FulfillmentChecker:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def check(self, user_query: str, draft: str, max_tokens=None) -> str:
        prompt = (
            ROLE_PROMPTS['fulfillment'] +
            "User Query:\n" + user_query + "\n\nDraft:\n" + draft
        )
        return self.llm.query(prompt, role="fulfillment", max_tokens=max_tokens)