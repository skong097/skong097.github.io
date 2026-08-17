---
title: "What Data Does Integrated Robot Monitoring Actually Deal With? (2) — OPC UA Gives It Structure, MQTT Carries It"
date: 2026-08-17
tags: ["통합관제", "OPC UA", "MQTT", "Sparkplug B", "제조", "스마트팩토리", "IIoT", "데이터 파이프라인"]
categories: ["robotics"]
summary: "How OPC UA, MQTT, and Sparkplug B fit together — and where people fall over. The OPC UA information model and Client/Server vs PubSub, MQTT's completely unconstrained payload, the birth/death state management Sparkplug B adds to fill that hole, and the price of it: a consumer that connects late runs on an empty screen."
draft: false
ShowToc: true
TocOpen: true
---

[Part 1](../manufacturing-robot-data-01/) laid out the types, rates, retention, and regulation of the
data that integrated monitoring handles. Protocols were compressed into a single table, and that
table **lists the options without saying why you use two of them together.**

This post is that background. It covers how **OPC UA · MQTT · Sparkplug B** mesh, and
**where people fall over.**

The confidence grading (A/B/C) is inherited unchanged from part 1 §0.

| Grade | Meaning |
|:---:|---|
| **A** | Stated in a standards document, statutory text, or regulator publication |
| **B** | A commonly cited figure that multiple vendor/industry sources agree on |
| **C** | Single source, or my own inference. Do not use as a design basis as-is |

---

## 1. Why two of them — the one-page version

The two protocols are **not competitors. They sit at different layers.**

| | **OPC UA** | **MQTT** |
|---|---|---|
| Standard | IEC 62541 (A) | An OASIS standard. 3.1.1 is ISO/IEC 20922:2016 (A) |
| Question it answers | *"**What** is this value?"* | *"How do I get this value **to many places**?"* |
| Good at | Meaning, structure, security | Distribution, scale, low bandwidth |
| Bad at | Heavy with many consumers, awkward through firewalls | **No meaning** — the payload is entirely free-form |
| Where it sits | Equipment ↔ edge | Edge → broker → N consumers |

In one line:

> **OPC UA attaches meaning to a value, MQTT carries it cheaply to many places, and
> Sparkplug B gives the MQTT side a consistent namespace, schema, and state management.** (C)

> ⚠️ **Sparkplug does not restore the OPC UA information model.**
> The reference tree, companion-spec semantics, and browsable address space **do not carry over
> automatically.** Mapping between the two models is **a separate design item**, and skipping it
> means **meaning is lost at the edge.** (C)

---

## 2. OPC UA ① — the point is the information model, not the protocol

### 2-1. It's a tree, not a tag list

A typical industrial protocol gives you **values only**.

OPC UA exposes a tree called the **address space**.
Next to the value sit its **data type, unit, valid range, timestamp, and quality code**, and nodes
are tied together by **references**.

Those references are the decisive part. **Joining on timestamps afterwards to recover the lot almost
always breaks.** OPC UA eliminates that problem by **attaching context to the value at the source.**
(C — this judgment is my own inference)

### 2-2. Companion specs — why different vendors end up with the same names

Information models are **standardized in advance per industry**.
Robotics has the **OPC UA for Robotics** family, a joint effort of VDMA and the OPC Foundation;
machine tools have the **umati** family. (B)

**Practical implication** — choosing equipment that supports a companion spec cuts integration cost
substantially. Without it, **a human has to build a per-vendor tag mapping table, and that table
becomes debt.** (C)

### 2-3. Services and the subscription mechanism

In Client/Server mode the client **doesn't poll — it creates a Subscription.**
The parameters attached to it determine bandwidth and load. (A)

| Parameter | Meaning | Practical feel |
|---|---|---|
| **Sampling interval** | How often the server looks at the value | Equipment capability sets the floor |
| **Publishing interval** | How often it sends the collected batch | Set larger than sampling so messages batch up |
| **Deadband** | Changes below this are not sent | **The main bandwidth-saving knob** |
| **Queue size** | Buffer between publishes | Overflow means loss (or the latest value overwrites) |

