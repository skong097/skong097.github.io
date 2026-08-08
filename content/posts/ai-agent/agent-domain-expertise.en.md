---
title: "Fine-Tuning Is the Ninth Option — Making an Agent a Domain Expert"
date: 2026-08-08
tags: ["ai-agent", "llm", "rag", "fine-tuning", "sft", "rl", "evaluation", "verifier", "context-engineering", "second-brain", "knowledge-management"]
categories: ["ai-agent"]
summary: "When people want an agent to become an expert in some domain, they reach for training. But the real bottleneck is usually not knowing things — it is finding out quickly that you were wrong. This breaks 'not an expert yet' into four distinct deficits, then lays out a nine-rung cost ladder from cheapest to most expensive. Which material is actually worth feeding it, and what works better than training at all."
draft: false
ShowToc: true
TocOpen: true
---

A few days ago, while researching something, I watched an agent be wrong very convincingly. It told me about a GitHub repository called `hivemoot/hivemoot-agent`, complete with a description of what the project did. No such repository exists.

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://api.github.com/repos/hivemoot/hivemoot-agent
# 404

# control — the endpoint itself is not dead
curl -s -o /dev/null -w "%{http_code}\n" https://api.github.com/repos/bigscience-workshop/petals
# 200
```

The real repository was `hivemoot/hivemoot`. What interests me is that **this failure cannot be fixed with knowledge.** Feeding it more repository listings does not help. Reaching for a bigger model does not help. One line of `curl` does.

That is where this post starts. Ask "how should I train an agent to become an expert in my domain" and most answers begin with fine-tuning. My conclusion runs the other way: **changing weights belongs at the bottom of the ladder, and most problems are solved on the eight rungs above it.**

---

## 1. "Not an expert yet" is four different illnesses

Before choosing a fix, work out **which deficit you actually have.** Skipping this step is why people jump straight to training.

{{< figure src="/images/diagrams/agent-deficit-quadrant-en.svg" alt="Four deficits behind an agent that is not yet an expert — knowledge, procedure, judgment and grounding — each with its symptom, its fix, and what not to do. The grounding gap is the most common." >}}

| Deficit | Symptom | Fix | Don't |
|---|---|---|---|
| **1. Knowledge** — doesn't know | Gets facts, APIs, specs wrong | Retrieval/RAG, inject the docs | Fine-tune — facts go stale, weights can't chase them |
| **2. Procedure** — wrong order | Every step is right, the sequence isn't | Workflows, checklists, scaffolding | Just write a longer prompt |
| **3. Judgment** — can't choose | Argues both sides plausibly, never decides | Decision corpus, small SFT, review loops | RAG — judgment isn't retrievable |
| **4. Grounding** — can't check | **Confidently wrong** | **Tools, verifiers, a real environment** | Reach for a bigger model |

In my experience the fourth is overwhelmingly the most common. The `hivemoot-agent` incident above is exactly that. And the fourth is not a problem of model capability but **a problem of plumbing**, which makes it the cheapest one to fix.

Confusing the third for the first is also common. If you diagnosed "it just doesn't know our domain," shovelled in documentation, and it still refuses to decide — that was never a knowledge gap. Judgment isn't written down in the docs.

---

## 2. The cost ladder — work down from the top

Once you have a diagnosis, the fixes have an order. Cheap at the top, expensive further down.

{{< figure src="/images/diagrams/agent-expertise-ladder-en.svg" alt="A nine-rung cost ladder for making an agent a domain expert: build an eval set, context design, verifiers and tools, retrieval, memory, workflow decomposition, trajectory SFT, RL or best-of-N, and continual pretraining. Only the last three rungs change weights." >}}

| # | Method | Cost | Impact | When to drop a rung |
|:--:|---|:--:|:--:|---|
| 1 | **Build an eval set** — 30–50 real cases with known-good outcomes | low | required | **Never skip this** |
| 2 | Context design — domain norms, glossary, constraints, few-shot | low | high | You encoded the norms and it still fails |
| 3 | **Verifiers and tools** — compiler, sim, tests, API, linter | med | **highest** | There is genuinely nothing to check against |
| 4 | Retrieval / RAG — domain corpus | med | high | Facts are right but judgment is poor |
| 5 | Memory — replay failure → cause → fix back in | med | high | It repeats the same mistake |
| 6 | Workflow decomposition — plan → act → adversarial verify | med | high | The task is too big for one pass |
| 7 | Trajectory SFT — distil successful trajectories | high | med | The above works but is **too slow or too costly** |
| 8 | RL / best-of-N — against a verifier | high | high | **Only if a cheap verifier exists** |
| 9 | Continual pretraining | highest | low–med | Effectively never |

### Skip rung 1 and everything above it becomes meaningless

Without an eval set you cannot tell **whether anything got better.** Impressions are not evidence. Tweaking a prompt, deciding "that feels better," and then seeing the same failure a week later is what happens when improvement is never measured.

I reached the same conclusion building [a measurable second brain](/posts/ai-agent/ai-collab-aiq-monitor-measurable-second-brain/) for this blog (Korean). Accumulating knowledge was the easy part; putting a gauge on it — did this knowledge actually make the AI cheaper or better — was the hard and more important one.

### Why rung 3 has the best return

A large part of expertise is not the ability to know but **the ability to find out quickly that you were wrong.** And that lives in the plumbing, not in the weights.

Given a cheap verifier, *a mediocre model plus a verifier plus retries* beats *an excellent model on its own.* A model that gets 60 out of 100 right is fine if you can check each answer cheaply — run it again and take the one that passes. Without a way to check, a model that gets 90 right is still untrustworthy, because **you cannot tell which ten were wrong.**

This is conditional, though. **It does not hold when the verifier is imprecise.** A verifier that waves through wrong answers just adds confidence to bad output as you retry more. The claim is about cheap *and* accurate checks.

### Only rungs 7–9 change weights

The moment you touch weights the cost structure changes. You now collect data, run training, evaluate, and watch for regressions. Worse, **mistakes become hard to undo.** You delete a line from a prompt; you do not delete a learned habit.

The most common mistake is skipping rung 3 and jumping straight to 7–9.

---

## 3. What to feed it — material by value density

"Which material should I train on" has an ordering.

| Tier | Material | Why | Mostly used for |
|:--:|---|---|---|
| **1** | **Decision records** — failure → root cause → fix, post-mortems, code review comments, bug↔fix pairs, work logs | Contains **judgment**. Almost none of it is public | Deficit 3, SFT |
| **2** | **Verifiable artifacts** — code with tests, scenarios, logs and bags, conformance suites | Comes with ground truth, so it becomes eval and reward signal | Rung 1, rung 8 |
| **3** | **Canonical references** — standards, specs, textbooks, API docs | Factually precise, but carries no judgment | RAG only |
| **4** | Papers, articles, talks | Breadth. Goes stale fast | RAG, background |
| **✗** | Generic tutorials, marketing, **unverified secondary reporting** | Noise. Raw material for hallucination | Leave it out |

**Tier 1 is the whole game.** Tiers 3 and 4 are available to everyone, so they differentiate nothing. Expertise is not *"what is Nav2"* — it is *"why `sigma_hit` was the first suspect when AMCL started drifting,"* and the second one is not in anybody else's documentation.

Tier 1 can't be bought. It has to be written down, in something like this shape:

```text
symptom    map looks fine, but pose jumps right after a rotation
hypotheses (a) lidar disturbance  (b) odometry yaw scale  (c) AMCL parameters
refuted    (a) does not reproduce while stationary → rejected
           (b) angular error accumulates over an in-place 360° spin → likely
