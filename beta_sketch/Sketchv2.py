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
def compress_with_llm(text, state: ConversationState, role="draft"):
    if not text:
        return ""
    prompt = f"""
Summarize the following {role} into a concise version under 200 words.
Preserve all key information, context, and improvement points.
Do not omit important details.

Text:
{text}
"""
    summary, _, _ = query_llm(prompt, state)
    return summary
    
def compress_text(text, max_len=800):
    """Trim drafts/feedback to avoid token bloat."""
    return text[:max_len] if text else ""

def compress_sources(results, max_items=5, max_len=300):
    """Summarize sources before feeding into generation prompt."""
    items = results.get("results", [])
    formatted = []
    for item in items[:max_items]:
        snippet = item.get("content", "")[:max_len]
        formatted.append(f"- {item['title']} ({item['url']})\n{snippet}")
    return "\n".join(formatted)

def build_generation_prompt(intent, formatted_results, user_message, last_draft=None, last_feedback=None, state=None):
    continuity = ""
    if last_draft and last_feedback and state:
        continuity = (
            f"\nPrevious Draft (summary):\n{compress_with_llm(last_draft, state, role='draft')}\n"
            f"Supervisor Feedback (summary):\n{compress_with_llm(last_feedback, state, role='feedback')}\n"
        )
    return f"{continuity}\nUser Request:\n{user_message}\n\nTask: Produce a {intent} using these sources (summarized):\n{formatted_results}"

def build_supervisor_prompt(intent, draft_answer, round_num):
    return f"""
You are reviewing a draft {intent}.

### Draft {intent}
{draft_answer}

### Evaluation Criteria
- Must integrate at least 3 distinct sources.
- Must include context (dates, locations, examples).
- Must synthesize perspectives, not just list facts.
- Must highlight gaps, contradictions, or uncertainties.
- Must use a professional tone suitable for publication.

Escalating Standards:
- Round 1: Basic coverage.
- Round 2: Add ≥3 sources.
- Round 3: Integrate perspectives, highlight contradictions.
- Round 4+: Professional polish, citations, synthesis.

Scoring Rules:
1 = poor, missing most criteria
2 = weak, partial coverage
3 = adequate, but shallow
4 = strong, but still improvable
5 = professional quality, all criteria met

Dynamic Strictness:
- Early rounds (1–2): allow 2–3 if partial coverage.
- Later rounds (≥3): do NOT give 4 or 5 unless ALL criteria are satisfied.

Respond ONLY in this format:

Score: X/5
Strengths: …
Weaknesses: …
Improvements: …
Final Answer (if forced): …
"""

DEEP_RESEARCH = True  # Toggle this flag per query

def supervisor_loop(user_message, state: ConversationState, max_loops=None, min_sources=1):
    intent = classify_intent(user_message, state)
    query = user_message

    # Adjust loop depth and strictness based on mode
    if DEEP_RESEARCH:
        max_loops = max_loops or 10
        strictness = "High"
    else:
        max_loops = max_loops or 3
        strictness = "Normal"

    for i in range(max_loops):
        keywords, _, _ = query_llm(f"Generate search keywords for: {query}", state)
        results = search_engine(keywords)
        formatted = compress_sources(results)

        gen_prompt = build_generation_prompt(
            intent, formatted, user_message,
            state.last_draft, state.last_feedback, state
        )
        draft, tokens_used, cost = query_llm(gen_prompt, state)

        supervisor_prompt = build_supervisor_prompt(intent, draft, i+1)
        review, _, _ = query_llm(supervisor_prompt, state)
        score, strengths, weaknesses, improvements, final_answer = parse_review(review)

        state.last_query = query
        state.last_draft = draft
        state.last_feedback = review
        state.iteration_history.append({
            "iteration": i+1,
            "score": score,
            "draft": draft,
            "feedback": review
        })

        log_iteration(
            iteration=i+1,
            intent=intent,
            query=query,
            keywords=keywords,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            improvements=improvements,
            approved=(score >= 4 and not improvements),
            tokens_used=tokens_used,
            cost_estimate=cost,
            final_answer=draft if (score >= 4 and not improvements) else final_answer
        )

        # Guided refinement: always push for sources, contradictions, examples
        if score < 4 or improvements:
            query = (
                f"{user_message}\nRefine by: {improvements}\n"
                f"Add at least 3 credible sources, highlight contradictions, expand with concrete examples."
            )

        if score >= 4 and not improvements:
            state.last_review_passed = True
            return draft
        elif i == max_loops - 1:
            state.last_review_passed = False
            return draft  # Always return the last draft for review

    return state.last_draft or "No draft available."
    
import re
import datetime

def safe_filename_from_query(query, suffix=".md"):
    # Lowercase and replace spaces with underscores
    fname = query.lower().strip().replace(" ", "_")
    # Remove unsafe characters
    fname = re.sub(r'[^a-z0-9_\-]', "", fname)
    # Truncate if too long
    if len(fname) > 50:
        fname = fname[:50]
    # Add timestamp suffix (YYYYMMDD_HHMMSS)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{fname}_{timestamp}{suffix}"
    
def save_markdown(content, query, history=None):
    filename = safe_filename_from_query(query)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Final Generated Answer\n\n")
        f.write(content)
        if history:
            f.write("\n\n---\n\n# Iteration History\n")
            for h in history:
                f.write(f"\n## Round {h['iteration']} (Score {h['score']}/5)\n")
                f.write(f"\n**Draft:**\n\n{h['draft']}\n")
                f.write(f"\n**Feedback:**\n\n{h['feedback']}\n")
    print(f"Markdown file saved as {filename}")
    
if __name__ == "__main__":
    state = ConversationState()
    answer = supervisor_loop("Compare NeurIPS and ICML in terms of focus, scale, and industry relevance.", state)
    print("\n[FINAL ANSWER]", answer)
    print("[STATUS]", "✅ Approved" if state.last_review_passed else "⚠️ Best attempt")
    print(f"\n[SUMMARY] Total tokens used: {state.total_tokens}, Estimated cost: ${state.total_cost:.6f}")
    print("\n[ITERATION HISTORY]")
    for h in state.iteration_history:
        print(f"Round {h['iteration']} → Score {h['score']}/5")