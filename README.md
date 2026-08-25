# Harbor + LangSmith research-agent demo

A [deepagents](https://github.com/langchain-ai/deepagents) research agent, evaluated with
[Harbor](https://www.harborframework.com/) and recorded to LangSmith as an experiment.
The agent reads a local markdown knowledge base and writes a 3-paragraph report; a pytest
verifier checks the output and produces a reward.

📊 **Slides:** [`presentation-deck.html`](./presentation-deck.html) — a self-contained walkthrough
of the demo (open in a browser; arrow keys / click to advance).

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13 (uv installs it if missing).

```bash
# 1. Install dependencies into a local .venv (creates uv.lock on first run)
uv sync

# 2. Add your LangSmith key
cp .env.example .env
# then edit .env — ANTHROPIC_API_KEY and LANGSMITH_API_KEY are both your LangSmith key

# 3. Run the agent locally against one task's knowledge base
set -a; source .env; set +a
uv run python dev.py                    # report on noise pollution
uv run python dev.py "urban beekeeping" # any topic present in the task's info/
```

`uv run` executes inside the project's `.venv` — no manual activation needed.

## Model routing

All model calls go through the LangChain gateway (`gateway.smith.langchain.com`), authenticated
with the LangSmith key — never the Anthropic API directly. See `.env.example` for the full set of
variables; `ANTHROPIC_API_KEY` and `LANGSMITH_API_KEY` are the same LangSmith key.

## Full eval

Run the whole dataset on a LangSmith sandbox, recorded as an experiment:

```bash
set -a; source .env; set +a
uv run harbor run -p ./dataset --agent langgraph \
  --ak project_path=./deep-agent --ak graph=deep_agent \
  --env langsmith \
  --model anthropic:claude-haiku-4-5-20251001 \
  --plugin langsmith --pk dataset_name=demo-reports --pk experiment_name=research-agent-reports \
  --ae ANTHROPIC_BASE_URL="$ANTHROPIC_BASE_URL" \
  --ae ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --ae LANGSMITH_API_KEY="$LANGSMITH_API_KEY" \
  --ae LANGSMITH_TRACING=true \
  --ae LANGSMITH_ENDPOINT="$LANGSMITH_ENDPOINT" \
  --ae LANGSMITH_PROJECT=harbor-report-demo \
  -y
```

Swap `--env langsmith` for `--env docker` to run locally. Results appear in LangSmith under
**Datasets & Experiments → demo-reports**.

## Layout

```
harbor-report-demo/
├── pyproject.toml                  # dependencies (managed by uv; uv.lock is committed)
├── deep-agent/                     # THE agent (single source of truth)
│   ├── agent.py                    #   create_deep_agent + LocalShellBackend + make_graph(config)
│   └── langgraph.json              #   graph entrypoint + pinned deps (Harbor installs these)
├── dataset/                        # the Harbor "dataset" = a folder of tasks (4 here)
│   ├── noise-pollution-report/     # one Harbor task
│   │   ├── task.toml               #   task config (schema 1.4, from `harbor task init`)
│   │   ├── instruction.md          #   the per-task prompt handed to the agent (topic varies)
│   │   ├── environment/
│   │   │   ├── Dockerfile          #   seeds info/ + empty report/ into the container's /app
│   │   │   └── info/*.md           #   the knowledge base (all 4 topics; agent picks the match)
│   │   ├── solution/solve.sh       #   oracle solution (sanity-checks the task)
│   │   └── tests/
│   │       ├── test_outputs.py     #   topic-agnostic pytest verifier (3 paragraphs + grounded in KB)
│   │       └── test.sh             #   runs pytest → writes /logs/verifier/reward.txt
│   ├── coffee-history-report/      # same shape, topic = history of coffee
│   ├── deep-sea-report/            # same shape, topic = deep sea exploration
│   └── urban-beekeeping-report/    # same shape, topic = urban beekeeping
├── dev.py                          # local runner: imports deep-agent, runs vs a scratch copy of info/
└── .env                            # gateway + LangSmith creds (gitignored; see .env.example)
```

The agent lives in exactly one place (`deep-agent/agent.py`); `dev.py` imports it rather than
copying it, and reuses the task's `environment/info/` as the knowledge base.
