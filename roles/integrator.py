import json
from utils.llm_interface import LLMInterface

class Integrator:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def write_summary(self, sections: list, language_hint: str, max_tokens=None) -> str:
        drafts = [s["draft"] for s in sections]
        prompt = (
            f"你是執行摘要撰寫者。請以{language_hint}撰寫 3–4 段執行摘要，"
            "簡潔、專業，適合董事會報告。\n\n"
            "以下是各章節草稿：\n" +
            json.dumps(drafts, ensure_ascii=False, indent=2)
        )
        return self.llm.query(prompt, role="executive", max_tokens=max_tokens)

    def integrate(self, sections: list, executive_summary: str, language_hint: str, max_tokens=None) -> str:
        drafts = [s["draft"] for s in sections]
        criticals = [s["critical"] for s in sections]

        prompt = (
            f"You are the integrator. Please integrate all chapter drafts, executive summaries, and contextual analyses "
            f"into a complete Markdown professional report. Must be written using {language_hint} and follow this structure:\n\n"
            "# Executive Summary\n...\n# Table of Contents\n...\n# Overview\n...\n# Chapter Analysis\n...\n"
            "# Insights and Contexts\n...\n# Visualizations\n...\n# References\n...\n# Appendix\n...\n\n"
            "Tone: Formal, professional, suitable for a board report.\n\n"
            "If any chapters or reviews contain diagrams with Mermaid syntax, please retain the original Mermaid code blocks "
            "for rendering in a browser or Markdown viewer. Do not convert to ASCII.\n\n"
            f"Executive Summary:\n{executive_summary}\n\n"
            "Chapter Drafts:\n" + json.dumps(drafts, ensure_ascii=False, indent=2) + "\n\n"
            "Situational analysis:\n" + json.dumps(criticals, ensure_ascii=False, indent=2)
        )
        return self.llm.query(prompt, role="integrator", max_tokens=max_tokens)