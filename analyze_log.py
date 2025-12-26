import json

def analyze_session_log(log_file="session.log"):
    scores = []
    tokens = 0
    cost = 0.0
    improvements = []
    approved_count = 0
    total_iterations = 0

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            total_iterations += 1
            scores.append(entry.get("score", 0))
            tokens += entry.get("tokens_used", 0)
            cost += entry.get("cost_estimate", 0.0)
            if entry.get("approved"):
                approved_count += 1
            if entry.get("improvements"):
                improvements.append(entry["improvements"])

    if total_iterations == 0:
        print("No log entries found.")
        return

    avg_score = sum(scores) / len(scores) if scores else 0
    approval_rate = approved_count / total_iterations * 100

    print("\n=== Session Analysis Report ===")
    print(f"Total iterations: {total_iterations}")
    print(f"Average score: {avg_score:.2f}/5")
    print(f"Approval rate: {approval_rate:.1f}%")
    print(f"Total tokens used: {tokens}")
    print(f"Estimated cost: ${cost:.6f}")
    print("\nImprovement Suggestions Across Iterations:")
    for i, imp in enumerate(improvements, 1):
        print(f"{i}. {imp}")
