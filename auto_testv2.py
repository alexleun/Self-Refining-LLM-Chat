from Sketchv2 import ConversationState, supervisor_loop, save_markdown

TEST_QUERIES = [
    "Which AI conferences in 2025 would be most useful for a startup founder, and why?”",
    "Give me a step‑by‑step plan to prepare for presenting at ICML 2025..",
    "Explain the controversies around generative AI safety discussed at conferences in 2025.",
    "Compare NeurIPS 2025 with NeurIPS 2015 in terms of themes and industry involvement."
]

DEBUG = True  # Toggle this flag to print all drafts

def run_tests():
    for query in TEST_QUERIES:
        print("\n==============================")
        print(f"Running test: {query}")
        state = ConversationState()
        answer = supervisor_loop(query, state, max_loops=20, min_sources=10)

        print("\n[FINAL ANSWER]\n", answer)
        
        # Save with query‑based filename
        save_markdown(answer, query, state.iteration_history)

        
        print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")
        print(f"[SUMMARY] Tokens: {state.total_tokens}, Cost: ${state.total_cost:.6f}")

        print("\n[ITERATION HISTORY]")
        for h in state.iteration_history:
            print(f"\n--- Round {h['iteration']} ---")
            print(f"Score: {h['score']}/5")
            print("Strengths:", h['feedback'].split("Strengths:")[1].split("Weaknesses:")[0].strip() if "Strengths:" in h['feedback'] else "")
            print("Weaknesses:", h['feedback'].split("Weaknesses:")[1].split("Improvements:")[0].strip() if "Weaknesses:" in h['feedback'] else "")
            print("Improvements:", h['feedback'].split("Improvements:")[1].split("Final Answer")[0].strip() if "Improvements:" in h['feedback'] else "")
            if DEBUG:
                print("\nDraft:\n", h['draft'])

if __name__ == "__main__":
    run_tests()