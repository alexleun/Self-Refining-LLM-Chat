# auto_test.py
# Run: python auto_test.py

from sketch_v3_5 import sketch_v3_5_loop, EvidenceStore, save_markdown, ConversationState

def run_tests():
    queries = [
        "deep research below topic, write report in Traditional Chinese, generate graph or picture support if it can help for understanding: https://www.jdsupra.com/legalnews/governing-the-ungovernable-corporate-1075132/"
    ]

    for q in queries:
        print(f"\n[TEST QUERY] {q}")
        state = ConversationState()
        evidence_store = EvidenceStore()
        answer = sketch_v3_5_loop(q, state, evidence_store, max_rounds=3, language_hint="繁體中文")

        print("=== FINAL ANSWER (Preview) ===")
        print(answer)
        # Save with query-based filename
        md_path = save_markdown(answer, q, history=state.iteration_history)

        # Inspect sources
        if evidence_store.store:
            last_qid = list(evidence_store.store.keys())[-1]
            sources = evidence_store.get_all_sources(last_qid)
            print(f"\nSources collected: {len(sources)}")
            for s in sources[:3]:
                print(f" - {s['title']} ({s['url']}) relevance={s.get('relevance_score',0.0)}")
        print(f"\nMarkdown saved: {md_path}")

if __name__ == "__main__":
    run_tests()