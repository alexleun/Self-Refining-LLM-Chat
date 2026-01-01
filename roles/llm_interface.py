import requests, json, time, logging
from utils.config import LLM_CFG, LM_STUDIO_URL, ROLE_TEMPS

class LLMInterface:
    def __init__(self, tokens):
        self.tokens = tokens

    def query(self, prompt: str, role: str, retries: int = 2, backoff: float = 0.75) -> str:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": ROLE_TEMPS.get(role, 0.7),
            "max_tokens": LLM_CFG.max_tokens,
        }
        for attempt in range(retries+1):
            try:
                r = requests.post(LM_STUDIO_URL, json=payload, timeout=LLM_CFG.timeout)
                data = r.json()
                if "usage" in data:
                    self.tokens.add(role, data["usage"])
                if "choices" in data and data["choices"]:
                    m = data["choices"][0].get("message", {})
                    if m and "content" in m:
                        return m["content"]
                    d = data["choices"][0].get("delta", {})
                    if "content" in d:
                        return d["content"]
                return json.dumps(data, ensure_ascii=False)
            except Exception as e:
                logging.error(f"LLM error role={role} attempt={attempt+1}: {e}")
                time.sleep(backoff * (attempt+1))
        return "[LLM Error]"