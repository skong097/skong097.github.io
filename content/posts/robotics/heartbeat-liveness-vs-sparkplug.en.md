---
title: "I Misremembered How Many Seconds It Takes My Own Dashboard to Grey Out a Robot"
date: 2026-08-17
tags: ["heartbeat", "liveness", "ros2", "dds", "qos", "mqtt", "Sparkplug B", "관제", "fleet"]
categories: ["robotics"]
summary: "A multi-robot dashboard paints dead robots grey. Asked how many seconds of silence it takes, I said \"two?\" — the code says 3.0. What those 40 minutes exposed wasn't a wrong number but a reversed causality: the packet loss wasn't an accident, it was the BEST_EFFORT QoS I chose. Here is how the industrial standard, Sparkplug B, solves the same problem — and what its solution costs."
draft: false
ShowToc: true
TocOpen: true
---

I built a multi-robot monitoring system. It shows the state of several robots on one screen,
and paints the dead ones as grey dots. Nothing exotic.

A few days ago I spent 40 minutes being interrogated over one of those grey dots. The question
was a single sentence.

> **"How many seconds of silence before you paint it grey?"**

I said **"two?"**

I opened the code. It was **3.0 seconds**.

---

## 1. What I built

An agent runs on each robot and fires a heartbeat at the console.

```python
# wasab_robot_agent/agent_node.py
HEARTBEAT_HZ = 2.0                       # twice per second

def _hb_qos():
    q = QoSProfile(depth=10)
    q.reliability = QoSReliabilityPolicy.BEST_EFFORT   # ← this one line becomes the problem
    return q
```

The console decides the state from two signals: heartbeat and ping.

```python
# wasab_gui/fleet.py
ROBOT_STALE_S = 3.0

def liveness_state(ping_ok, hb_fresh):
    if hb_fresh:
        return "online"     # ●  healthy
    if ping_ok:
        return "powered"    # ◐  box is up, agent is dead
    return "offline"        # ○  the grey dot
```

Two signals give four combinations, but there are only three states. One of them got absorbed
somewhere.

That was the design. I thought it was fine.

---

## 2. Where it fell apart

The questions came in a pressure-interview format. The scoreboard:

| Asked | My answer | Reality |
|---|---|---|
| After how many seconds does it go offline | **"two?"** | **3.0 s** (`ROBOT_STALE_S`) |
| Why that value | — | **No answer. No rationale exists** |
| Why wait for several beats | "Wireless drops packets. Judging on one gives false positives" | ✅ |
| **Is that loss an accident, or something you built** | **"I set the threshold that way"** | ❌ |
| Four combinations, three states — which one is missing | "The one with ping but no heartbeat" | ❌ **backwards** |

The first three rows were fine. The trouble starts at the fourth.

### 2-1. "I set the threshold" is the wrong answer

The question was *"is a missing heartbeat a network accident, or did you design it that way?"*
I answered that I picked the threshold.

**A threshold is a *response* to loss, not the *cause* of it.**

The cause is up above. `BEST_EFFORT`.

```python
q.reliability = QoSReliabilityPolicy.BEST_EFFORT
```

With `RELIABLE`, DDS retransmits. With `BEST_EFFORT` it does not. A dropped beat is simply gone.
**The loss isn't an accident — I chose it.** And it is precisely that choice that made a threshold
necessary in the first place.

The direction of causality was inverted. I named the consequence as the cause.

### 2-2. The right answer was in my own comment

Asked which of the four combinations disappeared, I said `ping O + heartbeat X`. Wrong.
That one is `powered` — far from vanishing, it is **the most valuable state on the board**, because
it separates "SSH in and restart the agent" from "someone has to drive out to the floor."

The one that disappears is `ping X + heartbeat O`. It gets absorbed into `online`.

The reason: **the arrival of a heartbeat is itself the stronger evidence** — it proves both that the
network is alive and that the agent is alive. You don't overturn strong evidence with weak evidence
(a failed ping).

And I had already written that sentence down.

```python
def liveness_state(ping_ok, hb_fresh):
    """heartbeat present → online regardless of ping (the stronger signal). Then ping only →
    powered (box up, agent waiting); neither → offline."""
```

**"The stronger signal"** — my own words, in my own file, and in the interview I said the opposite.

---

## 3. Why this is the frightening kind of mistake

This isn't something I failed to learn. **It's something I built and then failed to hold on to.**

An interviewer doesn't quiz you on other people's knowledge. **They hold up the code and the
documents you submitted and ask about those.** The moment "did I write it that way?" comes out of
your mouth, trust in the whole project collapses. **Misremembering what you know is far more
dangerous than admitting what you don't.**

