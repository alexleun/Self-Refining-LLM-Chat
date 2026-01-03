from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS
class Specialist:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def enrich(self, draft: str, audit: str, max_tokens=None) -> str:
        prompt = (
            ROLE_PROMPTS['Specialist'] + draft + "\n\nAudit:\n" + audit
        )
        return self.llm.query(prompt, role="specialist", max_tokens=max_tokens)