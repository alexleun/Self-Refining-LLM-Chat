import json
from utils.llm_interface import LLMInterface

class Editor:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def draft_section(self, section: dict, evidence: list, language_hint: str, max_tokens=None) -> str:
        prompt = (
            "You are the Drafting Editor.\n"
            f"Write in {language_hint}.\n"
            "Produce a Markdown section with heading, short paragraphs, bullets, and cite sources inline by Title or URL.\n\n"
            "Section:\n" + json.dumps(section, ensure_ascii=False) + "\n\nEvidence:\n" + json.dumps(evidence, ensure_ascii=False)
        )
        return self.llm.query(prompt, role="editor", max_tokens=max_tokens)