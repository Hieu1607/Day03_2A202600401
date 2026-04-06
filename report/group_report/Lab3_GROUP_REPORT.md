# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: X100
- **Team Members**: Nguyen Quang Dang, Nguyen Minh Tuan, Nguyen Minh Hieu, Hoang Anh Quyen, Nguyen Viet Long, Do Duc Manh, Ha Huy Hoang
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

Our team transformed the baseline stock chatbot into a ReAct-style stock analysis agent with explicit tool usage, telemetry logging, and multi-provider LLM support.

Compared with the chatbot baseline, the agent design is better suited for external-data tasks because it can call stock tools before answering. The implementation includes strict ReAct formatting instructions, structured tool execution, and max-step termination to reduce runaway loops.

- **Success Rate**: Strong qualitative performance on stock tasks that require tool chaining (fetch + compare), with remaining reliability risks from model formatting variance.
- **Key Outcome**: The ReAct agent can ground answers in tool observations (`fetch_Cafef_stock`, `fetch_FireAnt_stock`, `compare_stocks`) while the baseline chatbot often cannot access real-time or multi-step data correctly.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

The runtime follows a standard ReAct control flow:
1. Receive user question.
2. Generate model output with strict `Thought`/`Action`/`Final Answer` format.
3. If `Action` is detected, execute tool and append `Observation` back to prompt.
4. Repeat until `Final Answer` or `max_steps` (default 5).

```mermaid
flowchart TD
    A[User Input] --> B[LLM Generate]
    B --> C{Output Type}
    C -->|Final Answer| D[Return Answer]
    C -->|Action: tool(args)| E[Execute Tool]
    E --> F[Observation]
    F --> B
    C -->|No Action / Parse Miss| G[Return Raw Response]
    B --> H{steps < max_steps?}
    H -->|No| I[Stop: max steps reached]
```

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `fetch_Cafef_stock` | `"<ticker>"` | Return latest 5-session mock historical data for Vietnamese stocks. |
| `fetch_FireAnt_stock` | `{"ticker":"...","start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}` | Fetch real historical quotes from FireAnt API over a date range. |
| `compare_stocks` | `{"ticker1":"...","ticker2":"..."}` | Compare 5-session percentage change between two tickers and select winner. |

### 2.3 LLM Providers Used

- **Primary baseline runner**: Groq-compatible provider (`llama-3.3-70b-versatile`) in chatbot flow.
- **Available agent providers**: OpenAI-compatible, Gemini, Local (llama-cpp), and Groq via shared provider abstraction.
- **Architecture benefit**: Provider switching is possible without changing agent loop logic.

---

## 3. Telemetry & Performance Dashboard

Telemetry is implemented with structured JSON events and a request metric tracker:
- Event logging: `AGENT_START`, `LLM_RESPONSE`, `TOOL_CALL`, `TOOL_RESULT`, `AGENT_END`, `CHATBOT_START`, `CHATBOT_END`.
- Request metrics: `provider`, `model`, token usage, latency (`latency_ms`), and mock `cost_estimate`.

Current workspace snapshot does not include exported runtime log files, so aggregate benchmark values are reported as operationally tracked but not consolidated.

- **Average Latency (P50)**: Not consolidated in current snapshot.
- **Max Latency (P99)**: Not consolidated in current snapshot.
- **Average Tokens per Task**: Collected per request when provider usage metadata is available.
- **Total Cost of Test Suite**: Estimated per request from token count; no full-suite rollup file found.

Representative metric schema captured in code:

```text
{
  "provider": "groq/openai/google/local",
  "model": "<model_name>",
  "prompt_tokens": <int>,
  "completion_tokens": <int>,
  "total_tokens": <int>,
  "latency_ms": <int>,
  "cost_estimate": <float>
}
```

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Missing Action Format / Premature Direct Answer

- **Input**: A stock query that requires external data or multi-step comparison.
- **Observed Failure Pattern**:
  - Model sometimes returns prose without a parseable `Action:` line.
  - Agent then exits through no-action path or reaches max-step without finalization.
- **Root Cause**:
  - ReAct behavior depends on strict output formatting from the LLM.
  - Prompt constraints help but cannot fully guarantee deterministic machine-parseable output on every run.

### Fixes and Mitigations Applied

- Added strict ReAct rules in system prompt:
  - Must call tools for real-time/external stock information.
  - Must avoid hallucinating values.
  - Must provide `Final Answer` only after observation.
- Added robust loop boundaries (`max_steps=5`) to prevent infinite cycles.
- Added telemetry events for each reasoning stage to speed up diagnosis.

### Result

- Better transparency and debuggability of agent behavior.
- Safer termination on malformed or drifting outputs.
- Remaining gap: deterministic routing/validation can further improve tool-call reliability.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Chatbot Baseline vs ReAct Agent

| Case | Chatbot Baseline | ReAct Agent | Winner |
| :--- | :--- | :--- | :--- |
| Simple company question | Usually acceptable | Acceptable | Draw |
| Real-time close price | Tends to guess/refuse (no tool path) | Can call stock tools and answer from observation | **Agent** |
| Two-stock comparison | Weak for grounded numeric comparison | Tool-assisted comparison available | **Agent** |
| Multi-step reasoning with external data | Limited | Designed for this workflow | **Agent** |

### Experiment 2: Provider Flexibility (Design-Level)

- **Diff**:
  - Single-provider chatbot flow vs shared provider interface (`OpenAI`, `Gemini`, `Groq`, `Local`).
- **Result**:
  - Better portability across local and cloud inference endpoints.
  - Easier benchmarking and failover planning for production-like workflows.

---

## 6. Production Readiness Review

- **Security**:
  - Move FireAnt bearer token from source code to environment variables.
  - Add strict input validation and ticker allowlist where appropriate.
- **Guardrails**:
  - Add parser-hardening for malformed `Action` arguments.
  - Add retry-and-repair step when model output breaks required format.
- **Scaling**:
  - Add log aggregation scripts for P50/P95/P99, error rates, and tool success ratios.
  - Add deterministic router for high-confidence intents before LLM loop.

---

## 7. Evidence of Code Quality and Validation

- Clear modular structure:
  - Agent loop in `src/agent/agent.py`
  - Stock tools in `src/tools/stock_tools.py`
  - Provider abstraction in `src/core/*.py`
  - Telemetry in `src/telemetry/*.py`
- Baseline evaluation cases are defined in `chatbot.py` for repeatable behavior checks.
- Error paths are handled in tools and agent (input parsing errors, request exceptions, max-step termination).

---

## 8. Group Learning Points

1. Tool grounding is the key difference between a generic chatbot and an agent for financial-data tasks.
2. Strict prompt formatting alone is not enough; production agents need parser-aware guardrails.
3. Telemetry events and per-request metrics are critical for diagnosing reliability issues quickly.
4. Provider abstraction increases resilience and experimentation speed in real deployments.

---

> [!NOTE]
> This report is based on implemented code in this workspace and follows the provided group report template.
