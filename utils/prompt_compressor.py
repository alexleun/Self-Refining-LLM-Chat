# utils/prompt_compressor.py
import math
import logging
from utils.config import LLM_CFG


class PromptCompressor:
    def __init__(self, llm, tokens, model_max=None, reserve=2048):
        self.llm = llm
        self.tokens = tokens
        # Use config if not supplied explicitly
        self.model_max = model_max or LLM_CFG.max_tokens
        self.reserve = reserve

    # ------------------------------------------------------------------
    def compress_if_needed(self, text: str, role: str,
                           target_tokens=None, max_depth=10) -> str:
        """
        Recursively compresses `text` until its token count is <= target_tokens.
        """
        if target_tokens is None:
            target_tokens = self.model_max - self.reserve
        # logging.info(f"[compressor] target_tokens = {target_tokens}")

        n_tokens = self.tokens.count(text)
        if n_tokens <= target_tokens:
            return text

        logging.warning(
            f"[PromptCompressor] role={role} prompt too long ({n_tokens}), compressing…")

        # ------------------------------------------------------------------
        # 1️⃣ Compute a *real* number of chunks
        n_chunks = math.ceil(n_tokens / target_tokens)
        if n_chunks < 2:
            n_chunks = 2   # ensure we always split

        words = text.split()
        chunk_size_words = max(1, len(words) // n_chunks + 1)

        logging.debug(
            f"[compressor] splitting into {n_chunks} chunks "
            f"({chunk_size_words} words each, ~{target_tokens//2} tokens/chunk)"
        )

        # ------------------------------------------------------------------
        # 2️⃣ Build the chunks
        chunks = [
            " ".join(words[i:i + chunk_size_words])
            for i in range(0, len(words), chunk_size_words)
            if words[i:i + chunk_size_words]
        ]

        # ------------------------------------------------------------------
        # 3️⃣ Summarise each chunk
        summaries = []
        for idx, chunk in enumerate(chunks, start=1):
            prompt = (
                f"Summarize chunk {idx}/{len(chunks)} into ≤{chunk_size_words // 2} words, "
                "preserve ALL factual details, actors, dates, and metrics:\n\n"
                f"{chunk}"
            )
            summaries.append(self.llm.query(prompt, role=role))

        merged_summary = "\n".join(summaries)

        # ------------------------------------------------------------------
        # 4️⃣ Check progress
        merge_tokens = self.tokens.count(merged_summary)
        if merge_tokens >= n_tokens:
            logging.warning(
                f"[PromptCompressor] No improvement in compression "
                f"({merge_tokens} vs {n_tokens}) — returning original."
            )
            return text

        # ------------------------------------------------------------------
        # 5️⃣ Recurse only if still over limit
        if merge_tokens > target_tokens and max_depth > 0:
            logging.warning(
                f"[PromptCompressor] After first merge: {merge_tokens} tokens — "
                "re‑compressing…"
            )
            return self.compress_if_needed(
                text=merged_summary,
                role=role,
                target_tokens=target_tokens,
                max_depth=max_depth - 1
            )

        # ------------------------------------------------------------------
        # 6️⃣ Return the best we could do
        return merged_summary
