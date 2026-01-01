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

class Orchestrator:
    def __init__(self, language_hint="繁體中文", max_rounds=3, local_evidence_dir=None):
        self.language_hint = language_hint
        self.max_rounds = max_rounds
        self.local_evidence_dir = local_evidence_dir
        self.tokens = TokenCounter()
        self.llm = LLMInterface(self.tokens)

        # Initialize roles
        self.planner = Planner(self.llm, self.tokens)
        self.decomposer = Decomposer(self.llm, self.tokens)
        self.collector = Collector(self.tokens, self.llm)
        self.editor = Editor(self.llm, self.tokens)
        self.auditor = Auditor(self.llm, self.tokens)
        self.specialist = Specialist(self.llm, self.tokens)
        self.supervisor = Supervisor(self.llm, self.tokens)
        self.fulfillment = FulfillmentChecker(self.llm, self.tokens)
        self.critical = CriticalThinker(self.llm, self.tokens)
        self.integrator = Integrator(self.llm, self.tokens)

    def run(self, user_query: str):
        project_id = safe_name(user_query) + "_" + now_ts()
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

        for round_num in range(1, self.max_rounds + 1):
            logging.info(f"=== Round {round_num} start ===")

            fresh_sources = self.collector.collect(user_query, deep_visit=True, local_dir=self.local_evidence_dir)
            evidence_paths = save_evidence(project_id, fresh_sources)
            manifest["artifacts"].extend([{"type": "evidence", "path": p} for p in evidence_paths])

            cumulative_sources.extend(fresh_sources)
            dedup, seen = [], set()
            for s in cumulative_sources:
                key = (s.get("url", "").strip().lower(), s.get("hash", ""))
                if key not in seen:
                    seen.add(key)
                    dedup.append(s)
            cumulative_sources = dedup

            section_outputs = []
            for sec in sections:
                sec_dir = os.path.join(project_id, "sections", safe_name(sec.get("id", sec.get("title", "sec"))))
                os.makedirs(sec_dir, exist_ok=True)

                ev = fresh_sources
                draft = self.editor.draft_section(sec, ev, self.language_hint)
                audit = self.auditor.audit_section(draft, ev)
                enriched = self.specialist.enrich(draft, audit)
                score = self.supervisor.score(enriched)
                fulfill = self.fulfillment.check(user_query, enriched)
                critical = self.critical.questions(enriched)

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
            executive_summary = self.integrator.write_summary(iteration_history[-1]["sections"], self.language_hint)
            final_report = self.integrator.integrate(iteration_history[-1]["sections"], executive_summary, self.language_hint)

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

        return {
            "project_id": project_id,
            "final_report_path": os.path.join(project_id, "final_report.md"),
            "iteration_history": iteration_history,
            "token_summary": {"total": self.tokens.total, "by_role": self.tokens.role_usage}
        }