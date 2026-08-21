# Multi-Agent Research Analyst

An Agentic AI system that orchestrates multiple specialized sub-agents using LangGraph to produce structured, cited research briefs from complex questions.

# Report
Please Open the Report.html for more details.

## Architecture

```text
User Query
    │
    ▼
┌─────────────┐
│   PLANNER   │  Decomposes question into 3-5 sub-questions
└──────┬──────┘
       │ Fan-out (parallel)
  ┌────┼────┐
  ▼    ▼    ▼
┌───┐┌───┐┌───┐
│ R1││ R2││ R3│  Each researcher searches the web independently
└─┬─┘└─┬─┘└─┬─┘
  └────┼────┘  Fan-in (reducer merge)
       ▼
┌──────────────┐
│ SYNTHESIZER  │  Merges findings into a cohesive research brief
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    CRITIC    │  Evaluates: APPROVED → END, NEEDS_REVISION → loop back
└──────┬───────┘
       │ (max 3 iterations)
       ▼
    Final Brief
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Agent Framework | LangGraph |
| LLM | Groq (openai/gpt-oss-120b) |
| Web Search | Tavily |
| Frontend | Streamlit |
| Environment | python-dotenv |

## Project Structure

```text
multi-agent-analyst/
├── .env                    # API keys (never commit this)
├── requirements.txt         # Python dependencies
├── README.md
├── config.py               # LLM initialization, model name
├── tools.py                # Tool definitions (tavily_search, extract_page, calculator, etc.)
├── state.py                # ResearchState TypedDict definition
├── nodes.py                # Node functions (planner, researcher, synthesizer, critic)
├── graph.py                # LangGraph construction and compilation
├── baseline.py             # Single-agent baseline for comparison
├── evaluate.py             # LLM-as-Judge evaluation logic
├── run_multi.py            # Run multi-agent on multiple questions
├── app.py                  # Streamlit frontend
└── outputs/
    ├── baseline_results.json
    ├── multi_agent_results.json
    ├── evaluation_results.json
    ├── graph_image.png
    └── reports/
        ├── report_1.md
        ├── report_2.md
        ├── ...
        └── report_6.md
```

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd multi-agent-analyst
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 2. Set up API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_groq_key_here
TAVILY_KEY=tvly-your_tavily_key_here
```

**Get your keys:**
- Groq: https://console.groq.com/keys
- Tavily: https://app.tavily.com/sign-up

### 3. Verify setup

```python
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key=os.environ["GROQ_API_KEY"])
response = llm.invoke("Say hello in one word.")
print(response.content)
```

If this prints a response, you're ready.

## Usage

### Run the multi-agent system (single question)

```python
from graph import research_graph

question = "Compare the current EV strategies of Tata Motors and BYD."
result = research_graph.invoke({"question": question})

print(result["draft"])
```

### Run on multiple questions and generate reports

```python
from run_multi import run_all_questions

run_all_questions()
```

This generates 6 markdown reports in `outputs/reports/`.

### Run baseline comparison

```python
from baseline import run_baseline

result = run_baseline("Compare the current EV strategies of Tata Motors and BYD.")
print(result["answer"])
print(f"Time: {result['time_seconds']}s | Tool Calls: {result['steps']}")
```

### Run evaluation

```python
from evaluate import evaluate_both

scores = evaluate_both()
print(scores)
```

### Launch Streamlit frontend

```bash
streamlit run app.py
```

## Core Concepts

### Agent
An LLM in a loop — given a goal, it reasons, uses tools, observes results, and loops until the goal is achieved.

### Tools
Functions that perform actions in external systems — web search, page extraction, calculations. They act as the "hands" of the agent.

### Graph
Connected nodes with edges that define the flow of data and control between units of work.

### Nodes
A unit of work in the graph — a function that receives the current state, performs an operation (LLM call, tool invocation, Python logic), and returns state updates.

## Agentic Patterns Used

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| Planner–Executor | `planner_node` → Researchers | Decompose complex questions into sub-tasks |
| Orchestrator–Workers | Fan-out/fan-in to 3 researchers | Parallel execution with shared state |
| Evaluator–Optimizer | `critic_node` → `synthesizer_node` loop | Self-correcting feedback (max 3 iterations) |

## Evaluation

The multi-agent system is benchmarked against a single-agent baseline using LLM-as-Judge scoring (1–5) on:
- **Coverage** — Does it answer all parts of the question?
- **Faithfulness** — Are claims supported by citations?
- **Citation Quality** — Are sources properly referenced?
- **Coherence** — Is the brief well-structured?

## Key Learnings

1. **Cost per execution** — Multiple LLM calls multiply token consumption rapidly
2. **Latency** — Targeting sub-10ms perceived latency requires parallel execution and streaming
3. **Security** — Input/output guardrails are essential for tool-calling agents
4. **Trajectory evaluation** — Final output quality alone is insufficient; evaluate the full agent decision path

## Known Issues

- Groq free tier rate-limits parallel researcher execution (HTTP 429)
- Model names on Groq change frequently — check `client.models.list()` if you get 404 errors
- `openai/gpt-oss-120b` cannot receive ToolMessages back — use the two-call pattern (tools → execute → text-only call)

## Project Completion Flow

```text
Step 1: Import packages & modules
        ↓
Step 2: Load API keys from .env
        ↓
Step 3: Test LLM invoke (confirm model works)
        ↓
Step 4: Define tools (tavily_search, extract_page, calculator, wikipedia_search, get_financials)
        ↓
Step 5: Test each defined tool individually
        ↓
Step 6: Define ResearchState (TypedDict with question, plan, findings, draft, critique, iterations, approved)
        ↓
Step 7: Implement nodes
        ├── planner_node()       → decomposes question into sub-questions
        ├── researcher_node()    → runs ReAct loop with tools per sub-question
        ├── synthesizer_node()   → merges all findings into one draft brief
        └── critic_node()        → evaluates draft, returns APPROVED or NEEDS_REVISION
        ↓
Step 8: Build research_graph
        ├── Add nodes to StateGraph
        ├── Add edges: START → planner → researchers → synthesizer → critic
        ├── Add conditional edge: critic → synthesizer (if NEEDS_REVISION) or END (if APPROVED)
        └── Compile graph
        ↓
Step 9: Generate graph image (graph.get_graph().draw_mermaid_png())
        ↓
Step 10: Implement single-agent baseline
        ├── LLM + system prompt + tools (no planner, no orchestrator, no multi-agents)
        ├── Uses bind_tools for first call (tool selection)
        ├── Executes tools in Python
        └── Second call without tools (final answer generation)
        ↓
Step 11: Implement human-in-the-loop after planner
        ├── Add interrupt_before on researcher nodes
        ├── User reviews/edits the plan before execution
        └── User updates state and resumes graph
        ↓
Step 12: Run multi-agent on 1 question (test end-to-end)
        ↓
Step 13: Run multi-agent on 6 questions → generate 6 markdown report files
        ↓
Step 14: Implement evaluation
        ├── Run baseline on all 6 questions → save baseline_results.json
        ├── Run multi-agent on all 6 questions → save multi_agent_results.json
        ├── LLM-as-Judge scores both (Coverage, Faithfulness, Citation Quality, Coherence)
        └── Compare scores → save evaluation_results.json
```