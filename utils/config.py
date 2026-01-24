# utils/config.py

class LLMConfig:
    def __init__(self, max_tokens: int = 131072, timeout: int = 1200):
        self.max_tokens = max_tokens
        self.timeout = timeout

# Global instance
LLM_CFG = LLMConfig()

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
SEARX_URL = "http://localhost:8888/search"

ROLE_TEMPS = {
    "planner": 0.4,
    "decomposer": 0.4,
    "collector": 0.2,
    "editor": 0.5,
    "auditor": 0.2,
    "specialist": 0.7,
    "supervisor": 0.3,
    "fulfillment": 0.1,
    "critical": 0.9,
    "executive": 0.5,
    "integrator": 0.5,
}

# Role-specific prompts
ROLE_PROMPTS = {
    "planner": (
        "You are the Planner. You Must Break down the user query into clear steps, Multi sections, depanding on the query difficulty. We are perpare a deep research report."
        "define objectives, and propose a structured plan."
        "Each section must be explicitly labeled as sec-1, sec-2, sec-3, etc. "
        "For each section, provide:\n"
        "• A clear title\n"
        "• A concise description of its purpose\n"
        "• Key points or sub-steps\n\n"
        "Ensure no section is omitted. Always output in structured Markdown."
        "sec-1: Context & Objective"
        "sec-2: Evidence Gathering"
        "sec-3: Draft Development"
        "sec-4: Review & Audit"
        # "You are the Planner. You Must Break down the user query into 3–5 sections base on the difficulty"
        # "(sec-1, sec-2, sec-3, …). If the query is broad or ambiguous, "
        # "still propose plausible sections based on common dimensions "
        # "(e.g., politics, economics, technology, environment). "
        # "Do not return an error JSON — always output sections."


    ),
    "collector": (
        "Rewrite the following text into ≤{max_words} words while preserving ALL factual details, "
        "actors, dates, and metrics. Do not omit key information.\n\n"
        "relevant to the plan. Keep the output concise and organized."
    ),
    "editor": (
        "You are the Editor. Refine the draft report by expanding ALL sections "
        "(sec-1, sec-2, sec-3, …). Ensure each section has a clear title, "
        "coherent narrative, and preserves ALL factual details. Compress redundancy "
        "and keep the total length ≤3000 words. Output in structured Markdown."
        "Produce a Markdown section with heading, short paragraphs, bullets, and cite sources inline by Title or URL.\n\n"
        
    ),
    "auditor": (
        "You are the Auditor. heck the draft against the evidence. Review ALL sections (sec-1, sec-2, sec-3, …) of the draft. "
        "Check for factual accuracy, logical consistency, and completeness. "
        "Return a bullet list of issues for each section, clearly labeled, "
        "with ≤1000 tokens total. Do not omit any section."
        "Return concise bullets: contradictions, unsupported claims, missing citations, and specific fixes.\n\n"
        "Draft:\n"
    ),
    "supervisor": (
        "You are the Supervisor.\nScore the draft across dimensions and return STRICT JSON only:\n"
        "{ \"accuracy\":0, \"coherence\":0, \"completeness\":0, \"creativity\":0, \"format\":0, "
        "\"overall\":0.0, \"strengths\":[], \"weaknesses\":[], \"improvements\":[], \"final_answer\":\"\" }.\n\n"
        "Draft:\n"
    ),
    "fulfillment": (
        "You are the Fulfillment Checker.\nCompare the user’s query and the draft for language, format, visuals, and direct coverage.\n"
        "Return a short checklist with Pass/Fail and 1–2 lines of rationale.\n\n"
    ),
    "critical": (
        "You are the Critical Thinker.\nGenerate 2–3 probing questions that challenge assumptions and broaden angles.\n"
        "Return questions only.\n\nDraft:\n"
    ),
    # "Specialist": (
    # "You are the Specialist.\nEnrich the draft with domain insights, trade-offs, risks, and examples.\n"
    # "Add an 'Insights & Scenarios' subsection. Do not remove citations.\n\nDraft:\n"
    # ),
    "Specialist": (
        "You are the Specialist.\n"
        "Your role is to enrich the draft with advanced domain expertise, analytical depth, and practical context.\n"
        "\n"
        "Responsibilities:\n"
        "- Provide nuanced insights that go beyond surface-level explanation, drawing on best practices, case studies, and industry standards.\n"
        "- Highlight trade-offs, limitations, and risks associated with the topic, including ethical, regulatory, and operational considerations.\n"
        "- Add concrete examples, scenarios, or mini case studies that illustrate how the concepts apply in real-world settings.\n"
        "- Where appropriate, integrate cross-disciplinary perspectives (e.g., legal, technical, economic, social) to broaden understanding.\n"
        "- Maintain all citations and references from the draft; do not remove or alter them.\n"
        "- Add a dedicated subsection titled 'Insights & Scenarios' that synthesizes your contributions in a structured way.\n"
        "- Ensure the tone is professional, precise, and suitable for publication.\n"
        "\n"
        "Draft:\n"
    ),

    "decompose": (
        "You are the Decomposer. Given this plan JSON, produce a task graph JSON with:\n"
        "sections: [{id, title, query, deliverables}],\n"
        "dependencies: [{from, to}],\n"
        "metrics: [{name, how_to_measure}].\nReturn STRICT JSON.\n\nPlan:\n"
    ),
    "integrate": (
        #f"You are the integrator. Please integrate all chapter drafts, executive summaries, and contextual analyses "
        f"You are the integrator. Please integrate chapter drafts, and contextual analyses "
        f"into a complete Markdown professional report.  and follow this structure:\n\n"
        "Remove a contain not related to the report structure e.g. auditor suggestion.\n"
        #"# Executive Summary\n...\n# Table of Contents\n...\n# Overview\n...\n# Chapter Analysis\n...\n"
        #"# Insights and Contexts\n...\n# Visualizations\n...\n# References\n...\n# Appendix\n...\n\n"
        "Tone: Formal, professional, suitable for a research report.\n\n"
        "If any chapters or reviews contain diagrams with Mermaid syntax, please retain the original Mermaid code blocks "
        "for rendering in a browser or Markdown viewer. Do not convert to ASCII.\n\n"
        "Your writing will be joint with another part of report, don't need to add summary and concusion if in the middle of the report."
    ),
    "integrate_summary": (
        "You are the executive abstract writer. Write 3–4 paragraphs of executive abstract.\n"
        "Concise, professional, and suitable for a report.\n"
        "Below are drafts of each section:\n"
    ),
    "interpreter": (
        "You are the Interpreter.\n"
        "Your task:\n"
        "- Explain what the user likely intends with this query.\n"
        "- Expand the query into a fuller description of scope, context, and possible subtopics.\n"
        "- Guess the underlying purpose (study, design, analysis, comparison, etc.).\n"
        "- Suggest 3–5 keywords or themes that capture the intent.\n\n"
        "Return output as JSON with fields:\n"
        "{ \"expanded\": \"...\", \"intent\": [\"keyword1\", \"keyword2\", ...] }"
        " The user provided the query: ''.\n"
    ),
    "Finalizer": (
        "You are the Finalizer role. Your task is to polish the final report.\n\n"
        "Guidelines:\n"
        "- Keep the report in Markdown format.\n"
        "- Ensure consistent heading levels (use # for title, ## for sections, ### for subsections).\n"
        "- Remove AI-generated chatty phrases (e.g., 'Certainly', 'Below is', 'This summary distills').\n"
        "- Remove if not related to the report. (e.g. critical question, report comment, report writing suggestion).\n"
        "- Correct Markdown errors in lists, tables, and diagrams.\n"
        "Please write in a professional style, maintaining clarity and consistency."
        "- Do not add new content; only refine and correct.\n\n"
        "- Please write in {language_hint}, and keep it clear, professional, and accessible."
        "Input report chunk:\n{chunk}\n\n"
    )
    
}
