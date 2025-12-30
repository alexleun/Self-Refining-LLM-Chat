# auto_test.py
# Run: python auto_test.py

from sketch_v3 import sketch_v3_loop, EvidenceStore, save_markdown

def run_tests():
    queries = [
        "Which AI conferences in 2025 should a startup founder attend, and why?",
        "Explain controversies around generative AI safety in 2025.",
        "What are the best practices for scaling railway IoT systems?"
    ]

    for q in queries:
        print(f"\n[TEST QUERY] {q}")
        evidence_store = EvidenceStore()
        state = {}
        answer = sketch_v3_loop(q, state, evidence_store, max_rounds=6)

        # Save Markdown output
        filename = save_markdown(answer, q, history=state.get("iteration_history", []))
        print(f"Saved: {filename}")

        # Quick inspection
        if evidence_store.store:
            last_query_id = list(evidence_store.store.keys())[-1]
            sources = evidence_store.get_all_sources(last_query_id)
            print(f"Sources collected: {len(sources)}")
            for s in sources[:2]:  # show first 2
                print(f" - {s['title']} ({s['url']})")

if __name__ == "__main__":
    run_tests()