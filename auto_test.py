from Sketchv2 import ConversationState, supervisor_loop

# Benchmark queries across all intents
TEST_QUERIES = [
    "Summarize the main themes of AI research conferences in 2025.",
    "List the top AI conferences happening in 2025 with dates and locations.",
    "Compare NeurIPS 2025 and ICML 2025 in terms of focus, scale, and industry relevance.",
    "Which AI conferences in 2025 would be most useful for a startup founder, and why?",
    "Explain why NeurIPS is considered more industry-aligned than ICML.",
    "Give me a step-by-step plan to prepare for presenting at ICML 2025."
]

def run_tests():
    for query in TEST_QUERIES:
        print("\n==============================")
        print(f"Running test: {query}")
        state = ConversationState()
        answer = supervisor_loop(query, state, max_loops=5, min_sources=1)
        print("\n[FINAL ANSWER]", answer[:500], "..." if len(answer) > 500 else "")
        print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")
        print(f"[SUMMARY] Tokens: {state.total_tokens}, Cost: ${state.total_cost:.6f}")
        for h in state.iteration_history:
            print(f"Round {h['iteration']} → Score {h['score']}/5")

if __name__ == "__main__":
    run_tests()