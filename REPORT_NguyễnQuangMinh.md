# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Quang Minh
- **Student ID**: 2A202600195
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

### Modules Implemented

- `src/agent/agent.py`
- `src/core/openai_provider.py` (modified to OpenRouter LLaMA)
- `tests/test_local.py` (converted to agent test)
- Tool execution logic (`trade_yes`, `trade_no`)

---

### Code Highlights

#### Robust Action Parsing
```python
args = re.sub(r"[a-zA-Z_]+\s*=\s*", "", args)
```

#### Flexible Final Answer Extraction
```python
num_match = re.search(r"([0-9]*\.?[0-9]+)", final_answer)
```

#### Early Stop Condition
```python
if "Final Answer:" in output:
    break
```

- **Documentation**: The system follows a ReAct loop adapted to a prediction market setting:

The user query is interpreted as a forecasting problem
The LLM generates reasoning (Thought) and proposes a market action (Action)
The system executes the action via a tool (trade_yes or trade_no)
The resulting updated probability is returned as Observation
The Observation is appended to the context and fed back into the model
The loop continues until a Final Answer is produced or max steps are reached

This simulates a simplified market where beliefs are updated iteratively.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

Problem Description

The agent initially failed with the error:

'NoneType' object is not subscriptable

This occurred during LLM response parsing when the model returned an empty response.

Log Source

From logs:

DEBUG RAW OUTPUT:
Error: Empty response from model
Diagnosis

The failure was caused by multiple factors:

OpenRouter occasionally returns empty responses
LLaMA models are less reliable in structured output formatting
The system assumed valid outputs and did not handle null responses safely

Additionally, formatting inconsistencies caused parsing failures:

trade_yes (input = 0.5)

instead of:

trade_yes(0.5)
Solution
Added fallback handling for empty responses:
if not content:
    content = "Error: Empty response from model"
Improved parser robustness:
Removed named arguments like input =
Extracted numeric values using regex
Allowed flexible formats for tool calls
Introduced defensive logging:
Logged raw LLM output at each step
Logged parser failures explicitly
Added loop guardrails:
Maximum step limit (max_steps = 5)
Early termination when Final Answer is detected

These changes made the agent stable even with weaker instruction-following models.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. Reasoning

The ReAct framework significantly improves reasoning quality.

A standard chatbot produces a single response, often:

shallow
non-transparent
inconsistent under conflicting signals

In contrast, the ReAct agent:

explicitly decomposes reasoning into steps
forces the model to justify actions
produces interpretable intermediate decisions

This is especially valuable in financial contexts where explainability matters.

2. Reliability

The agent performs worse than a chatbot in certain scenarios:

When the model fails to follow strict formatting
When tool parsing breaks due to inconsistent syntax
When the model continues reasoning indefinitely without converging

This issue is amplified when using LLaMA instead of GPT:

Higher variance in outputs
Less adherence to structured prompts
More frequent formatting drift

Thus, agent systems require significantly more engineering effort to ensure reliability.

3. Observation Feedback

The Observation step is the most important component of the ReAct loop.

It acts as:

environmental feedback
a grounding mechanism
a way to simulate state updates (in this case, market price changes)

Without Observation:

the model cannot refine its beliefs
reasoning becomes static

With Observation:

the agent dynamically adjusts predictions
behavior resembles a real prediction market

This transforms the system from a static chatbot into an interactive decision-making process.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

Scalability

To extend this into a full multi-agent prediction market:

Introduce specialized agents:
Data Agent (technical indicators)
Macro Agent (economic signals)
News Agent (sentiment analysis)
Risk Agent (downside scenarios)
Use asynchronous communication:
Redis message queues
event-driven architecture
Aggregate agent outputs into a shared market
Safety
Implement a Supervisor LLM to validate actions
Add strict schema validation for tool inputs
Prevent extreme or invalid probability outputs
Add guardrails against prompt injection
Performance
Cache repeated prompts to reduce cost
Use smaller models for intermediate reasoning steps
Introduce a vector database for:
tool retrieval
memory augmentation
Optimize loop termination to reduce unnecessary tokens

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
