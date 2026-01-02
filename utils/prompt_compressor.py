# utils/prompt_compressor.py
import logging

class PromptCompressor:
    def __init__(self, llm, tokens, model_max=131072, reserve=2048):
        self.llm = llm
        self.tokens = tokens
        self.model_max = model_max
        self.reserve = reserve

    def compress_if_needed(self, text: str, role: str, target_tokens=None) -> str:
        target_tokens = target_tokens or (self.model_max - self.reserve)
        n_tokens = self.tokens.count(text)

        if n_tokens <= target_tokens:
            return text

        logging.warning(f"[PromptCompressor] role={role} prompt too long ({n_tokens}), compressing...")

        # Split into chunks
        words = text.split()
        chunk_size = int(target_tokens / 4)  # adjust chunk size
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

        summaries = []
        for i, chunk in enumerate(chunks):
            prompt = (
                f"Summarize chunk {i+1}/{len(chunks)} into ≤{chunk_size//2} words, "
                "preserve ALL factual details, actors, dates, and metrics:\n\n"
                f"{chunk}"
            )
            summaries.append(self.llm.query(prompt, role=role))

        merged = "\n".join(summaries)

        # Recursive compression if still too long
        if self.tokens.count(merged) > target_tokens:
            return self.compress_if_needed(merged, role, target_tokens)

        return merged