import requests, json, time, logging
from utils.token_counter import TokenCounter
from utils.config import LLM_CFG, LM_STUDIO_URL, ROLE_TEMPS

class LLMInterface:
    def __init__(self, tokens):
        self.tokens = tokens
        self.model_max = 131072  # ceiling

    def query(self, prompt: str, role: str, max_tokens=None, retries=2, backoff=0.75):
        requested_max = max_tokens or LLM_CFG.max_tokens
        effective_max = min(requested_max, self.model_max)

        reserve_for_completion = int(effective_max * 0.1)
        max_prompt = effective_max - reserve_for_completion

        n_tokens = self.tokens.count(prompt)
        if n_tokens > max_prompt:
            # logging.warning(f"[LLMInterface] role={role} prompt too long ({n_tokens} > {max_prompt}), truncating.")
            words = prompt.split()
            prompt = " ".join(words[:max_prompt])

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": ROLE_TEMPS.get(role, 0.7),
            "max_tokens": reserve_for_completion,
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