**The key** — if the value doesn't change, no data change notification goes out. **This is
fundamentally different from polling.** (A)

> ⚠️ **That does not mean traffic goes to zero.** A subscription sends **KeepAlive** messages even
> with nothing to report, to show the connection is alive. Don't leave that share out of your
> bandwidth budget. (A)

---

## 3. OPC UA ② — Client/Server vs PubSub, and security

### 3-1. Two communication models

**This is the distinction people get confused about most often in practice.**

| | **Client/Server** | **PubSub** (IEC 62541-14) |
|---|---|---|
| Connection | Session-based **1:1**. `opc.tcp://`, default port **4840** | No session. Publisher → many |
| Data | Subscription + MonitoredItem | Publishes a **DataSet** periodically |
| Transport | Direct TCP | A combination of **message mapping** (UADP or JSON) × **transport mapping** (UDP, Ethernet, MQTT, AMQP) |
| Character | Solid but heavy. Server load grows with consumers | Light, favorable with many consumers |
| Watch out | Awkward through NAT and firewalls | Relatively new — **uneven vendor support** (B) |

IEC 62541-14 states explicitly that **PubSub complements Client/Server rather than replacing it** —
it is a model for distributing data not only inside the device network but out to IT and analytics
clouds. (A)

The important structural point is that **you choose message encoding and transport separately.**
**"MQTT means JSON" is false** — carrying UADP over MQTT is a valid configuration. (B)
That is where the combination **"OPC UA PubSub over MQTT"** comes from.

> That said, what it moves is **the DataSet you configured for publication**, not **the server's
> entire address space.** Don't mistake it for transferring the browsable information model intact. (C)

### 3-2. Security is inside the standard

OPC UA has **security at the spec level** — X.509 certificate-based mutual authentication, message
signing and encryption, and user authentication are **part of the protocol**. (A)

**MQTT has none of this.** MQTT security is a **separate layer**: wrap it in TLS and do
authentication and authorization at the broker. (A)

→ **Design implication**: **the security model changes the moment you cross from the edge into
MQTT.** Stitching the authentication schemes together at that boundary is the designer's job. (C)

### 3-3. This protocol can write, too — the most dangerous point in monitoring

OPC UA is **not read-only by nature.** Method calls and writes are in the specification. (A)

So the **account used for monitoring collection must be separated as read-only.**

> The moment the collection path holds write permission on the control path,
> **it is not a monitoring system, it is attack surface.** (B)

Same conversation as IEC 62443 zones & conduits in part 1 §7.

---

## 4. MQTT — the side that carries it cheaply to many places

### 4-1. Get the standards status right first

- **MQTT 5.0 is an OASIS standard.** (A)
- **ISO/IEC 20922:2016 is 3.1.1. Not 5.0.** (A)
  → Writing *"ISO standard MQTT 5.0"* in a specification makes it **a false statement**. This is a
  frequent confusion.
- Default ports: plaintext **1883**, TLS **8883**. (B)

### 4-2. Structure — publishers and subscribers don't know each other

Publishers and subscribers attach to a single broker.
This is the implementation of part 1 §2-3, *"don't create a poll per consumer."*

> **The equipment is read once, and whether there are 4 consumers or 40, the load on the equipment
> is the same.** (B)

### 4-3. The features you actually use

The left column is **what the spec fixes**; the right is **practical judgment**. Grades are attached
per cell.

