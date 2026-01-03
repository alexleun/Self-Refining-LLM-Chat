from utils.llm_interface import LLMInterface
from utils.config import ROLE_PROMPTS

class CriticalThinker:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def questions(self, draft: str, max_tokens=None) -> str:
        prompt = (
            ROLE_PROMPTS['critical'] + draft
        )
        return self.llm.query(prompt, role="critical", max_tokens=None)