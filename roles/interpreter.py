import logging
from utils.config import ROLE_PROMPTS
from utils.llm_interface import LLMInterface

class Interpreter:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def interpret(self, user_query: str, max_tokens=None):
        """
        Expand the raw user query into a fuller description of intent, scope, and possible subtopics.
        Returns: dict with 'expanded' (text explanation) and 'intent' (summary keywords).
        """
        logging.info(f"[Interpreter] Interpreting query: {user_query}")

        prompt = (
            f"You are the Interpreter. The user provided the query: '{user_query}'.\n\n"
            "Your task:\n"
            "- Explain what the user likely intends with this query.\n"
            "- Expand the query into a fuller description of scope, context, and possible subtopics.\n"
            "- Guess the underlying purpose (study, design, analysis, comparison, etc.).\n"
            "- Suggest 3–5 keywords or themes that capture the intent.\n\n"
            "Return output as JSON with fields:\n"
            "{ \"expanded\": \"...\", \"intent\": [\"keyword1\", \"keyword2\", ...] }"
        )
        # prompt = f"{ROLE_PROMPTS['interpreter']}"

        try:
            reply = self.llm.query(prompt, role="interpreter", max_tokens=max_tokens)
            return reply
        except Exception as e:
            logging.error(f"[Interpreter] LLM query failed: {e}")
            return {
                "expanded": f"Could not interpret query due to error: {e}",
                "intent": []
            }