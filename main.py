from orchestrator import Orchestrator
from utils.logging_utils import setup_logging
#        "Construct a multidisciplinary argument evaluating whether superintelligence should be developed, "
#        "focusing on macro-scale impacts on human cognition, diplomacy, and global market dynamics."
if __name__ == "__main__":
    setup_logging()  # initialize logging before anything else

    query = (
                "focusing on macro-scale impacts on human cognition, diplomacy, and global market dynamics."
    )
    user_max_tokens = 131072   # example override

    orchestrator = Orchestrator(language_hint="繁體中文", max_rounds=1, local_evidence_dir=None)
    result = orchestrator.run(query, max_tokens=user_max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])