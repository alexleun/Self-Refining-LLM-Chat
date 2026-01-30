#!/usr/bin/env python3
"""
resume.py

Resume an interrupted orchestration run:
- By default, find the latest project folder (by modification time).
- Or, if --project <folder> is specified, resume that folder directly.
- Calls Orchestrator.resume() to continue remaining rounds.
"""

import os
import sys
import logging
import argparse
from utils.logging_utils import setup_logging
from orchestrator import Orchestrator

def find_latest_project(base_dir="."):
    """Find the most recent project folder by modification time."""
    candidates = [d for d in os.listdir(base_dir) if os.path.isdir(d)]
    if not candidates:
        raise RuntimeError("No project folders found.")
    latest = sorted(candidates, key=lambda x: os.path.getmtime(x))[-1]
    return latest

def main(argv=None):
    setup_logging()
    parser = argparse.ArgumentParser(description="Resume an interrupted orchestration run.")
    parser.add_argument("--project", help="Path to project folder to resume. If omitted, latest folder is used.")
    parser.add_argument("--lang", default="繁體中文", help="Language hint for orchestrator (default: 繁體中文)")
    parser.add_argument("--max-rounds", type=int, default=3, help="Max rounds to run (default: 3)")
    parser.add_argument("--max-tokens", type=int, default=None, help="Optional max tokens override")
    args = parser.parse_args(argv)

    if args.project:
        project_dir = args.project
        if not os.path.isdir(project_dir):
            logging.error("Specified project folder not found: %s", project_dir)
            sys.exit(2)
    else:
        project_dir = find_latest_project(".")
        logging.info("Auto-detected latest project folder: %s", project_dir)

    logging.info("Resuming project: %s", project_dir)

    orchestrator = Orchestrator(language_hint=args.lang,
                                max_rounds=args.max_rounds,
                                local_evidence_dir=os.path.join(project_dir, "evidence"))

    result = orchestrator.resume(project_dir, max_tokens=args.max_tokens)

    print("Project:", result["project_id"])
    print("Final report:", result["final_report_path"])
    print("Total tokens:", result["token_summary"]["total"])

if __name__ == "__main__":
    main()