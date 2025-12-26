# -*- coding: utf-8 -*-

import json
import logging
import requests
import tiktoken

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
SEARCH_URL = "http://localhost:8888/search"

# Configure logging to file
logging.basicConfig(
    filename="session.log",
    level=logging.INFO,
    format="%(message)s"
)

class ConversationState:
    def __init__(self):
        self.last_query = None
        self.last_keywords = None
        self.last_results = None
        self.last_summary = None
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_review_passed = False

def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_cost(token_count, price_per_1k=0.002):
    return (token_count / 1000) * price_per_1k

def query_llm(prompt, state: ConversationState):
    token_count = count_tokens(prompt)
    response = requests.post(LM_STUDIO_URL, json={
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}]
    })
    completion = response.json()["choices"][0]["message"]["content"]

    completion_tokens = count_tokens(completion)
    total_tokens = token_count + completion_tokens
    cost = estimate_cost(total_tokens)

    state.total_tokens += total_tokens
    state.total_cost += cost

    return completion, total_tokens, cost

def search_engine(keywords):
    response = requests.get(SEARCH_URL, params={"q": keywords, "format": "json"})
    return response.json()

def format_results(results, max_items=10):
    items = results.get("results", [])
    return "\n".join([f"- {item['title']} ({item['url']})" for item in items[:max_items]])

def parse_review(review_text):
    score, strengths, weaknesses, improvements, final_answer = 0, "", "", "", None
    for line in review_text.splitlines():
        if line.startswith("Score:"):
            try:
                score = int(line.split(":")[1].split("/")[0].strip())
            except:
                score = 0
        elif line.startswith("Strengths:"):
            strengths = line.replace("Strengths:", "").strip()
        elif line.startswith("Weaknesses:"):
            weaknesses = line.replace("Weaknesses:", "").strip()
        elif line.startswith("Improvements:"):
            improvements = line.replace("Improvements:", "").strip()
        elif line.startswith("Final Answer"):
            final_answer = line.replace("Final Answer (if forced):", "").strip()
    return score, strengths, weaknesses, improvements, final_answer

def log_iteration(iteration, intent, query, keywords, score, strengths, weaknesses,
                  improvements, approved, tokens_used, cost_estimate, final_answer=None):
    entry = {
        "iteration": iteration,
        "intent": intent,
        "query": query,
        "keywords": keywords,
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "approved": approved,
        "tokens_used": tokens_used,
        "cost_estimate": cost_estimate,
        "final_answer": final_answer
    }
    logging.info(json.dumps(entry))

def supervisor_loop(user_message, state: ConversationState, max_loops=8, min_sources=3):
    intent = "search"  # Simplified; you can still classify intent with LLM if needed
    query = user_message

    for i in range(max_loops):
        keywords, _, _ = query_llm(f"Generate search keywords for: {query}", state)
        results = search_engine(keywords)
        formatted = format_results(results)

        if len(results.get("results", [])) < min_sources:
            query = f"{query} (refine: not enough sources)"
            continue

        summary, tokens_used, cost = query_llm(f"Summarize these results:\n{formatted}", state)
        supervisor_prompt = f"""
You are acting as a supervisor reviewing an assistant's draft answer.

### Draft Answer
{summary}

### Evaluation Criteria
1. Accuracy - Are the facts correct and grounded in the sources?
2. Coverage - Does it include all major points or sources?
3. Clarity - Is the answer easy to read and well-structured?
4. Usefulness - Does it provide actionable insights or context?

### Instructions
- Give a score from 1 to 5 (1 = poor, 5 = excellent).
- List strengths of the draft.
- List weaknesses or missing elements.
- Suggest specific improvements for the next iteration.
- If this is the final allowed loop, force a user-facing response by rewriting the draft into the best possible answer.

### Output Format
Score: X/5
Strengths: ...
Weaknesses: ...
Improvements: ...
Final Answer (if forced): ...
"""
        review, _, _ = query_llm(supervisor_prompt, state)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review)

        state.last_query = query
        state.last_keywords = keywords
        state.last_results = results
        state.last_summary = summary

        log_iteration(
            iteration=i+1,
            intent=intent,
            query=query,
            keywords=keywords,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            improvements=improvements,
            approved=(score >= 4),
            tokens_used=tokens_used,
            cost_estimate=cost,
            final_answer=summary if score >= 4 else final_answer
        )

        if score >= 4:
            state.last_review_passed = True
            return summary
        elif i == max_loops - 1:
            state.last_review_passed = False
            return final_answer or summary
        else:
            query = f"{query} (refine: {improvements})"

    return state.last_summary or "No summary available."

if __name__ == "__main__":
    state = ConversationState()
    answer = supervisor_loop("What are the latest AI conferences in 2025?", state)
    print("\n[FINAL ANSWER]", answer)
    print("[STATUS]", "? Approved" if state.last_review_passed else "?? Best attempt")
    print(f"\n[SUMMARY] Total tokens used: {state.total_tokens}, Estimated cost: ${state.total_cost:.6f}")
