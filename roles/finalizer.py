import logging
import re
from langchain_core.prompts import PromptTemplate
from utils.llm_interface import LLMInterface
from langchain_text_splitters import MarkdownHeaderTextSplitter
from utils.config import ROLE_PROMPTS



class Finalizer:
    """
    Finalizer role: cleans and normalizes the final report.
    Ensures consistent Markdown, removes AI chat artifacts, and polishes style.
    """

    def __init__(self, llm: LLMInterface, max_tokens: int = 2048, style = "standard"):
        self.llm = llm
        self.max_tokens = max_tokens
        


    def polish_chunk(self, chunk: str,language_hint = "English", max_tokens=None, style = "standard") -> str:
        """Polish a single chunk of the report."""
        logging.info("[Finalizer] Polishing report chunk")
        if style == "standard":
            prompt_style = "Finalizer"
        if style == "wiki":
            prompt_style = "WIKI_FINALIZER"

        # Prompt template for polishing
        prompt_template = PromptTemplate.from_template(
            ROLE_PROMPTS[prompt_style]
        )
        prompt = prompt_template.format(chunk=chunk, language_hint=language_hint)
        try:
            polished = self.llm.query(prompt, role="finalizer", max_tokens=max_tokens)
        except Exception as e:
            logging.error(f"[Finalizer] LLM query failed: {e}")
            polished = chunk
        return polished.strip()

    def polish_report(self, report: str, chunk_size: int = 3000, language_hint="English", max_tokens=None ) -> str:
        """
        Divide a large report into chunks, polish each, and recombine.
        """
        logging.info("[Finalizer] Splitting report into chunks")
        # Use LangChain MarkdownHeaderTextSplitter to chunk by headings
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("##", "Section")]
            # headers_to_split_on=[("#", "Title"), ("##", "Section"), ("###", "Subsection")]
        )
        
        chunks = splitter.split_text(report)
        logging.info(f"[Finalizer] Splitting size ={len(chunks)}")

        polished_chunks = [self.polish_chunk(c, language_hint, max_tokens) for c in chunks]

        final_report = "\n\n".join(polished_chunks)
        # Final normalization: collapse excessive blank lines
        final_report = re.sub(r"\n{3,}", "\n\n", final_report)
        logging.info("[Finalizer] Report polishing complete")
        return final_report