#!/bin/bash
# Reference ("oracle") solution: the matching info/ file already has a title, three body
# paragraphs, and a Sources section, so a correct report is that file copied into report/.
# Runs from the working directory (/app). Use with `harbor check` to sanity-check the task.
set -euo pipefail
mkdir -p report
cp "info/urban_beekeeping.md" "report/urban-beekeeping-report.md"
echo "wrote report/urban-beekeeping-report.md"
