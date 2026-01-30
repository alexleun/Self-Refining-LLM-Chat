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
        - If force_hardcode=True: use fixed scaffold, refined by LLM.
        - Else: fall back to original LLM-driven parsing.
        """
        if force_hardcode:
            logging.info("[Planner] Using scaffold with LLM refinement.")
            return self._refined_sections(user_query, max_tokens)

        # fallback to original parsing if needed
        prompt = f"User query: {user_query}\n\nGenerate structured sections."
        raw_reply = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
        plan = self._parse_sections(raw_reply)

        # ✅ Validate plan
        if len(plan.get("sections", [])) < 5:
            logging.warning("[Planner] LLM produced too few sections, regenerating with scaffold.")
            return self._refined_sections(user_query, max_tokens)

        return plan

    def _refined_sections(self, user_query: str, max_tokens=None):
        """
        Start with fixed scaffold, then ask LLM to refine each section title + statement.
        Ensures minimum coverage even if LLM is weak.
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

        prompt = (
            "We are designing a research report plan.\n"
            "Refer to base_steps and the user_query.\n"
            "The first must be 'Introduction & Scope' and the last must be 'Conclusion'.\n"
            "Generate 7–9 meaningful section titles that cover the topic comprehensively.\n"
            "Return title line by line ONLY.\n\n"
            f"base_steps:\n{json.dumps(base_steps, ensure_ascii=False, indent=2)}\n\n"
            f"user_query:\n{user_query}\n"
        )

        plan_steps_str = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
        plan_steps = [line.strip() for line in plan_steps_str.splitlines() if line.strip()]

        # ✅ Validation: enforce scaffold if too few or generic
        if len(plan_steps) < 5:
            logging.warning("[Planner] Plan too short, falling back to base_steps.")
            plan_steps = base_steps

        refined = []
        for i, title in enumerate(plan_steps, start=1):
            if title.lower().startswith("step"):
                # Replace generic titles with scaffold fallback
                title = base_steps[i-1] if i-1 < len(base_steps) else f"Section {i}"

            prompt = (
                f"You are the Planner.\n\n"
                f"Section: {title}\n"
                "Write a refined section plan that:\n"
                "- Explains clearly how this section relates to the overall query\n"
                "- Provides a concise narrative statement (1 sentence)\n"
                "- Suggests 2–3 subtopics or angles to cover\n"
                "- Defines 2–3 concrete deliverables for this section\n"
                "- Adds 1–2 critical questions for later refinement\n\n"
                "Return JSON in the following format:\n"
                "{\n"
                f"  \"id\": \"sec-{i}\",\n"
                "  \"title\": \"...\",\n"
                "  \"statement\": \"...\",\n"
                "  \"query\": \"...\",\n"
                "  \"deliverables\": [\"...\", \"...\"],\n"
                "  \"critical\": [\"...\", \"...\"]\n"
                "}\n\n"
                f"The query: {user_query}"
            )
            try:
                reply = self.llm.query(prompt, role="planner", max_tokens=max_tokens)
                parsed = json.loads(reply)
                refined.append(parsed)
            except Exception:
                refined.append({
                    "id": f"sec-{i}",
                    "title": title,
                    "statement": f"This section will discuss {title} in relation to {user_query}.",
                    "query": user_query,
                    "deliverables": [],
                    "critical": []
                })

        return {"sections": refined}

    def _parse_sections(self, text: str):
        import re
        sections = []
        for match in re.finditer(r"##\s*(sec-\d+):?\s*(.+)", text):
            sec_id, title = match.groups()
            sections.append({"id": sec_id.strip(), "title": title.strip(), "content": text})
        return {"sections": sections}