action     corrected yaw scale, re-measured: 12° error → 1.5°
evidence   table comparing integrated /odom against measured angle, before and after
```

Those five lines are closer to real domain expertise than a hundred pages of specification, **because the refutations are written down.** Knowing what it wasn't is the core of judgment.

---

## 4. What works better than training

The other half of the question — is there something more efficient than learning? Yes.

**1. Build a verifier instead of injecting knowledge.**
If answers can be checked cheaply, the output is accurate even when the model isn't brilliant. The 404 above needed a `curl`, not more facts.

**2. Give it an environment, not a textbook.**
An agent holding a bag replay and a simulator beats an agent that has read every document. If you can run it, you don't have to guess.

**3. Narrow the job.**
Half of "making it an expert" is not raising capability but **shrinking scope.** You cannot build a "robotics expert"; you can build an "AMCL parameter triager." In practice the second one is what the work actually needs.

**4. Compile expertise into determinism.**
Anything that could be a lint rule should be a lint rule, not a model capability. This blog has one: bare code fences get intercepted by Hugo's diagram hook and shred the page, so instead of "remember to be careful" it became a `grep` check after every build. Recurring mistakes get nailed down in code, not trained away.

**5. Retrieve instead of memorise.**
Versions, figures, APIs — anything that changes stays out of the weights. Put it in and it freezes wrong.

**6. Recover failures as assets.**
Write the five lines from section 3 after every failure and they become context for the next run. It is the cheapest form of "learning," and it is exactly what rung 5 does.

**7. Put humans on the 5%.**
Automating 95% and gating only the dangerous decisions is far cheaper than making all 100% excellent. Human experts don't decide everything alone either.

---

## 5. Applying it to this blog

This blog is meant to be a pipeline that gathers knowledge and eventually feeds a personal second brain. KB Radar scrapes external material, posts and work logs record the internal work, and both flow into nextbrain's LLM wiki.

Through the lens of this post, **the structure is already right.** KB Radar covers tiers 3 and 4; the work logs cover tier 1. And there are years of tier 1 already: the error correction behind precision parking, static files 404-ing because of colcon symlinks, multi-robot traffic mediation. All of them in *symptom → hypothesis → refutation → action* form.

What's missing isn't material — it's **the feedback loop.** The order I'm working in:

1. **Thirty eval cases.** Pull *"symptom at the time → the action that actually turned out right"* from the work logs into question/answer pairs. Without this, nothing afterwards can be shown to have helped.
2. **Give it verifiers.** Bag replay, a parameter sanity checker, checking the original endpoint. Close the grounding gap first.
3. **Normalise tier 1.** Restructure the prose work logs into a `symptom / hypothesis / refutation / action / evidence` schema in the wiki, so it is searchable and reusable.
4. **That is where it will most likely end.** If it is still too slow or too expensive after that, then consider rung 7.

The [three-agent harness of orchestrator, reviewer and researcher](/posts/ai-agent/ai-collab-3-agent-harness-orchestrator-reviewer-researcher/) (Korean) is rung 6. At the time I called it role separation; through this lens it was really **making each agent a verifier for the others.**

---

## 6. Limits of this post

Stated plainly.

- **The ladder ordering is judgment, not benchmark.** The relative position of rungs 7 and 8 in particular can flip depending on the domain and on whether verifiers are available. In domains that already have cheap, accurate automatic checks — code, mathematics, simulation — rung 8 moves much higher.
- **"A mediocre model plus a verifier beats an excellent model" is conditional.** It fails when the verifier is imprecise, as noted in section 2.
- **"The fourth deficit is the most common" is my observation, not a statistic.** That said, starting the diagnosis there has never cost me anything, because attaching a way to check is so cheap.

If one sentence survives: **before trying to make the agent smarter, make it able to find out that it was wrong.** That is usually cheaper, and it works faster.
