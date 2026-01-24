import os
import json
from utils.helpers import safe_name, now_ts, slugify_query
from utils.token_counter import TokenCounter
from utils.persistence import save_evidence
from roles.planner import Planner
from roles.decomposer import Decomposer
from roles.collector import Collector
from roles.editor import Editor
from roles.auditor import Auditor
from roles.specialist import Specialist
from roles.supervisor import Supervisor
from roles.fulfillment import FulfillmentChecker
from roles.critical import CriticalThinker
from roles.integrator import Integrator
from roles.interpreter import Interpreter
from roles.finalizer import Finalizer
from utils.llm_interface import LLMInterface
from tqdm import tqdm
import logging
from colorama import Fore, Style, init
from utils.config import LLM_CFG
from utils.search_engine import SearxSearch
from utils.section_runner import run_sections

init(autoreset=True)

class Orchestrator:
    def __init__(self, language_hint="English", max_rounds=3, limit=20, local_evidence_dir=None):
        self.language_hint = language_hint
        self.max_rounds = max_rounds
        self.local_evidence_dir = local_evidence_dir
        self.tokens = TokenCounter()
        self.llm = LLMInterface(self.tokens)
        self.limit = limit
        self.search_engine = SearxSearch(base_url="http://localhost:8888")
        
        self.project_id = f"{slugify_query(language_hint)}_{now_ts()}"
        self.collector = Collector(self.search_engine, self.project_id, self.limit, self.llm)
        self.planner = Planner(self.llm, self.tokens)
        self.decomposer = Decomposer(self.llm, self.tokens)
        self.editor = Editor(self.llm, self.tokens)
        self.auditor = Auditor(self.llm, self.tokens)
        self.specialist = Specialist(self.llm, self.tokens)
        self.supervisor = Supervisor(self.llm, self.tokens)
        self.fulfillment = FulfillmentChecker(self.llm, self.tokens)
        self.critical = CriticalThinker(self.llm, self.tokens)
        self.integrator = Integrator(self.llm, self.tokens)
        self.Interpreter = Interpreter(self.llm, self.tokens)
        self.Finalizer = Finalizer(self.llm, self.tokens)

    def run(self, user_query: str, max_tokens=None):
        self.max_tokens = max_tokens or LLM_CFG.max_tokens
        interpretation = self.Interpreter.interpret(user_query, max_tokens=self.max_tokens)
        logging.info(f"[Interpretation]:done")
        plan = self.planner.plan(interpretation, max_tokens=self.max_tokens)
        logging.info(f"[Planner]:done")
        # sources = self.collector.collect(user_query, max_tokens=self.max_tokens)
        # logging.info(f"[Collector]:done")
        slug = slugify_query(user_query, max_words=5, max_len=50)
        project_id = f"{slug}_{now_ts()}"

        os.makedirs(project_id, exist_ok=True)
        os.makedirs(os.path.join(project_id, "evidence"), exist_ok=True)
        os.makedirs(os.path.join(project_id, "sections"), exist_ok=True)

        with open(os.path.join(project_id, "plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)

        iteration_history = []
        cumulative_sources = []
        prev_total = 0
        prev_round_outputs = {}  # store outputs per section
        
        fresh_sources = self.collector.collect(user_query, deep_visit=True, local_dir=self.local_evidence_dir)
        evidence_paths = save_evidence(project_id, fresh_sources)
            
        # Outer loop: rounds
        for round_num in tqdm(range(1, self.max_rounds + 1), desc="Orchestration rounds", unit="round"):
            logging.info(f"[Orchestrator] Round {round_num} start, Sections received Number of sections: {len(plan['sections'])} ")  
            
            section_outputs = run_sections(
                                    user_query,
                                    plan['sections'], 
                                    project_id,round_num,
                                    fresh_sources, 
                                    prev_round_outputs,
                                    self.language_hint, 
                                    self.max_tokens, 
                                    self.fulfillment, 
                                    self.critical, 
                                    self.supervisor, 
                                    self.editor, 
                                    self.auditor, 
                                    self.specialist
                                )
            # Update prev_round_outputs for next iteration
            prev_round_outputs = {o["section"]["id"]: o for o in section_outputs}

            # Round summary
            round_tokens = self.tokens.total - prev_total
            avg_overall = sum(o["score"].get("overall", 0.0) for o in section_outputs) / max(1, len(section_outputs))
            total_improvements = sum(len(o["score"].get("improvements", [])) for o in section_outputs)
            
            # ✅ Color-coded summary
            if avg_overall >= 8.0:
                color = Fore.GREEN
            elif avg_overall >= 5.0:
                color = Fore.YELLOW
            else:
                color = Fore.RED

            summary_text = (
                f"Round {round_num} summary: avg_overall={avg_overall:.2f}, "
                f"improvements={total_improvements}, tokens_used={round_tokens}"
            )

            # Print with color
            tqdm.write(color + summary_text + Style.RESET_ALL)

            # Log as usual
            logging.info(summary_text)
            logging.info(f"[ROUND {round_num}] tokens_used={round_tokens} total={self.tokens.total}")
            prev_total = self.tokens.total


            # Update outer progress bar description with metrics
            #tqdm.write(f"Round {round_num} summary: avg_overall={avg_overall:.2f}, improvements={total_improvements}, tokens_used={round_tokens}")
            logging.info(f"[ROUND {round_num}] sections={len(section_outputs)} avg_overall={avg_overall:.2f} improvements={total_improvements}")
            logging.info(f"[ROUND {round_num}] tokens_used={round_tokens} total={self.tokens.total}")
            prev_total = self.tokens.total

            iteration_history.append({
                "round": round_num,
                "avg_overall": avg_overall,
                "tokens_used": round_tokens,
                "tokens_total": self.tokens.total,
                "sections": section_outputs
            })
            # if avg_overall >= 8.0 and total_improvements == 0:
            if avg_overall >= 8.0:
                break
                
        # Final integration
        if iteration_history:
            executive_summary = self.integrator.write_summary(iteration_history[-1]["sections"], self.language_hint, max_tokens=self.max_tokens)
            with open(os.path.join(project_id, "executive_summary.md"), "w", encoding="utf-8") as f:
                f.write(executive_summary)
            draft_final_report = self.integrator.integrate(iteration_history[-1]["sections"], executive_summary, self.language_hint, max_tokens=self.max_tokens)
            with open(os.path.join(project_id, "draft_final_report.md"), "w", encoding="utf-8") as f:
                f.write(draft_final_report)
            final_report = self.Finalizer.polish_report(draft_final_report,language_hint=self.language_hint ,max_tokens=self.max_tokens)
            report_path = os.path.abspath(os.path.join(project_id, "final_report.md"))
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(final_report)

            # with open(os.path.join(project_id, "history.json"), "w", encoding="utf-8") as f:
                # json.dump(iteration_history, f, ensure_ascii=False, indent=2)
            # with open(os.path.join(project_id, "evidence_pool.json"), "w", encoding="utf-8") as f:
                # json.dump(cumulative_sources, f, ensure_ascii=False, indent=2)
            # with open(os.path.join(project_id, "manifest.json"), "w", encoding="utf-8") as f:
                # json.dump(manifest, f, ensure_ascii=False, indent=2)

            print("Final professional report saved at:", report_path)
        else:
            logging.warning("No iteration history; skipping final_report.md and history.json")
            
        if iteration_history:
            final_avg = iteration_history[-1]["avg_overall"]
            if final_avg >= 8.0:
                banner_color = Fore.GREEN
                banner_text = "✅ SUCCESS: High-quality report generated"
            elif final_avg >= 5.0:
                banner_color = Fore.YELLOW
                banner_text = "⚠️ REVIEW: Report acceptable but improvements suggested"
            else:
                banner_color = Fore.RED
                banner_text = "❌ NEEDS IMPROVEMENT: Report quality below threshold"

            print(banner_color + "\n" + "="*60)
            print(banner_text.center(60))
            print("="*60 + Style.RESET_ALL)
            
            # --- Token Usage Summary Banner ---
            token_summary = {
                "total": self.tokens.total,
                "by_role": self.tokens.all_usage()
            }

            print(Fore.CYAN + "\n" + "="*60)
            print("📊 TOKEN USAGE SUMMARY".center(60))
            print("="*60 + Style.RESET_ALL)

            print(f"Total tokens used: {token_summary['total']}")
            print("Per-role breakdown:")
            for role, usage in token_summary["by_role"].items():
                print(f"{role:<12} prompt={usage['prompt_tokens']} completion={usage['completion_tokens']} total={usage['total_tokens']}")
            
        else:
            print(Fore.RED + "\n" + "="*60)
            print("❌ NO REPORT GENERATED".center(60))
            print("="*60 + Style.RESET_ALL)
            
        return {
            "project_id": project_id,
            "final_report_path": os.path.join(project_id, "final_report.md"),
            "iteration_history": iteration_history,
            "token_summary": {"total": self.tokens.total, "by_role": self.tokens.role_usage}
        }