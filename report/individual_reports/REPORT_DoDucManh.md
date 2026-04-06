# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đỗ Đức Mạnh
- **Student ID**: 2A202600037
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**: `src/tools/stock_tools.py`
- **Code Highlights**:
```python
def is_banking_stock(stock_name: str) -> str:
    """
    Check if a stock ticker belongs to the Banking sector.
    Input: stock ticker symbol (e.g. "VCB", "MBB", "SHB").
    Returns: A message confirming if it's a bank or not.
    """
    banking_tickers = ["VCB", "BID", "CTG", "TBC", "MBB", "TCB", "ACB", "VPB", "HDB", "STB", "SHB", "LPB", "TPB", "VIB", "MSB", "OCB"]
    ticker = stock_name.upper()
    if ticker in banking_tickers:
        return f"{ticker} thuộc nhóm ngành Ngân hàng (Banking)."
    return f"{ticker} không nằm trong danh sách nhóm Ngân hàng phổ biến hoặc thuộc ngành khác."
```

**System Prompt with Strict Rules (agent.py:20-44)** — Prevents hallucination by forcing tool usage:

```python
STRICT RULES:
1. You MUST call a tool using Action BEFORE giving a Final Answer
   if the question requires real-time data, stock prices, or any external information.
2. NEVER fabricate, assume, or hallucinate data.
3. Only give a Final Answer AFTER you have received real Observation data from tool calls.
4. You may call multiple tools in sequence (one per step).
```

### Documentation

The `ReActAgent` receives a user question, then enters an iterative loop:
1. The LLM generates a response following the `Thought → Action → Final Answer` format.
2. If an `Action: tool_name(args)` is detected, the agent dispatches to the matching tool in the tool registry, executes it, and appends the `Observation` back into the prompt context.
3. The loop repeats until the LLM produces a `Final Answer` or `max_steps` is reached.
4. Every stage (`AGENT_START`, `LLM_RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `AGENT_END`) is logged via the telemetry system for debugging and performance analysis.

---

## II. Debugging Case Study (10 Points)

### Problem Description

During testing, the agent occasionally produced a direct prose answer (e.g., "FPT stock is currently trading at 95,000 VND") without calling any tool. This meant the agent was **hallucinating stock prices** instead of using `fetch_CafeF_stock` or `fetch_FireAnt_stock` to retrieve real data.

### Log Source

```json
{"timestamp": "2026-04-06T09:15:32", "event": "LLM_RESPONSE", "data": {"step": 1, "response": "FPT is currently trading at approximately 95,000 VND..."}}
{"timestamp": "2026-04-06T09:15:32", "event": "AGENT_END", "data": {"steps": 1, "status": "no_action"}}
```

The agent exited through the `no_action` path (agent.py:108) after only 1 step because no `Action:` line was found in the LLM output.

### Diagnosis

The root cause was insufficient constraint in the system prompt. The LLM (llama-3.3-70b via Groq) sometimes chose to answer directly from training data rather than following the ReAct format, especially for questions that sounded like general knowledge ("What is the price of FPT?"). The model treated the ReAct instructions as optional guidance rather than mandatory rules.

### Solution

1. **Strengthened the system prompt** with explicit `STRICT RULES` (see code highlight above):
   - Rule 1: MUST call a tool before giving Final Answer for any data-dependent question.
   - Rule 2: NEVER fabricate or hallucinate data.
   - Rule 3: Only give Final Answer AFTER receiving real Observation data.
2. **Added format enforcement**: The prompt specifies `Use EXACTLY this format (no extra text before Thought)` to reduce the chance of free-form responses.
3. **Kept the `no_action` fallback** as a safety net — if the model still fails to follow format, the raw response is returned rather than entering an infinite loop.

After these changes, the agent consistently called tools before answering data-dependent questions in subsequent test runs.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning

The `Thought` block is the key differentiator. In the chatbot baseline, the LLM jumps directly to an answer — for real-time data questions this means either refusing ("I don't have access to real-time data") or hallucinating numbers. With the ReAct agent, the `Thought` block forces the model to reason about **what information it needs** and **which tool can provide it** before acting. For example:

> *Thought: The user wants the close price of FPT. I need to call fetch_CafeF_stock to get real data.*
> *Action: fetch_CafeF_stock("FPT")*

This explicit reasoning step transforms the LLM from a pattern-matching text generator into a goal-directed problem solver that can decompose multi-step tasks.

### 2. Reliability

The agent performs **worse** than the chatbot in two scenarios:
- **Simple knowledge questions** (e.g., "What is FPT company?"): The chatbot answers instantly in one round-trip, while the agent may unnecessarily call a tool or take extra steps, wasting tokens and latency.
- **When the LLM breaks format**: If the model outputs malformed `Action:` syntax (e.g., missing parentheses, wrong tool name), the agent either fails to parse the action or calls a non-existent tool, producing an error. The chatbot, having no parsing layer, never encounters this class of failure.

### 3. Observation

The `Observation` feedback loop is critical for grounded reasoning. After receiving real data from a tool call, the agent can:
- Adjust its next action based on actual values (e.g., calling `calculate` after seeing raw price data).
- Chain multiple tools together (e.g., `fetch_FireAnt_stock` -> `calculate` -> `Final Answer`).
- Self-correct if the first tool call returns an error (e.g., retrying with corrected arguments).

Without observations, the agent would be no better than the chatbot — it would just be guessing with extra steps. The observation transforms the loop from "LLM talking to itself" into "LLM interacting with the real world."

---

## IV. Future Improvements (5 Points)

### Scalability
- **Asynchronous tool execution**: Use `asyncio` for concurrent tool calls when the agent needs data from multiple independent sources (e.g., fetching two stocks simultaneously for comparison).
- **Conversation memory**: Replace the current prompt-concatenation approach with a proper message history or vector store to handle longer multi-turn interactions without exceeding context limits.

### Safety
- **Output validator / Supervisor LLM**: Add a lightweight validation layer that checks the agent's `Final Answer` against the `Observation` data to catch remaining hallucinations before returning to the user.
- **Input sanitization**: Move the FireAnt bearer token from source code to environment variables. Add a ticker allowlist to prevent injection of arbitrary strings into API calls.

### Performance
- **Tool routing with intent classification**: Use a fast classifier to detect whether a question requires tools at all. Simple knowledge questions can bypass the ReAct loop entirely, reducing unnecessary latency and token usage.
- **Caching layer**: Cache tool results for repeated queries (e.g., same ticker within a short time window) to reduce API calls and improve response time.

---

> [!NOTE]
> This report is authored by Nguyen Minh Hieu (2A202600401) based on implemented code in this workspace.
