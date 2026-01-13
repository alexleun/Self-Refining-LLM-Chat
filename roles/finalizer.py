import logging
from langchain_core.prompts import PromptTemplate
from utils.llm_interface import LLMInterface

class Finalizer:
    """
    Finalizer role: cleans and normalizes the final report.
    Ensures consistent Markdown, removes AI chat artifacts, and polishes style.
    """

    def __init__(self, llm: LLMInterface, max_tokens: int = 2048):
        self.llm = llm
        self.max_tokens = max_tokens

        # Prompt template for polishing
        self.prompt_template = PromptTemplate.from_template(
            "You are the Finalizer role. Your task is to polish the final report.\n\n"
            "Guidelines:\n"
            "- Keep the report in Markdown format.\n"
            "- Ensure consistent heading levels (use # for title, ## for sections, ### for subsections).\n"
            "- Remove AI-generated chatty phrases (e.g., 'Certainly', 'Below is', 'This summary distills').\n"
            "- Correct Markdown errors in lists, tables, and diagrams.\n"
            "- Normalize spacing (no duplicate blank lines).\n"
            "- Maintain professional, board-level tone.\n"
            "- Do not add new content; only refine and correct.\n\n"
            "Input report chunk:\n{chunk}\n\n"
            "Please write in a professional style, maintaining clarity and consistency."
        )

    def polish_chunk(self, chunk: str, max_tokens=None) -> str:
        """Polish a single chunk of the report."""
        logging.info("[Finalizer] Polishing report chunk")
        prompt = self.prompt_template.format(chunk=chunk)
        try:
            polished = self.llm.query(prompt, role="finalizer", max_tokens=max_tokens)
        except Exception as e:
            logging.error(f"[Finalizer] LLM query failed: {e}")
            polished = chunk
        return polished.strip()

    def polish_report(self, report: str, chunk_size: int = 3000, max_tokens=None ) -> str:
        """
        Divide a large report into chunks, polish each, and recombine.
        """
        logging.info("[Finalizer] Splitting report into chunks")
        chunks = [report[i:i+chunk_size] for i in range(0, len(report), chunk_size)]

        polished_chunks = [self.polish_chunk(c, max_tokens) for c in chunks]

        final_report = "\n\n".join(polished_chunks)
        logging.info("[Finalizer] Report polishing complete")
        return final_report