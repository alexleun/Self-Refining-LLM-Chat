from orchestrator import Orchestrator
from roles.finalizer import Finalizer
from roles.integrator import Integrator, write_summary
from utils.logging_utils import setup_logging
import os
import argparse
import logging
import sys

"""
LLM agent and skill in full auto AI software development
quility of research report

"""
def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
        
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run finalize step only using existing Orchestrator.Finalizer.polish_report")
    p.add_argument("input", nargs="?", default="draft_final_report.md", help="Path to draft file (default: draft_final_report.md)")
    p.add_argument("-o", "--output", default="final_report.md", help="Path to save finalized report (default: final_report.md)")
    return p

def main(argv=None):
    setup_logging()  # same as main.py
    language_hint = "Traditional Chinese"
    max_rounds = 1
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = args.input
    output_path = args.output


    orchestrator = Orchestrator(language_hint=language_hint, max_rounds=max_rounds, local_evidence_dir=None)
    
    if not os.path.isfile(input_path):
        logging.error("Input file not found: %s", input_path)
        sys.exit(2)
        
    raw_report = read_file(input_path)
    logging.info(f"[write_summary] start")
    executive_summary = self.integrator.write_summary(raw_report, language_hint)
    with open(os.path.abspath(os.path.join("executive_summary.md")), "w", encoding="utf-8") as f:
                f.write(executive_summary)
    logging.info(f"[integrator] start")
    draft_final_report = self.integrator.integrate(raw_report, executive_summary, language_hint)
    logging.info(f"[Finalizer] start")
    final_report = orchestrator.Finalizer.polish_report(draft_final_report, language_hint)
    logging.info(f"[Finalizer] Done")
    report_path = os.path.abspath(os.path.join("final_report.md"))
    logging.info(f"[path] {report_path}")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)

if __name__ == "__main__":
    main()

    
    