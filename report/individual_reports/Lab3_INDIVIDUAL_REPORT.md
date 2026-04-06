# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Minh Hieu
- **Student ID**: 2A202600401
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

- **Project Initialization & Scaffolding**: Set up the repository structure, created the initial commit, and pushed the full project skeleton including all core modules in the `group commit` (`f8e3749`).
- **`src/agent/agent.py`**: Implemented the `ReActAgent` class with the full Thought-Action-Observation loop, including:
  - System prompt construction with strict ReAct formatting rules.
  - Iterative reasoning loop with `max_steps` termination.
  - Regex-based parsing for `Action:` and `Final Answer:` blocks.
  - Tool dispatch via `_execute_tool()` with error handling.
- **`src/core/` (Provider Abstraction)**: Set up all LLM provider modules — `llm_provider.py` (base interface), `groq_provider.py`, `openai_provider.py`, `gemini_provider.py`, `local_provider.py` — enabling seamless provider switching.
- **`src/telemetry/`**: Set up the telemetry subsystem — `logger.py` (structured JSON event logging) and `metrics.py` (`PerformanceTracker` with token/latency/cost tracking).
- **`chatbot.py`**: Implemented the chatbot baseline with 4 test cases demonstrating limitations of a tool-less LLM on real-time data and multi-step reasoning tasks.

### Code Highlights

**ReAct Loop (agent.py:55-114)** — The core reasoning loop that drives the agent:

```python
while steps < self.max_steps:
    result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
    response_text = result["content"]

    # Check for Final Answer
    final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL)
    if final_match:
        return final_match.group(1).strip()

    # Parse Action
    action_match = re.search(r"Action:\s*(\w+)\((.*)?\)", response_text, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        tool_args = (action_match.group(2) or "").strip()
        observation = self._execute_tool(tool_name, tool_args)

        # Append exchange to prompt for next iteration
        current_prompt = (
            f"{current_prompt}\n\n"
            f"{response_text}\n"
            f"Observation: {observation}\n"
        )
    else:
        return response_text.strip()

    steps += 1
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
