"""Local dev runner — iterate on the agent without Harbor.

Runs the *exact* agent Harbor loads in the sandbox (`deep-agent/agent.py:make_graph`)
against a throwaway workspace seeded from the task's own knowledge base
(`dataset/<task>/environment/info/`). There is only one copy of the agent and one copy of
the knowledge base in this repo — this script reuses both rather than duplicating them.

    python dev.py                          # report on noise pollution
    python dev.py "urban beekeeping"       # any topic present in the task's info/

Requires the gateway env (ANTHROPIC_BASE_URL + the LangSmith key). Source the demo .env first:

    set -a; source .env; set +a; python dev.py
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from langchain.chat_models import init_chat_model

REPO = Path(__file__).parent.resolve()
AGENT_DIR = REPO / "deep-agent"
INFO_SRC = REPO / "dataset" / "noise-pollution-report" / "environment" / "info"
WORKSPACE = REPO / ".dev-workspace"  # gitignored scratch dir, mirrors the container's /app
MODEL = "anthropic:claude-haiku-4-5-20251001"


def _seed_workspace() -> None:
    """Recreate a clean workspace with info/ (from the task) and an empty report/."""
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    shutil.copytree(INFO_SRC, WORKSPACE / "info")
    (WORKSPACE / "report").mkdir(parents=True)


def main() -> None:
    topic = sys.argv[1] if len(sys.argv) > 1 else "noise pollution"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Gateway creds missing — run `set -a; source .env; set +a` first.")

    _seed_workspace()

    # Enter the workspace BEFORE building the graph so the agent's LocalShellBackend
    # (root_dir=".") is anchored here — mirroring /app inside the Harbor container.
    os.chdir(WORKSPACE)
    sys.path.insert(0, str(AGENT_DIR))  # import the single canonical agent
    from agent import make_graph

    graph = make_graph({"configurable": {"model": init_chat_model(MODEL)}})
    result = graph.invoke(
        {"messages": [{"role": "user", "content": f"Write a report about {topic}."}]},
        config={"configurable": {"thread_id": "dev-run"}},
    )

    print("\n=== agent final message ===")
    print(result["messages"][-1].content)
    print("\n=== files in report/ ===")
    for p in sorted((WORKSPACE / "report").glob("*.md")):
        print(f"- {p.relative_to(REPO)} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
