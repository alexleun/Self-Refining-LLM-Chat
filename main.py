from orchestrator import Orchestrator
from utils.logging_utils import setup_logging

"""
set of question for test:
LLM agent and skill in full auto AI software development
quility of research report
AI for self empowerment
研究人類日常行為是自動進行習慣比意志力更重要
negative Arctic Oscillation
"""

if __name__ == "__main__":
    setup_logging()  # initialize logging before anything else

    query = ("Health and Longevity Research")
    user_max_tokens = 131072   # example override

    orchestrator = Orchestrator(language_hint="English", max_rounds=1, limit = 3, local_evidence_dir=None)
    result = orchestrator.run(query, max_tokens=user_max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])