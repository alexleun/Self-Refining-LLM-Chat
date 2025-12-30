# auto_test.py
# Run: python auto_test.py

from sketch_v3 import sketch_v3_loop, EvidenceStore

def run_tests():
    queries = [
        "Which AI conferences in 2025 should a startup founder attend, and why?",
        "Explain controversies around generative AI safety in 2025.",
        "What are the best practices for scaling railway IoT systems?"
    ]

    for q in queries:
        print(f"\n[TEST QUERY] {q}")
        evidence_store = EvidenceStore()
        answer = sketch_v3_loop(q, evidence_store, max_rounds=3)

        print("=== FINAL ANSWER (Preview) ===")
        print(answer)

        # Inspect sources
        if evidence_store.store:
            last_qid = list(evidence_store.store.keys())[-1]
            sources = evidence_store.get_all_sources(last_qid)
            print(f"\nSources collected: {len(sources)}")
            for s in sources[:2]:
                print(f" - {s['title']} ({s['url']})")

if __name__ == "__main__":
    run_tests()