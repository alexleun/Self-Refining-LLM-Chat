import os, json, logging
from utils.helpers import safe_name, now_ts
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
from utils.llm_interface import LLMInterface
from tqdm import tqdm
import logging
from colorama import Fore, Style, init

# Initialize colorama (needed on Windows)
init(autoreset=True)

from utils.search_engine import SearxSearch
from utils.helpers import slugify_query, now_ts

from utils.token_counter import TokenCounter

class Orchestrator:
    def __init__(self, language_hint="繁體中文", max_rounds=3, local_evidence_dir=None):
        self.language_hint = language_hint
        self.max_rounds = max_rounds
        self.local_evidence_dir = local_evidence_dir

        # ✅ initialize token counter + llm
        self.tokens = TokenCounter()
        self.llm = LLMInterface(self.tokens)

        # other roles
        self.planner = Planner(self.llm, self.tokens)
        self.decomposer = Decomposer(self.llm, self.tokens)

        # ✅ initialize search engine
        self.search_engine = SearxSearch(base_url="http://localhost:8888")

        # ✅ generate project_id
        self.project_id = f"{slugify_query(language_hint)}_{now_ts()}"

        # ✅ pass llm into collector
        self.collector = Collector(self.search_engine, self.project_id, self.llm)

        # Initialize roles
        self.planner = Planner(self.llm, self.tokens)
        self.decomposer = Decomposer(self.llm, self.tokens)
        # self.collector = Collector(self.tokens, self.llm)
        self.editor = Editor(self.llm, self.tokens)
        self.auditor = Auditor(self.llm, self.tokens)
        self.specialist = Specialist(self.llm, self.tokens)
        self.supervisor = Supervisor(self.llm, self.tokens)
        self.fulfillment = FulfillmentChecker(self.llm, self.tokens)
        self.critical = CriticalThinker(self.llm, self.tokens)
        self.integrator = Integrator(self.llm, self.tokens)

    def run(self, user_query: str, max_tokens=None):
        # store override
        self.max_tokens = max_tokens or LLM_CFG.max_tokens

        plan = self.planner.plan(user_query, max_tokens=self.max_tokens)
        sources = self.collector.collect(user_query, max_tokens=self.max_tokens)
        slug = slugify_query(user_query, max_words=5, max_len=50)
        project_id = f"__{slug}_{now_ts()}"

        os.makedirs(project_id, exist_ok=True)
        os.makedirs(os.path.join(project_id, "evidence"), exist_ok=True)
        os.makedirs(os.path.join(project_id, "sections"), exist_ok=True)

        plan = self.planner.plan(user_query)
        tasks = self.decomposer.decompose(plan)

        with open(os.path.join(project_id, "plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        with open(os.path.join(project_id, "tasks.json"), "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        iteration_history = []
        cumulative_sources = []
        manifest = {"project_id": project_id, "artifacts": []}
        prev_total = 0

        sections = tasks.get("sections", []) or [
            {"id": "sec-1", "title": "Overview", "query": user_query, "deliverables": ["report"]}
        ]

        # Outer loop: rounds
        for round_num in tqdm(range(1, self.max_rounds + 1),
                              desc="Orchestration rounds",
                              unit="round"):

            logging.info(f"=== Round {round_num} start ===")

            fresh_sources = self.collector.collect(user_query, deep_visit=True, local_dir=self.local_evidence_dir)
            evidence_paths = save_evidence(project_id, fresh_sources)
            manifest["artifacts"].extend([{"type": "evidence", "path": p} for p in evidence_paths])

            # Dedup evidence pool
            cumulative_sources.extend(fresh_sources)
            dedup, seen = [], set()
            for s in cumulative_sources:
                key = (s.get("url", "").strip().lower(), s.get("hash", ""))
                if key not in seen:
                    seen.add(key)
                    dedup.append(s)
            cumulative_sources = dedup

            section_outputs = []
            # Inner loop: sections with progress bar
            for sec in tqdm(sections,
                            desc=f"Round {round_num} sections",
                            unit="section",
                            leave=False):
                sec_dir = os.path.join(project_id, "sections", safe_name(sec.get("id", sec.get("title", "sec"))))
                os.makedirs(sec_dir, exist_ok=True)

                ev = fresh_sources
                draft = self.editor.draft_section(sec, ev, self.language_hint , max_tokens=self.max_tokens)
                audit = self.auditor.audit_section(draft, ev, max_tokens=self.max_tokens)
                enriched = self.specialist.enrich(draft, audit,  max_tokens=self.max_tokens)
                score = self.supervisor.score(enriched,  max_tokens=self.max_tokens)
                fulfill = self.fulfillment.check(user_query, enriched,  max_tokens=self.max_tokens)
                critical = self.critical.questions(enriched, max_tokens=self.max_tokens)

                # Save artifacts
                with open(os.path.join(sec_dir, f"draft_round{round_num}.md"), "w", encoding="utf-8") as f:
                    f.write(enriched)
                with open(os.path.join(sec_dir, f"audit_round{round_num}.md"), "w", encoding="utf-8") as f:
                    f.write(audit)
                with open(os.path.join(sec_dir, f"score_round{round_num}.json"), "w", encoding="utf-8") as f:
                    json.dump(score, f, ensure_ascii=False, indent=2)
                with open(os.path.join(sec_dir, f"fulfillment_round{round_num}.md"), "w", encoding="utf-8") as f:
                    f.write(fulfill)
                with open(os.path.join(sec_dir, f"critical_round{round_num}.md"), "w", encoding="utf-8") as f:
                    f.write(critical)

                section_outputs.append({
                    "section": sec,
                    "draft": enriched,
                    "audit": audit,
                    "score": score,
                    "fulfillment": fulfill,
                    "critical": critical
                })

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


            # ✅ Update outer progress bar description with metrics
            tqdm.write(f"Round {round_num} summary: avg_overall={avg_overall:.2f}, improvements={total_improvements}, tokens_used={round_tokens}")

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

            if avg_overall >= 8.0 and total_improvements == 0:
                break
                
        # Final integration
        if iteration_history:
            executive_summary = self.integrator.write_summary(iteration_history[-1]["sections"], self.language_hint, max_tokens=self.max_tokens)
            final_report = self.integrator.integrate(iteration_history[-1]["sections"], executive_summary, self.language_hint, max_tokens=self.max_tokens)

            report_path = os.path.abspath(os.path.join(project_id, "final_report.md"))
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(final_report)

            with open(os.path.join(project_id, "executive_summary.md"), "w", encoding="utf-8") as f:
                f.write(executive_summary)
            with open(os.path.join(project_id, "history.json"), "w", encoding="utf-8") as f:
                json.dump(iteration_history, f, ensure_ascii=False, indent=2)
            with open(os.path.join(project_id, "evidence_pool.json"), "w", encoding="utf-8") as f:
                json.dump(cumulative_sources, f, ensure_ascii=False, indent=2)
            with open(os.path.join(project_id, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

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
                "by_role": self.tokens.role_usage
            }

            print(Fore.CYAN + "\n" + "="*60)
            print("📊 TOKEN USAGE SUMMARY".center(60))
            print("="*60 + Style.RESET_ALL)

            print(f"Total tokens used: {token_summary['total']}")
            print("Per-role breakdown:")
            for role, usage in token_summary["by_role"].items():
                print(f"  {role:<12} prompt={usage['prompt']} completion={usage['completion']} total={usage['total']}")
            
        else:
            print(Fore.RED + "\n" + "="*60)
            print("❌ NO REPORT GENERATED".center(60))
            print("="*60 + Style.RESET_ALL)
            
        logging.info(f"[Orchestrator] Round {i} consumed {round_tokens} tokens, total={self.tokens.total}")


        return {
            "project_id": project_id,
            "final_report_path": os.path.join(project_id, "final_report.md"),
            "iteration_history": iteration_history,
            "token_summary": {"total": self.tokens.total, "by_role": self.tokens.role_usage}
        }