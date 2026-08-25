"""Research deep agent used as the agent-under-test for the Harbor eval.

Harbor's `--agent langgraph` loads the `deep_agent` graph declared in
`langgraph.json` and calls `make_graph(config)` once per trial. The model is
injected by Harbor via `config["configurable"]["model"]` (resolved from the
`--model` flag), so this factory stays model-agnostic.

The agent runs *inside* the Harbor sandbox container. `LocalShellBackend` gives
it real shell + filesystem access rooted at the container working directory
(`/app`), which is where the verifier later reads the generated report from.
`virtual_mode=True` still writes real files on disk but jails every path to the
working directory (blocks `..`/`~`), so the agent cannot wander outside `/app`.
"""

from __future__ import annotations

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

_SYSTEM_PROMPT = """You are a research assistant that writes short reports from a local markdown knowledge base.

Your working directory is the root of a filesystem with exactly two folders:
  - `info/`   : source material. One markdown file per topic (e.g. `info/noise_pollution.md`).
  - `report/` : the folder where you MUST save every report you generate.

When you are asked to generate a report about a topic, follow these steps:
  1. List the files in `info/` and choose the single file whose topic best matches the
     request (for "noise pollution" that is `info/noise_pollution.md`).
  2. Read that file in full.
  3. Write the report as a markdown file into `report/`, named after the topic
     (for example `report/noise-pollution-report.md`).

FORMAT REQUIREMENT — the body of every report MUST be exactly THREE paragraphs. Not two,
not four — exactly three paragraphs of prose. After the three paragraphs you MUST include a
final section whose heading is `## Sources`, listing the reference URLs found in the source
file. The Sources section does not count as a paragraph.

The report must be based on and reference the content of the `info/` file you read, and must
carry over the reference URLs from that file into the Sources section.

When you have written the report, stop.
"""


def make_graph(config):
    """Build the research agent. Called once per trial by Harbor's langgraph agent."""
    model = config["configurable"]["model"]
    return create_deep_agent(
        model=model,
        system_prompt=_SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=".", virtual_mode=True),
    )
