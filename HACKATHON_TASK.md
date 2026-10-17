# Autonomous Colo Scout: Crusoe Recursive Agents Hackathon Build Task

**Date:** October 17, 2026
**Repository:** https://github.com/joedatacap/aidatacenter2
**Owner goal:** Ship a working, demonstrably recursive agent application today, ideally in two hours, using Crusoe Managed Inference. Prioritize completion and a convincing demo over breadth.

## Product goal

An autonomous, evidence-based scout that investigates **US colocation data center opportunities with 3–30 MW of capacity and stated or plausible availability by December 31, 2027**, targeting **Tier III reliability or demonstrably equivalent reliability**.

**Important scope:**
- **DO NOT** use N+1 redundancy or liquid cooling as eligibility filters. You may collect these as optional informational fields.
- A 20 MW facility is *not* automatically an available 20 MW opportunity. Distinguish `total_facility_mw`, `marketed_capacity_mw`, and `confirmed_available_mw`.
- Differentiate **existing / under construction / proposed**, and **confirmed availability / projected availability / unknown**.
- Tier III status must be `certified | operator-claimed | equivalent-with-evidence | unverified`, with actual evidence.
- Unverified leads stay in **Needs Diligence** and are never silently promoted to verified matches.
- Country = USA; deadline inclusive = 2027-12-31.

## Hackathon alignment (critical)

The central challenge is **build an agent team you can walk away from**. We must demonstrate:
1. A manager that turns a broad goal into an executable task plan.
2. **Dynamic** spawning/delegation of subagent research tasks based on intermediate findings, not just a hardcoded four-prompt chain.
3. Agent-to-agent results, progress monitoring, and a shared durable memory/task store.
4. Evidence-verification and self-critique that generates **new follow-up tasks** if sources conflict or a critical field is unknown.
5. Bounded retries, graceful failure handling, explicit stop/completion criteria, and persistent state so closing the browser does not stop an active run.
6. A UI **activity timeline** that proves the preceding behavior happened.
7. Inference actually runs on **Crusoe Managed Inference**, preferably `nvidia/Nemotron-3-Nano-30B-A3B`, possibly `nvidia/Nemotron-3-Super-120B-A12B` for validation if working.

## Stack

- Python 3.11+, FastAPI, minimal HTML/CSS/JS with polling.
- SQLite to persist runs, tasks, agent events, site findings, and evidence.
- OpenAI Python SDK with `base_url="https://api.inference.crusoecloud.com/v1"` and API key `CRUSOE_API_KEY` from environment only.
- No heavy agent orchestration framework needed: implement a lightweight explicit agent/task loop.
- Search layer optional: use You.com if `YDC_API_KEY` configured (or other reliable search API already available). **Do not block core agent demo on search credentials**.
- Without live search, build a fully labeled `DEMO MODE` using static test fixtures with source metadata. Never make synthetic/example leads appear to be real verified opportunities.
- Never commit or log secrets; supply `.env.example` and `.gitignore` excluding `.env`, `*.db`, venv and caches.

## Sequence: BUILD, TEST, THEN POLISH

**Milestone A: Live Crusoe inference (first 15 min)**
- Test whether `CRUSOE_API_KEY` is available securely. Do not print its value.
- Call real Crusoe chat completions with a supported Nemotron model; print only model ID and sanitized response.
- If a credential or external network blocker occurs, document precisely and implement/test offline fixtures rather than stop all coding.

**Milestone B: Real autonomous loop**
- Models: `Run`, `Task` (`pending | running | completed | failed | blocked`), `AgentEvent`, `SiteLead`, `Evidence`.
- A manager generates a plan and dispatches tasks to scouts.
- Scouts retrieve leads or evaluate seeded source material; specialized analysts extract capacity/availability/reliability with citations.
- A verifier detects unsupported claims or inconsistencies and asks the manager to create a more focused new task.
- Manager dynamically decides to continue, spawn a follow-up, or stop based on completion/evidence/budget.
- Constrain recursion: <= 18 tasks total, <= 25 LLM calls per run, <= 2 retries per task, <= 5 min wall time per run. Guard against cycles and duplicate tasks.
- Persist task state before and after each transition; append event log. Recover stale `running` tasks on restart.
- A run continues in the running server even if user closes the browser.

**Milestone C: UI**
- Form with prefilled objective; Start / Resume / Stop, Run status, elapsed time.
- Timeline of manager plan, spawned subagents, research findings, verification failure, follow-up assignment and final decision.
- Ranked leads table with location, operator, available MW, deadline, reliability evidence, verification state and primary source URLs.
- Distinguish `Verified match` vs `Needs diligence` vs `Rejected`.
- Include an easily accessible demo example so judge sees a genuine failure/recovery loop.

**Milestone D: End-to-end test and submit readiness**
- Test Crusoe API, job enqueue/persistence, dynamic spawning, missing-field follow-up, capped retries, safe stop, and recovery after browser refresh (restart if feasible).
- Demo from a real source set if internet access allows. Otherwise explicitly label the demo fixtures.
- GitHub README with architecture, setup/run commands, model/Crusoe integration, screenshots or demo script, limitations, and the exact recurring autonomous loop.
- Commit working code to repository branch and prepare PR, or push to main if allowed. GitHub permissions may vary.
- Deployment is optional until working core and demo. Cloud Codex is a build environment and does NOT automatically host a durable public demo.

## Suggested demo script (90 seconds)

1. Click `Start`: goal is find 3–30 MW US colo opportunities available by 2027-12-31, Tier III equivalent.
2. Show manager planning and delegating a research task.
3. Show an initial candidate with uncertain availability.
4. Show verifier rejecting unsupported availability assertion; manager spawning an availability follow-up.
5. Show follow-up executed, and final report presenting verified / unknown separately.
6. Refresh/close/reopen browser while server stays running to prove persistence.

## Definition of done

- [ ] At least one **real** Crusoe inference request completed.
- [ ] Actual manager-driven follow-up task spawned from a verifier finding.
- [ ] Agent state and evidence persisted in SQLite.
- [ ] Viewable dashboard including an honest status timeline.
- [ ] No invented real-world capacities or dates or false certification claims.
- [ ] Unit tests pass; at least one full run completes in a documented mode.
- [ ] README plus a short demo guide.
- [ ] GitHub commits ready to submit.

## Coding-agent operating instructions

**Do the work, not just another plan.** Proceed autonomously through working code and tests, with frequent commits. Keep first end-to-end functionality tiny. Ask human only if Crusoe key is not configured or a genuine unavoidable blocker occurs. No need to ask for permission between coding steps.

Do not falsely report Crusoe calls, live search, hosting, or successful tests. If resources or authentication are missing, distinguish offline simulated tests from real API calls and tell the user exactly what is missing.
