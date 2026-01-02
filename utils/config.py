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