from orchestrator import Orchestrator
from utils.logging_utils import setup_logging
import argparse
import logging

"""
set of question for test:
LLM agent and skill in full auto AI software development
quility of research report
AI for self empowerment
研究人類日常行為是自動進行習慣比意志力更重要
negative Arctic Oscillation
Health and Longevity Research
"""

def main():
    setup_logging()  # initialize logging before anything else

    parser = argparse.ArgumentParser(description="Run orchestration pipeline")
    parser.add_argument("--query", help="User query for research/report generation")
    parser.add_argument("--style", choices=["standard", "wiki"], default="standard",
                        help="Choose report style: standard (default) or wiki")
    parser.add_argument("--lang", default="English", help="Language hint (default: English)")
    parser.add_argument("--max-rounds", type=int, default=1, help="Max rounds to run (default: 3)")
    parser.add_argument("--max-tokens", type=int, default=131072, help="Max tokens (default: 131072)")
    parser.add_argument("--max-SearhResult", type=int, default=3, help="Max Search Result (default: 3)")
    
    args = parser.parse_args()

 # ✅ Default query if none provided
    query = args.query or "rapid permafrost thaw reduces albedo"

    logging.info("Starting orchestration with query: %s", query)

    
    orchestrator = Orchestrator(language_hint=args.lang, 
                                max_rounds=args.max_rounds,
                                limit = args.max_SearhResult, 
                                local_evidence_dir=None,
                                report_style=args.style)
                                
    result = orchestrator.run(query, max_tokens=args.max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])


if __name__ == "__main__":
    main()