# Lab 3: Chatbot vs ReAct Agent (Industry Edition)

Welcome to Phase 3 of the Agentic AI course! This lab focuses on moving from a simple LLM Chatbot to a sophisticated **ReAct Agent** with industry-standard monitoring.

## 🚀 Getting Started

### 1. Setup Environment
Copy the `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

Recommended Python version (keep everyone consistent):
- `3.11` (see `.python-version`)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL (Docker)
This project uses PostgreSQL for products, inventory, coupons, shipping rules, and FAQs.

```bash
docker compose up -d postgres
```

If you prefer quick scripts:
- Windows PowerShell: `./scripts/run_postgres.ps1`
- macOS/Linux: `./scripts/run_postgres.sh`

### 3b. Run Full Stack with Docker
This starts PostgreSQL, FastAPI, and Streamlit together.

```bash
docker compose up -d --build
```

Services after startup:
- FastAPI: `http://127.0.0.1:8000`
- Streamlit: `http://127.0.0.1:8501`
- PostgreSQL: `127.0.0.1:5432`

Quick scripts:
- Windows PowerShell: `./scripts/run_stack.ps1`
- macOS/Linux: `./scripts/run_stack.sh`

### 4. Run Backend (FastAPI)
```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Quick scripts:
- Windows PowerShell: `./scripts/run_backend.ps1`
- macOS/Linux: `./scripts/run_backend.sh`

### 5. Run Frontend (Streamlit)
```bash
streamlit run streamlit_app.py --server.port 8501
```

Quick scripts:
- Windows PowerShell: `./scripts/run_frontend.ps1`
- macOS/Linux: `./scripts/run_frontend.sh`

### ✅ Quick Check for Phase 6-9
If Docker/Postgres is not available yet, the app will automatically fall back to bundled seed data (`fallback-seed`) so you can still demo locally.

Useful checks:
```bash
# API smoke test
pytest -q

# 5-case benchmark for v1 vs v2
python scripts/run_benchmark.py
```

What to expect:
- `/api/v1/health` returns `status: ok`
- `streamlit_app.py` shows compare mode, history, and metrics summary
- `logs/benchmarks/benchmark_latest.json` is generated after running the benchmark

### 3. Directory Structure
- `src/tools/`: Extension point for your custom tools.

## 🏠 Running with Local Models (CPU)

If you don't want to use OpenAI or Gemini, you can run open-source models (like Phi-3) directly on your CPU using `llama-cpp-python`.

### 1. Download the Model
Download the **Phi-3-mini-4k-instruct-q4.gguf** (approx 2.2GB) from Hugging Face:
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- Direct Download: [phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

### 2. Place Model in Project
Create a `models/` folder in the root and move the downloaded `.gguf` file there.

### 3. Update `.env`
Change your `DEFAULT_PROVIDER` and set the path:
```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 🎯 Lab Objectives

1.  **Baseline Chatbot**: Observe the limitations of a standard LLM when faced with multi-step reasoning.
2.  **ReAct Loop**: Implement the `Thought-Action-Observation` cycle in `src/agent/agent.py`.
3.  **Provider Switching**: Swap between OpenAI and Gemini seamlessly using the `LLMProvider` interface.
4.  **Failure Analysis**: Use the structured logs in `logs/` to identify why the agent fails (hallucinations, parsing errors).
5.  **Grading & Bonus**: Follow the [SCORING.md](file:///Users/tindt/personal/ai-thuc-chien/day03-lab-agent/SCORING.md) to maximize your points and explore bonus metrics.

## 🛠️ How to Use This Baseline
The code is designed as a **Production Prototype**. It includes:
- **Telemetry**: Every action is logged in JSON format for later analysis.
- **Robust Provider Pattern**: Easily extendable to any LLM API.
- **Clean Skeletons**: Focus on the logic that matters—the agent's reasoning process.

---

*Happy Coding! Let's build agents that actually work.*