| Feature | What the spec fixes | Why it matters (practical judgment) |
|---|---|---|
| **QoS 0/1/2** | 0 = at most once (loss possible), 1 = at least once (duplicates possible), 2 = exactly once (A) | Floor telemetry is usually **1**. 2 adds round trips and is slow (B) |
| **Retained message** | The broker keeps a topic's last value and delivers it to new subscribers (A) | The reason a dashboard isn't blank the moment it opens (C) |
| **LWT (Last Will)** | If a client terminates abnormally, **the broker publishes** the designated message on its behalf (A) | **The foundation of Sparkplug's death notification** (B) |
| **Persistent session** | Subscriptions and undelivered QoS messages survive a reconnect (A) | Worth more the flakier the site (C) |
| **Wildcards** | `+` one level, `#` everything below (A) | Used for consumer separation like `factory/+/robot/#` (C) |
| **MQTT 5.0 additions** | Shared subscriptions, message expiry, user properties, topic alias, reason codes (A) | **Consumer scale-out is far easier on 5.0** (B) |

### 4-4. And the decisive weakness

**MQTT puts no rules on the payload at all.** Topic names are free, content is free. (A)

> Put three teams on it and **you get three topic schemes.**
> The meaning OPC UA worked to attach **evaporates** the moment it crosses into MQTT. (C)

---

## 5. Sparkplug B — bringing back the evaporated meaning

**Eclipse Sparkplug** is what fills the hole in §4-4. It is a specification layered on MQTT, and
**from 3.0.0 it is managed under the Eclipse Foundation's formal specification process**. (A)

### 5-1. What it specifies

- **Topic namespace** — the first token is fixed to `spBv1.0` (or `spAv1.0`), and
  **that token denotes the payload encoding.** (A)

  ```text
  spBv1.0/{Group ID}/{message_type}/{Edge Node ID}/[{Device ID}]
  ```

- **Payload** — not free-form JSON; **specified in protobuf**. (B)
- **State management** — this is the core, below.

### 5-2. Birth / Death — separating "no new value" from "the equipment died"

| Message | Meaning |
|---|---|
| `NBIRTH` / `DBIRTH` | **Birth certificate.** Declares the full tag list and current values at once |
| `NDATA` / `DDATA` | From then on, **changes only** |
| `NDEATH` / `DDEATH` | **Death certificate** |
| `NCMD` / `DCMD` | Downward commands |
| `STATE` | The state of the Primary Host application |

The specification requires an edge node to **publish `NBIRTH` before any other message after
connecting**, and to register `{namespace}/{Group ID}/NDEATH/{Edge Node ID}` as its **MQTT Will
topic**. (A)

**Why this is decisive**

- A consumer that received `NBIRTH` can **reconstruct the full state from the changes (`NDATA`)
  alone.** No separate tag-list document has to be exchanged.
- Thanks to `NDEATH`, ***"no value is arriving"*** and ***"the equipment is dead"*** **can be told
  apart.** Without that distinction, **the monitoring screen quietly lies** — the last value is still
  sitting there and you can't tell whether it's current or a relic. (C)

> ⚠️ **A consumer that connects late does not just work.**
>
> `NBIRTH` is **published once and gone**. A consumer that connects afterwards does not
> automatically receive the past `NBIRTH`. **Do not mistake it for having the same effect as an MQTT
> retained message.**
>
> To get state aligned you have to design a synchronization procedure alongside it, such as a
> **rebirth request (`NCMD`)**, and you have to watch the Primary Host's `STATE` flow as well. (B)
>
> **This is the common cause of failed Sparkplug deployments** — a consumer that didn't account for
> connection order **starts running with empty state.** (C)

### 5-3. Supporting machinery

- **Sequence number (`seq`)** — lets the consumer detect lost or out-of-order messages (B)
- **alias** — replaces long tag names with numbers to save bandwidth (B)

---

## 6. The combined architecture and its design principles

### 6-1. The edge gateway is both translator and boundary

On a floor mixing legacy equipment (Modbus and friends) with modern robots (OPC UA), the edge
gateway **translates several industrial protocols into Sparkplug-conformant MQTT**, bringing them in
without a hardware swap. (B)

The edge is not just a translator; it is **a boundary where three things happen at once** (C):

1. **Protocol translation** (OPC UA / Modbus → MQTT)
2. **Security model transition** (OPC UA built-in security → TLS + broker authorization)
3. **Reduction** (deadband and aggregation to cut upstream bandwidth)

### 6-2. Mines people step on

