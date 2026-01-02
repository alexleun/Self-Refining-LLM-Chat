import requests, json, time, logging
from utils.config import LLM_CFG, LM_STUDIO_URL, ROLE_TEMPS
# roles/token_counter.py (or wherever TokenCounter lives)
import tiktoken  # or any tokenizer you use
import logging
from utils.prompt_compressor import PromptCompressor

class TokenCounter:
    def __init__(self):
        self.usage_log = {}

    def add(self, role, usage):
        self.usage_log.setdefault(role, []).append(usage)

    def count(self, text: str) -> int:
        """
        Return approximate token count for a given text.
        """
        try:
            enc = tiktoken.get_encoding("cl100k_base")  # adjust to your model
            return len(enc.encode(text))
        except Exception:
            # fallback: rough word count
            return len(text.split())

class LLMInterface:
    def __init__(self, tokens: TokenCounter, default_max=None):
        self.tokens = tokens
        self.default_max = default_max or LLM_CFG.max_tokens
        self.model_max = 131072
        self.compressor = PromptCompressor(self, tokens, model_max=self.model_max)


        # logging.info(f"LLMInterface initialized with tokens={type(tokens)}")

    def query(self, prompt: str, role: str, max_tokens=None, retries: int = 2, backoff: float = 0.75) -> str:
        # pick user override or default
        requested_max = max_tokens or self.default_max
        # enforce ceiling
        effective_max = min(requested_max, self.model_max)
        safe_prompt = self.compressor.compress_if_needed(prompt, role)


        n_tokens = self.tokens.count(safe_prompt)
        reserve_for_completion = int(effective_max * 0.1)  # leave 10% for response
        max_prompt = effective_max - reserve_for_completion

        if n_tokens > max_prompt:
            logging.warning(f"[LLMInterface] role={role} prompt too long ({n_tokens} > {max_prompt}), truncating.")
            words = safe_prompt.split()
            safe_prompt = " ".join(words[:max_prompt])

        payload = {
            "messages": [{"role": "user", "content": safe_prompt}],
            "temperature": ROLE_TEMPS.get(role, 0.7),
            "max_tokens": reserve_for_completion,
        }


        for attempt in range(retries + 1):
            try:
                r = requests.post(LM_STUDIO_URL, json=payload, timeout=LLM_CFG.timeout)
                data = r.json()

                # --- Usage logging ---
                if "usage" in data:
                    self.tokens.add(role, data["usage"])
                    logging.info(f"[LLMInterface] role={role} usage={data['usage']}")

                # --- Response extraction ---
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
                time.sleep(backoff * (attempt + 1))

        return "[LLM Error]"