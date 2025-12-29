import re
import requests
import json
import logging
import tiktoken

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
SEARCH_URL = "http://localhost:8888/search"

logging.basicConfig(filename="session.log", level=logging.INFO, format="%(message)s")

class ConversationState:
    def __init__(self):
        self.last_query = None
        self.last_intent = None
        self.last_draft = None
        self.last_feedback = None
        self.sources_used = []
        self.iteration_history = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_review_passed = False

# --- Token + Cost ---
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def estimate_cost(token_count, price_per_1k=0.002):
    return (token_count / 1000) * price_per_1k

# --- LLM Query ---
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

# --- Intent Classification ---
def classify_intent(user_message, state: ConversationState):
    intent_prompt = f"""
Classify the user request into one of these categories:
- Summary
- List
- Comparison
- Recommendation
- Explanation
- Step-by-Step Plan

User request: "{user_message}"

Answer with only the category name.
"""
    intent, _, _ = query_llm(intent_prompt, state)
    state.last_intent = intent.strip()
    return state.last_intent

# --- Search + Deep Fetch ---
def search_engine(keywords):
    response = requests.get(SEARCH_URL, params={"q": keywords, "format": "json"})
    return response.json()

def deep_fetch(url):
    try:
        page = requests.get(url, timeout=5)
        return page.text[:800]  # trim for demo
    except:
        return ""

def format_results(results, max_items=5):
    items = results.get("results", [])
    formatted = []
    for item in items[:max_items]:
        snippet = item.get("content", "") or deep_fetch(item["url"])
        formatted.append(f"- {item['title']} ({item['url']})\n{snippet}")
    return "\n".join(formatted)

# --- Build Generation Prompt ---
def build_generation_prompt(intent, formatted_results, user_message, last_draft=None, last_feedback=None):
    continuity = ""
    if last_draft and last_feedback:
        continuity = f"\nPrevious Draft:\n{last_draft}\nSupervisor Feedback:\n{last_feedback}\n"
    return f"{continuity}\nUser Request:\n{user_message}\n\nTask: Produce a {intent} using these sources:\n{formatted_results}"

# --- Supervisor Prompt (strict format) ---
def build_supervisor_prompt(intent, draft_answer):
    return f"""
You are acting as a supervisor reviewing an assistant’s draft {intent}.

### Draft {intent}
{draft_answer}

### Evaluation Criteria
- Accuracy
- Coverage
- Clarity
- Usefulness

### Instructions
Respond ONLY in this exact format:

Score: X/5
Strengths: …
Weaknesses: …
Improvements: …
Final Answer (if forced): …
"""

# --- Parse Supervisor Feedback (regex) ---
def parse_review(review_text):
    score_match = re.search(r"Score:\s*(\d)", review_text)
    score = int(score_match.group(1)) if score_match else 0

    strengths_match = re.search(r"Strengths:\s*(.*)", review_text)
    weaknesses_match = re.search(r"Weaknesses:\s*(.*)", review_text)
    improvements_match = re.search(r"Improvements:\s*(.*)", review_text)
    final_match = re.search(r"Final Answer.*:\s*(.*)", review_text)

    strengths = strengths_match.group(1).strip() if strengths_match else ""
    weaknesses = weaknesses_match.group(1).strip() if weaknesses_match else ""
    improvements = improvements_match.group(1).strip() if improvements_match else ""
    final_answer = final_match.group(1).strip() if final_match else None

    return score, strengths, weaknesses, improvements, final_answer

# --- Logging ---
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

# --- Supervisor Loop ---
def supervisor_loop(user_message, state: ConversationState, max_loops=5, min_sources=1):
    intent = classify_intent(user_message, state)
    query = user_message

    for i in range(max_loops):
        keywords, _, _ = query_llm(f"Generate search keywords for: {query}", state)
        results = search_engine(keywords)
        formatted = format_results(results)

        gen_prompt = build_generation_prompt(intent, formatted, user_message, state.last_draft, state.last_feedback)
        draft, tokens_used, cost = query_llm(gen_prompt, state)

        supervisor_prompt = build_supervisor_prompt(intent, draft)
        review, _, _ = query_llm(supervisor_prompt, state)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review)

        state.last_query = query
        state.last_draft = draft
        state.last_feedback = review
        state.iteration_history.append({"iteration": i+1, "score": score, "draft": draft, "feedback": review})

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
            final_answer=draft if score >= 4 else final_answer
        )

        if score >= 4:
            state.last_review_passed = True
            return draft
        elif i == max_loops - 1:
            state.last_review_passed = False
            return final_answer or draft
        else:
            query = f"{query} (refine: {improvements})"

    return state.last_draft or "No draft available."

if __name__ == "__main__":
    state = ConversationState()
    answer = supervisor_loop("Compare NeurIPS and ICML in terms of focus, scale, and industry relevance.", state)
    print("\n[FINAL ANSWER]", answer)
    print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")
    print(f"\n[SUMMARY] Total tokens used: {state.total_tokens}, Estimated cost: ${state.total_cost:.6f}")
    print("\n[ITERATION HISTORY]")
    for h in state.iteration_history:
        print(f"Round {h['iteration']} → Score {h['score']}/5")