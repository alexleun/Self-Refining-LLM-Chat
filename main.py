from orchestrator import Orchestrator
from utils.logging_utils import setup_logging

"""
LLM agent and skill in full auto AI software development
quility of research report

"""

if __name__ == "__main__":
    setup_logging()  # initialize logging before anything else

    query = ("AI for self empowerment")
    user_max_tokens = 262144   # example override

    orchestrator = Orchestrator(language_hint="English", max_rounds=3, local_evidence_dir=None)
    result = orchestrator.run(query, max_tokens=user_max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])