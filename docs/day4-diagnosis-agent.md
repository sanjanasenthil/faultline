# Faultline Day 4 Diagnosis Agent

Date: 2026-10-10

## Goal

Add the first diagnosis agent loop on top of the scrubbed Day 3 telemetry tools.

Day 4 adds a dependency-light agent that can:

- Triage service-level errors.
- Generate root-service hypotheses from metrics, traces, logs, and recent changes.
- Prefer conclusions with at least two non-change telemetry signals.
- Abstain when there is not enough evidence.
- Run against live telemetry or a saved Day 2 snapshot.

## Files

- `faultline/agent.py`: diagnosis loop and evidence scoring.
- `scripts/diagnose.py`: CLI wrapper for live and snapshot diagnosis.
- `tests/test_agent.py`: unit tests for corroborated diagnosis and abstention.

## Commands

Run the unit tests:

```sh
python3 -m unittest discover -s tests
```

Run the agent against the live demo:

```sh
python3 scripts/diagnose.py live --alert-service frontend --symptom checkout_errors
```

Run against a saved snapshot:

```sh
python3 scripts/diagnose.py snapshot snapshots/payment-failure-100-01/<timestamp>
```

## How The Agent Thinks

The agent follows four small phases:

1. Triage: summarize top services with error spans.
2. Hypothesize: score candidate root services using metrics, traces, logs, and recent changes.
3. Investigate: require two non-change evidence types for medium confidence.
4. Conclude: return a root service, confidence, reason, and supporting evidence.

This matters because recent changes can be decoys. The agent records them, but it does not treat a change record alone as enough to make a diagnosis.

## Verification Results

Ran:

```sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/flags.py scripts/cases.py scripts/telemetry.py scripts/diagnose.py faultline/scrubber.py faultline/telemetry.py faultline/agent.py
python3 scripts/diagnose.py live --alert-service frontend --symptom checkout_errors
```

Results:

- Agent and scrubber tests passed.
- The live diagnosis command returned a structured JSON diagnosis with `checkout` as the selected root service for a `frontend` / `checkout_errors` alert.
- The output passed the scrubber leakage check before printing.
- The first live run over-weighted load-generator and proxy noise; the agent now keeps those as symptom services and prefers downstream services when they have corroborated evidence.

## Current Limit

This is not yet a Claude/LangGraph agent. The current implementation is intentionally transparent and stdlib-only so the diagnosis loop can be tested without API keys or dependency installation. The next step is to wrap this evidence collector and conclusion schema with an LLM planner while keeping the same scrubbed tool boundary.
