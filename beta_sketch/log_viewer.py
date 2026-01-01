import json

def view_log(log_file="session.log"):
    with open(log_file, "r", encoding="utf-8") as f:
        entries = [json.loads(line.strip()) for line in f if line.strip()]

    if not entries:
        print("No log entries found.")
        return

    print("\n=== Session Log Report ===")
    for e in entries:
        print(f"\nIteration {e['iteration']} ({e['intent']})")
        print(f"Query: {e['query']}")
        print(f"Score: {e['score']}/5 | Approved: {e['approved']}")
        print(f"Strengths: {e['strengths']}")
        print(f"Weaknesses: {e['weaknesses']}")
        print(f"Improvements: {e['improvements']}")
        print(f"Tokens: {e['tokens_used']} | Cost: ${e['cost_estimate']:.6f}")
        if e['final_answer']:
            print(f"Final Answer (excerpt): {e['final_answer'][:200]}...")

if __name__ == "__main__":
    view_log()