And that `3.0` still has no rationale. It exists in the code and nowhere in the docs.
Nobody knows who chose 3.0 or why. I don't either. And I chose it.

---

## 4. The industry already solved this

My three-state judgment boils down to one question.

> **How do you distinguish "no new value" from "dead"?**

**Sparkplug B** — the industrial standard layered on top of MQTT — attacks that question head-on,
and does it in a way that has nothing to do with my heartbeat polling.

| Message | Meaning |
|---|---|
| `NBIRTH` / `DBIRTH` | **Birth certificate.** On connect, declares the full tag list and current values at once |
| `NDATA` / `DDATA` | From then on, **changes only** |
| `NDEATH` / `DDEATH` | **Death certificate** |
| `NCMD` / `DCMD` | Downward commands |

The key is `NDEATH`. On connect, the node registers a will with the broker — **"if I vanish
suddenly, publish this on my behalf"** (MQTT's Last Will). So when it dies, **the broker announces
the obituary for it.**

Side by side with mine:

| | My heartbeat approach | Sparkplug B |
|---|---|---|
| Declaring death | The console **counts time and guesses** | The broker **notifies explicitly** |
| Threshold | **Required** (which is where `3.0` came from) | Unnecessary in principle |
| No-change vs death | **Cannot tell them apart** | Distinguished |

The question I couldn't answer for 40 minutes was already nailed down as an answer in a spec.
(There's a fuller treatment of the spec side in
[OPC UA gives it structure, MQTT carries it](../manufacturing-robot-data-02/) §5.)

---

## 5. But it isn't free

Here I got one more thing wrong on the same day.

The scenario handed to me:

```text
3 of 12 robots don't appear on the dashboard at all.
The broker is healthy. Those 3 are running fine on the floor.
Subscribe to the broker directly and their DDATA is flowing, several per second.
Restarting the dashboard changes nothing.
```

I said I'd check whether the agent was alive and whether the heartbeat looked healthy.
**I reached straight for what I do in my own system.** Every one of those checks passes. The
problem stays exactly where it was.

The answer was this.

> **`NBIRTH` is not a retained message.**

`NBIRTH` is **published once and gone**. The broker does not hold it and hand it to a subscriber
that shows up later. And the `NDATA` that follows **carries no tag names** — to save bandwidth it
carries only numeric aliases.

```text
NBIRTH  { "metrics": [ {"name": "Axis1/Torque", "alias": 7, ...}, ... ] }
NDATA   { "metrics": [ {"alias": 7, "value": 23.4} ] }     ← no idea what alias 7 is
```

Those three robots had been connected **since before the dashboard started subscribing**. They never
dropped, so they had no reason to publish `NBIRTH` again. The dashboard receives their data and
**cannot interpret it.** Restarting the dashboard doesn't help — what restarts is the dashboard,
not the edge node.

The fix is to request a **rebirth** via `NCMD`, so the node emits `NBIRTH` again.

Which comes to this.

> **The price of learning about death explicitly is a dependence on birth.**
> You get the obituary, but miss the birth certificate and you don't know the thing exists at all.

My heartbeat approach has exactly the opposite character. Death has to be guessed at, but
**whenever you connect, a single next heartbeat restores everything.** The late-subscriber problem
cannot occur by construction.

This isn't an argument that one is better. **They gave up different things.**

---

## 6. What's left

- Document the rationale for `ROBOT_STALE_S = 3.0`. Right now it lives only in the code, without a
  reason. At `BEST_EFFORT` + 2 Hz, 3.0 s means **six consecutive drops**. Whether 6 is the right
  number I still haven't decided.
- If I switch QoS to `RELIABLE`, does this value go up or down? I can't answer that with confidence
  yet.
- If it happens once more that I can't hold to a comment I wrote myself, that isn't coincidence.

---

## Three lines I take away

1. **Packet loss isn't an accident; it's the consequence of a QoS choice.** The threshold is the
   response, not the cause.
2. **Strong evidence isn't overturned by weak evidence.** If a heartbeat arrived, ignore the failed
   ping.
3. **If I don't know what's written in my own code, it's the same as not having built it.**

---

> This post is a record of defending my own project in a pressure-interview format inside a learning
> tutor system (`dr.dom`), and losing. The verdicts in the tables above are in the actual session log.

**Continues in** → [What Data Does Integrated Robot Monitoring Actually Deal With? (1) — Types, Rates, Retention, Regulation](../manufacturing-robot-data-01/)
