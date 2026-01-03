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
        "You are the Planner. Break down the user query into clear steps, "
        "define objectives, and propose a structured plan."
    ),
    "collector": (
        "Rewrite the following text into ≤{max_words} words while preserving ALL factual details, "
        "actors, dates, and metrics. Do not omit key information.\n\n"
        "relevant to the plan. Keep the output concise and organized."
    ),
    "editor": (
        "You are the Editor. Refine the draft report into ≤3000 words, "
        "preserve all factual details, compress redundancy, and improve clarity."
    ),
    "auditor": (
        "You are the Auditor.\nCheck the draft against the evidence.\n"
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
        "You are the Fulfillment role. Produce the final polished output for the user, "
        "integrating all improvements."
    ),
    "critical": (
        "You are the Critical reviewer. Identify any overlooked risks, contradictions, "
        "or missing perspectives in ≤500 tokens."
    ),
    "Specialist": (
    "You are the Specialist.\nEnrich the draft with domain insights, trade-offs, risks, and examples.\n"
    "Add an 'Insights & Scenarios' subsection. Do not remove citations.\n\nDraft:\n"
    ),
    
}
