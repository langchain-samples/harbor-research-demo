# Base image with Python so Harbor can install and run the langgraph agent inside the
# container. The build context is this `environment/` directory.
FROM python:3.12-slim

# git is occasionally needed when pip resolves VCS-based dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Seed the research knowledge base and an empty report/ folder into the working directory.
# The agent reads from info/ and writes its report into report/; the verifier reads report/.
COPY info/ /app/info/
RUN mkdir -p /app/report
