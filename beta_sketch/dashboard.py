import json
import matplotlib.pyplot as plt
import statistics

def plot_dashboard(log_file="session.log"):
    with open(log_file, "r", encoding="utf-8") as f:
        entries = [json.loads(line.strip()) for line in f if line.strip()]

    if not entries:
        print("No log entries found.")
        return

    # Group by query
    queries = {}
    for e in entries:
        q = e["query"]
        if q not in queries:
            queries[q] = []
        queries[q].append(e)

    # --- Score progression per query ---
    plt.figure(figsize=(10,6))
    for q, rounds in queries.items():
        scores = [r["score"] for r in rounds]
        plt.plot(range(1, len(scores)+1), scores, marker="o", label=q[:40]+"...")

    plt.title("Supervisor Score Progression")
    plt.xlabel("Iteration")
    plt.ylabel("Score (1–5)")
    plt.grid(True)

    # Place legend outside the chart
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # --- Token usage per query ---
    plt.figure(figsize=(10,6))
    for q, rounds in queries.items():
        tokens = [r["tokens_used"] for r in rounds]
        plt.plot(range(1, len(tokens)+1), tokens, marker="x", label=q[:40]+"...")
    plt.title("Token Usage per Iteration")
    plt.xlabel("Iteration")
    plt.ylabel("Tokens Used")
    #plt.legend()
    plt.grid(True)
    
       # Place legend outside the chart
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    
    plt.show()

    # --- Combined Summary Report ---
    print("\n=== Combined Summary Report ===")
    for q, rounds in queries.items():
        scores = [r["score"] for r in rounds]
        tokens = [r["tokens_used"] for r in rounds]
        avg_score = statistics.mean(scores)
        avg_tokens = statistics.mean(tokens)
        total_tokens = sum(tokens)
        print(f"\nQuery: {q}")
        print(f"  Avg Score: {avg_score:.2f}")
        print(f"  Avg Tokens: {avg_tokens:.0f}")
        print(f"  Total Tokens: {total_tokens}")
        print(f"  Rounds: {len(rounds)}")

if __name__ == "__main__":
    plot_dashboard()