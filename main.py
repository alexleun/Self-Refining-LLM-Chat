from orchestrator import Orchestrator
from utils.logging_utils import setup_logging

if __name__ == "__main__":
    setup_logging()  # initialize logging before anything else

    query = ("LLM agent and skill in full auto AI software development")
    user_max_tokens = 77617   # example override

    orchestrator = Orchestrator(language_hint="English", max_rounds=1, local_evidence_dir=None)
    result = orchestrator.run(query, max_tokens=user_max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])