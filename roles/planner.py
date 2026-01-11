import json
import logging
from utils.llm_interface import LLMInterface

class Planner:
    def __init__(self, llm: LLMInterface, tokens):
        self.llm = llm
        self.tokens = tokens

    def plan(self, user_query: str, max_tokens=None, force_hardcode=True):
        """
        Generate a multi-section plan.
        - If force_hardcode=True: use fixed 9-step scaffold, refined by LLM.
        - Else: fall back to original LLM-driven parsing.
        """
        if force_hardcode:
            logging.info("[Planner] Using 9-step scaffold with LLM refinement.")
            return self._refined_sections(user_query, max_tokens)

        # fallback to original parsing if needed
        prompt = f"User query: {user_query}\n\nGenerate structured sections."
        raw_reply = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
        return self._parse_sections(raw_reply)

    def _refined_sections(self, user_query: str, max_tokens=None):
        """
        Start with fixed scaffold, then ask LLM to refine each section title + statement.
        """
        base_steps = [
            "Introduction & Scope",
            "Historical Context",
            "Current Landscape",
            "Key Challenges",
            "Methodologies",
            "Case Studies",
            "Solutions",
            "Future Trends",
            "Conclusion"
        ]

        refined = []
        for i, title in enumerate(base_steps, start=1):
            # prompt = (
                # f"You are the Planner. The user query is: '{user_query}'.\n\n"
                # f"Section: {title}\n"
                # "Write a refined section plan that:\n"
                # "- Explains how this section relates to the query\n"
                # "- Suggests 2–3 subtopics or angles to cover\n"
                # "- Keep it concise (3–4 sentences)\n\n"
                # "Return JSON: {\"id\": \"sec-X\", \"title\": \"...\", \"statement\": \"...\"}"
            # )
            prompt = (
                f"You are the Planner. The user query is: '{user_query}'.\n\n"
                f"Section: {title}\n"
                "Write a refined section plan that:\n"
                "- Explains clearly how this section relates to the overall query\n"
                "- Provides a concise narrative statement (1 sentences)\n"
                "- Suggests 2–3 subtopics or angles to cover\n"
                "- Defines 2–3 concrete deliverables for this section (e.g., timeline, analysis, recommendations)\n"
                "- Adds 1–2 critical questions that should be addressed in later refinement rounds\n\n"
                "Return JSON in the following format:\n"
                "{\n"
                f"  \"id\": \"sec-{i}\",\n"
                "  \"title\": \"...\",\n"
                "  \"statement\": \"...\",\n"
                "  \"query\": \"...\",\n"
                "  \"deliverables\": [\"...\", \"...\", \"...\"],\n"
                "  \"critical\": [\"...\", \"...\"]\n"
                "}"
            )

            try:
                reply = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
                parsed = json.loads(reply)
                refined.append(parsed)
            except Exception:
                refined.append({
                    "id": f"sec-{i}",
                    "title": title,
                    "statement": f"This section will discuss {title} in relation to {user_query}."
                })

        return {"sections": refined}

    def _parse_sections(self, text: str):
        import re
        sections = []
        for match in re.finditer(r"##\s*(sec-\d+):?\s*(.+)", text):
            sec_id, title = match.groups()
            sections.append({"id": sec_id.strip(), "title": title.strip(), "content": text})
        return {"sections": sections}