| Mine | Symptom | Response |
|---|---|---|
| **Broker SPOF** | One broker dies and **visibility of the whole plant disappears** | Cluster and redundancy (B) |
| **Reconnection storm** | The instant the network recovers, **every node reconnects and republishes at once** | Distributed backoff if Sparkplug birth is heavy (C) |
| **A poll per consumer** | The equipment dies | Equipment→edge once, publish/subscribe after (B) |
| **Write permission on the collection account** | Monitoring becomes attack surface | Separate read-only (§3-3) (B) |
| **Clock mismatch** | Event order inverts and **cause analysis becomes impossible** | Unify NTP and timestamp policy at the edge (C) |
| **Topic scheme sprawl** | Different names per team. **Unfixable later** | Fix Sparkplug or an in-house UNS convention **first** (C) |

### 6-3. Order of decisions

1. **Fix the information model first** — tag names, units, context. **This comes before protocol
   choice**
2. **Fix the topic namespace** — Sparkplug, or an in-house UNS convention
3. **Derive QoS, deadband, and publishing rate backwards from the bandwidth budget** (part 1 §3)
4. **Only then** pick broker and gateway products

> Do it in reverse and **the product decides your data model. That is the most expensive mistake.** (C)

---

## 7. Putting wearable / behavioral data on top of this — where it doesn't fit

Worker behavioral data (smart gloves, HMDs, IMU bands) **does not enter this pipeline as-is.**

- **Wearables don't speak OPC UA.** They typically go out over **BLE → vendor gateway → vendor cloud
  (REST)**. → You need **one more adapter segment** to pull it out of the vendor cloud and republish
  over MQTT. That segment doesn't exist for machine data, and **this is where the real cost of the
  integration sits.** (C)
- **Work-unit labels are events.** They fit poorly with OPC UA's periodic sampling model.
  The MQTT side is more natural, but Sparkplug's birth/death **means something different for a
  person** — a worker taking off a glove is not "equipment failure." **Wire the death notification
  straight into alarms and you get false alerts.** (C)
- ⛔ **Do not embed personal identifiers in the topic path.**
  Put an employee number into the `spBv1.0/{Group ID}/.../{Edge Node ID}/{Device ID}` structure and
  **it spreads across the broker, the historian, and every backup, irreversibly.** Break the mapping
  to an anonymous ID **at the edge boundary.** (C)
- **The retention ceiling is different.** For machine data the criterion is **storage cost**; for
  human data **the law** sets the ceiling. Put them in the same topic tree and you cannot separate
  the retention policies. (C)

> **Conclusion** — putting behavioral data on this pipeline is **possible**, but you have to design
> three additional things: **the adapter, the anonymization boundary, and a separate retention
> policy.** *"It's MQTT, just put it on there"* does not hold. (C)

---

## Sources

**Standards texts** — OPC Foundation (IEC 62541 update announcements) · IEC 62541-14 PubSub
overview · OPC Foundation Robotics (VDMA collaboration) · MQTT Version 5.0 (OASIS Standard) ·
MQTT Specification (mqtt.org) · OASIS (announcement of ISO/IEC 20922 approval for MQTT 3.1.1) ·
Eclipse Sparkplug 3.0 specification · Sparkplug normative statements

**Implementation and commentary** — open62541 (Core Concepts: address space, services,
subscriptions) · HiveMQ (OPC UA ↔ MQTT bridge) · HiveMQ (what changed in Sparkplug 3.0) ·
EMQ (Sparkplug B, the formalization of Sparkplug 3.0)

## What this survey could not confirm

- **The clause-level text of the IEC 62541 parts** — a paid standard, not read.
  The basis here is OPC Foundation announcements and summary documents
- **The exact document number of the OPC UA for Robotics companion spec** — I couldn't confirm it,
  so I didn't write a number
- **Per-vendor actual support for PubSub and Sparkplug** — needs measurement at product selection
  time

---

**Previous** → [Types, Rates, Retention, Regulation (1)](../manufacturing-robot-data-01/)
