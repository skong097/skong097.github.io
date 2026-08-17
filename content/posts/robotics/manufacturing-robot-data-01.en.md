---
title: "What Data Does Integrated Robot Monitoring Actually Deal With? (1) — Types, Rates, Retention, Regulation"
date: 2026-08-17
tags: ["통합관제", "OPC UA", "MQTT", "Sparkplug B", "제조", "스마트팩토리", "IIoT", "데이터 파이프라인"]
categories: ["robotics"]
summary: "Before choosing a product for integrated monitoring on a robot-equipped factory floor, you have to answer what data you will actually be handling. This is a research note on the types, collection methods, rates, retention, and pipelines — plus the standards and laws that force your hand. Rates span six orders of magnitude, from 1 kHz to 15 minutes; retention is decided by regulators, not engineers. Every figure carries a confidence grade (A/B/C)."
draft: false
ShowToc: true
TocOpen: true
---

When you set out to build integrated monitoring and control for a factory floor that runs robots,
the first question you hit is not "which tool should we use."

> **"What data are we going to be handling in the first place?"**

Decide that after picking a product and the product decides your data model for you. That is the
most expensive mistake available.

This is the research note I wrote trying to answer that question. It covers the **types, collection
methods, rates, retention, and pipelines** of the data, plus the **standards and laws** that force
your hand.

Protocol detail (OPC UA · MQTT · Sparkplug B) grew too large and moved to
[part 2](../manufacturing-robot-data-02/).

---

## 0. First, how to read this — everything gets a confidence grade

Every figure and claim in this post carries a grade.

| Grade | Meaning |
|:---:|---|
| **A** | Stated in a standards document, statutory text, or regulator publication |
| **B** | A commonly cited figure that multiple vendor/industry sources agree on |
| **C** | Single source, or my own inference. **Do not use as a design basis as-is** |

Why bother: **if you don't separate the strength of the evidence inside the sentence, the reader
takes it all at the same weight.** "Vibration is sampled at 25 kHz" and "SCADA polling is usually
1 second" are on completely different evidentiary tiers, but listed side by side they both look
like facts.

And one thing to nail down up front.

> ⚠️ **This is a literature survey, not measurements from a specific plant.**
> The figures below are *a starting range at the beginning of design*, not *the values at our site*.
> On an actual deployment, task number one is **measuring the tags on the floor** (tag count, real
> update rate, daily growth). (C)

---

## 1. Types of data — it splits into five layers

The data handled by integrated monitoring splits into **five layers** with distinct characteristics.
This split matters because **rate, retention, and pipeline differ by an order of magnitude or more
between layers.** Bundle them under one policy and something is guaranteed to be over-engineered or
lost.

### 1-1. Robot and equipment control data (Level 1–2)

| Data | Content | Primary use |
|---|---|---|
| Per-axis joint values | Position, velocity, acceleration per axis | Trajectory verification, collision analysis |
| Per-axis torque / motor current | Servo load | **The core predictive-maintenance signal** — deciding gearbox grease changes and mastering (B) |
| Temperature | Motor, controller, gearbox | Degradation, overload |
| I/O state | Digital/analog in and out | Interlocks, handshakes |
| Program context | Running program, line number, job ID | **The key to attributing an error to a process step** |
| Operating state | run / idle / estop / fault + stop reason | The availability term of OEE |
| Alarms and events | Code, timestamp, severity | Fault analysis |
| Cycle count and time | Units, duration | Productivity, drift detection |

Robot maintenance tooling attaches to the controller over OPC UA to track uptime and stop reasons,
and **reads motor torque to decide when grease changes and mastering are due**. (B)

### 1-2. Process and equipment data (Level 2)

PLC tags (pressure, flow, temperature, position), CNC machine tool data, conveyors, jig and fixture
state, barcode/RFID readers, torque-gun fastening values.

**Why looking at the robot alone fails** — a large share of robot stoppages are not robot faults but
**the consequence of surrounding equipment and material supply**. Collect only robot data and you
never reach the cause. (C)

### 1-3. High-frequency condition monitoring data (handled separately)

Vibration, acoustic emission (AE), motor current signature (MCSA).

Physically the same objects as 1-1, but **as data they are a completely different animal.**
Sampling is in the kHz band, so putting it straight onto the SCADA pipeline **collapses your
bandwidth.** (see §3)

### 1-4. Quality and traceability data (Level 3, MES)

Per-unit genealogy (lot, batch, serial), inspection results, **vision verdicts and the source
images**, process parameter snapshots, operator/shift/equipment assignment, rework and scrap
history.

For automotive, **IATF 16949 8.5.2** requires lot-, batch-, and part-level genealogy to be collected
and retained automatically. (A)

> **Vision images are a capacity bomb.** Put the verdict (a few bytes) and the source image (a few
> MB) under the same retention policy and storage cost goes out of control. In practice, **keeping
> the source only for NG and borderline verdicts** is the norm. (C)

### 1-5. Business and aggregate data (Level 3–4)

OEE (availability × performance × quality), actual vs. planned output, energy consumption (power per
machine), inventory and material requirements, maintenance work orders (CMMS integration).

### 1-6. Safety and security data (cross-cutting)

Safety PLC events (light curtain break, emergency stop, safety zone intrusion), speed-and-separation
monitoring events on collaborative robots, access control, **OT network audit logs**.

That last item is required by **IEC 62443 / NIST SP 800-82**, and it is **the axis most easily left
out of "monitoring data."** (A · see §7)

---

## 2. Collection methods — "OPC UA gives it structure, MQTT carries it"

As of 2026 the industry consensus is clear. **OPC UA structures the data; MQTT transports it.**
Layer **Sparkplug B** on top and MQTT messages gain structure and consistency, so data travels from
the plant floor to the cloud with its security and data model intact. (B)

| Protocol | Position | Characteristics | Watch out for |
|---|---|---|---|
| **OPC UA** | Equipment ↔ edge | Information model (carries context: lot code, process parameters, equipment ID), security built in | If polling-based, load grows with each consumer |
| **OPC UA PubSub over MQTT** | Edge → upstream | OPC UA model + MQTT transport | Relatively new, uneven vendor support |
| **MQTT + Sparkplug B** | Edge → broker → N consumers | **State management (birth/death)**, defined topic namespace and payload schema | **The broker is a SPOF — redundancy is mandatory** |
| **MTConnect** | Machine-tool centric | Vendor-neutral semantic vocabulary. ANSI/MTC1.4-2018 | **Read-only. No control** |
| **Fieldbus** (PROFINET / EtherNet/IP / Modbus TCP) | Control layer | Deterministic real time | Collecting from it directly **disturbs the control loop** |
| **Vendor-specific APIs** | Direct to equipment | FANUC FOCAS, ABB Robot Web Services, KUKA RSI, etc. | Lock-in. Not reusable across vendors |
| **ROS 2 / DDS** | AMRs and research lines | Topic-based, high frequency | Exposing it raw on the plant monitoring network creates traffic and security problems |

### 2-1. MTConnect structure (mandatory if machine tools are in the mix)

An **Adapter** attaches to the equipment controller, reads signals, converts them to **SHDR** (a
plain-text stream, pipe-delimited, each line starting with a UTC timestamp), and feeds an **Agent**.
The Agent organizes this into an internal buffer and exposes it over an HTTP API. Typically the
Adapter sits on the equipment and the Agent on a separate server. (A/B)

### 2-2. Integrating legacy equipment

The reality on the floor is **"a 20-year-old machine next to a robot bought last year."**
An edge gateway translates **100+ industrial protocols**, Modbus and OPC UA among them, into
Sparkplug-B-conformant MQTT, bringing them in **without replacing hardware**. (B)

### 2-3. Three design principles

1. **Don't create a poll per consumer.** Equipment → edge happens once; everything after that is
   publish/subscribe. If MES, ERP, analytics, and the dashboard each poll, **the equipment dies.** (B)
2. **Separate collection onto a read-only path.** The moment monitoring collection holds write
   permission on the control path, it is not a monitoring system — it is **attack surface**.
   (§7, IEC 62443 zones & conduits)
3. **Attach context at the source.** Joining on time afterwards to recover the lot almost always
   fails. OPC UA carrying the lot code and equipment ID alongside the value is what solves this. (C)

---

## 3. Collection rates — four to five orders of magnitude between layers

**This table is the most practically useful part of the survey.** Get the rate wrong and either your
bandwidth blows up or you miss the events you were supposed to catch.

| Layer | Target | Rate / frequency | Grade |
|---|---|---|:---:|
| Robot internal control loop | Servo control | **1 kHz (1 ms)** — KUKA FRI supports up to the same 1 kHz as the internal control layer | B |
| Real-time external control IF | KUKA RSI | Two cycles: 4 ms / 12 ms | B |
| 〃 | ABB EGM, FANUC DPM | For real-time path correction. Same band as RSI | B |
| Bulk process data collection | CNC, robots | At least **100 Hz** (sampling period ≤ 10 ms) | B |
| Vibration — early bearing/gear defects | Condition monitoring | **25–50 kHz** sampling, flat response up to 10–20 kHz recommended | B |
| Vibration/current (research cases) | Induction motor PdM | 10 kHz, split into 1.0-second windows / another case at 50 kHz | B |
| SCADA tag polling | Pressure, temperature, state | **100 ms – 1 s** (the general monitoring default) | C |
| Robot run/alarm state | Integrated monitoring dashboard | **1 s, or on-change events** | C |
| MES events | Lot start/end, inspection | **Event-driven** (not periodic) | B |
| OEE / aggregates | Dashboard | 1-minute to 15-minute aggregation | C |
| Energy | Power per machine | 1 minute | C |

**From 1 kHz to 15 minutes.** Six orders of magnitude inside one system.

### 3-1. Three practical conclusions

**① Never send raw high-frequency (kHz) data to the center.**

The edge gateway takes high-speed sensor data and low-speed controller data and sends **not the raw
stream but an actionable insight** upstream. (B)
In practice this looks like: extract FFT/features (RMS, crest factor, band energy) at the edge, send
**a handful of values per second**, and **upload a raw waveform burst only when an anomaly appears**. (C)

**② Change-driven (on-change / deadband) beats fixed polling almost every time.**

Most tags don't change most of the time.
Sparkplug B's state management is what makes this **safe** — it tells you whether the absence of a
value means *"normal, unchanged"* or *"dead."* (C)

**③ The rate is set by the use case, not by the fastest thing you can do.**

Being able to pull at 1 ms and needing to store at 1 ms are different questions.

> **5,000 measurement points** at a **1-second rate** alone is **432 million records per day**. (B)

---

## 4. Retention — this is a regulatory decision, not a technical one

What the engineer decides is **"when do we move a tier."**
**"When may we delete"** is decided by law and by customer-specific requirements (CSR).

### 4-1. Technical tiers — common practice

| Tier | Medium | What it holds | Typical period | Grade |
|---|---|---|---|:---:|
| **Hot** | Memory, NVMe SSD | Recent sensor values, active alarms, current process control data | Sensors 24 h / quality 7 days | B |
| **Warm** | Ordinary disk | Trend summaries — training data for AI prediction models | 1–5 years (cases move raw sensor data after 30 days) | B |
| **Cold** | Archive, object storage | Regulatory compliance | 5–10 years | B |

An example policy for quality data — **hot 7 days / warm 90 days / cold 7 years.** (B)

### 4-2. Regulatory floors

| Domain | Basis | Required retention | Grade |
|---|---|---|:---:|
| **Automotive** | IATF 16949 7.5.3.2.1 · 8.5.2 | Typically **10–15 years**. PPAP, tooling, design, and contracts for **N+1 calendar years** (N = production/service life). OEM CSRs demand longer for safety-critical characteristics | A |
| **Pharma / bio (GxP)** | FDA 21 CFR Part 11 · EU GMP Annex 11 · PIC/S PI 041 | Electronic records and audit trails must stay **reproducible for the entire retention period**. Audit trails need **who/what/when/why**, all four | A |
| **Food** | FDA FSMA 204 | Key data elements (KDE) for **at least 2 years**. **Produce within 24 hours** on FDA request | A |
| **Oil and gas** | FERC · PHMSA | Process data **at least 7 years**. Many operators keep 20–30 years in practice | B |
| **Occupational safety (US)** | OSHA | Hazardous exposure records for **30 years after separation**. Training and maintenance defect logs 3 years or more | A |
| **Semiconductor** | Fab customer requirements · SEMI | The standards themselves fix no term. **The customer contract decides** | C |

### 4-3. Easy mistakes at design time

- **Lumping it all into "about 7 years" guarantees a cost blowup.**
  Keeping 1 kHz raw data for 7 years and keeping 1-minute aggregates for 7 years differ by
  **thousands of times**. You need **a different period per resolution**. (C)
- **Audit trails outlive the data.**
  In GxP domains, retaining *"who changed what, when, and why"* is stricter than retaining the value
  itself. (A)
- **Deletion is also a policy.** Operator-identifying data caught by EU GDPR (worker ID, biometrics,
  location) has an **upper bound** on retention. **"Keep everything" is not compliance.** (C)

---

## 5. Data pipeline

### 5-1. Unified Namespace (UNS)

Put the broker at the center as **"the single source of truth for the current state of the plant"**
and have every system face the broker instead of connecting point to point.

The effect is **polling load removed and per-consumer integrations eliminated.** Telemetry from CNCs,
robot arms, and conveyors reaches MES/ERP in real time with neither polling overhead nor a
point-to-point integration per consumer. (B)

Open-source stacks like United Manufacturing Hub have productized the combination of
**TimescaleDB + UNS (MQTT/Kafka)**. (B)

### 5-2. Broker vs. stream — do you need both?

| | MQTT broker | Kafka |
|---|---|---|
| Role | Propagates current state, lightweight, OT-friendly | **Replayable log**, large buffer, backpressure |
| When you need it | **From day one** | When consumers multiply and you need **reprocessing and replay** |

Introducing Kafka from the start at a small site is **very likely over-engineering.** (C)
The recommended order is **start with MQTT + a TSDB**, and add Kafka when the requirement *"we have
to replay historical data to retrain the model"* **actually shows up**. (C)

### 5-3. Historian / TSDB options

| | Character |
|---|---|
| **AVEVA PI System** | The traditional historian. OT integration and a long operational track record. Heavy license cost |
| **InfluxDB** | Time-series specialist. Compression around **10:1**. Windowed aggregation, downsampling, derivatives, and trends built in. 2.x has limits on high-cardinality tags (relaxed by the 3.0 columnar engine) |
| **TimescaleDB** | A PostgreSQL extension. Lossless compression of **94–97%**. Continuous aggregates = materialized views that incrementally refresh only the changed chunks |

**If the team already runs PostgreSQL, TimescaleDB has the lowest learning cost.** (C)

---

## 6. Storage and processing

### 6-1. A sense of scale first

> **5,000 measurement points** × **1-second sampling** = **432 million records per day**. (B)

That number is the reason every technique below exists.
Without time-series-optimized storage, columnar compression, and time-partitioned query execution,
none of it holds up.

### 6-2. Techniques in use

| Technique | What it does | Effect |
|---|---|---|
| **Edge filtering** | Don't ship raw high-frequency data; send features, with a raw burst only on anomaly | Bandwidth and storage cut by **tens to hundreds of times** (C) |
| **Deadband / on-change** | Don't record if the change is below threshold | Removes the cost of unchanging tags (C) |
| **Columnar compression** | TimescaleDB 94–97% lossless / InfluxDB ~10:1 | Storage cost (B) |
| **Continuous aggregates and downsampling** | Maintain 1-minute/1-hour/1-day rollups from 1-second raw, incrementally | Dashboard query speed (B) |
| **Retention differentiated by resolution** | Raw 30 days · 1-minute aggregates 2 years · 1-hour aggregates 10 years | Compliance and cost at the same time (C) |
| **Time partitioning** | Split into chunks | Archive or drop old partitions wholesale (B) |
| **Automatic tiering** | Age-threshold-driven hot→warm→cold | Removes operational burden (B) |

### 6-3. Four things you must decide

1. **Where the timestamp comes from.** The equipment clock or the gateway clock?
   Without NTP/PTP synchronization, the moment you join data from multiple machines
   **causality inverts.** **This is the most common accident.** (C)
2. **Distinguishing a missing value from "no value arrived."** Sparkplug B's birth/death addresses
   this. (B)
3. **Immutability of the raw record.** In GxP domains, **downsampling that overwrites the original is
   itself a violation.** Aggregates go in **derived tables** and the original is left alone.
   (A — the *Original* of ALCOA+)
4. **Schema evolution.** Equipment replacement and new tags will happen, guaranteed.
   Fail to fix the Sparkplug B topic namespace and ISA-95 hierarchy in advance and
   **your tag names are chaos in three years**. (C)

---

## 7. Standards, security regulation, and law

Three distinct kinds — ① **structural standards** (how to build it), ② **security regulation** (how to
protect it), ③ **law** (violate it and you face penalties or market exclusion).

### 7-1. Structural standards

| Standard | Content | Why it matters |
|---|---|---|
| **ISA-95 / IEC 62264** | Manufacturing operations levels (0–4) and standard terminology | The layer split of integrated monitoring comes from here. IEC 62443's zones & conduits were built on this model (A) |
| **Purdue model** | ICS layer reference model | Aligned with IEC 62443 and NIST SP 800-82. Accepted as a compliance basis in regulated industries (A/B) |
| **ISA-88 / IEC 61512** | Batch process control model | Chemical and pharmaceutical batch sites |
| **MTConnect** (ANSI/MTC1.4-2018) | Semantic vocabulary for manufacturing equipment | Vendor-independent tag naming (A) |
| **OPC UA** (IEC 62541) | Information model + secure communication | **The de facto base standard for integrated monitoring** (A) |
| **Sparkplug B** | MQTT topic namespace, payload schema, state management | **What makes MQTT usable in OT** (B) |
| **SEMI standards** (semiconductor) | E30 GEM = equipment behavior standard. Interface A = E120+E125+E132, purely for data collection. E134 = data collection management, E147 = EDA guide | **A fab won't let equipment in the door without these** (A) |

### 7-2. Security regulation

| Regulation | Requirement | Constraint it puts on monitoring design |
|---|---|---|
| **IEC 62443** | **Zones & conduits** — group assets with similar security requirements into zones, and control data movement between zones through conduits | **Your data collection path *is* a conduit.** Put the collector anywhere you like and that alone is a violation (A) |
| **NIST SP 800-82** | Build the OT network on a layered reference model derived from Purdue + 62443 zones/conduits | The practical standard in US and global manufacturing (A) |
| **Common — logging and audit trail** | Both frameworks require logging, audit trails, and security event detection | In OT this has to be done with **passive network monitoring** — **no active traffic injection** that would disturb deterministic control loops (A) |
| **EU NIS2** | Cybersecurity management and incident reporting for essential and important entities | Much of manufacturing is in scope. Requires log retention and a reporting process (B) |

> **The one line to bake into the design** — monitoring data collection is designed as
> **passive, read-only, and unidirectional (aiming at a data diode)**.
> The moment you open a write path from the upper network into the control network for the
> convenience of monitoring, the 62443 structure collapses. (C)

### 7-3. Law — by region

#### EU

| Law | In force | Obligation regarding manufacturing data |
|---|---|---|
| **EU Data Act** (Reg. (EU) 2023/2854) | Entered into force 2024-01-11, **applicable 2025-09-12** | Guarantees **user access to data generated by the use of connected products** — including the telemetry, logs, performance metrics, and error events an industrial robot produces in a customer's plant. It must be **readily available, free of charge, and in a machine-readable format**. Cloud switching (portability) interfaces and procedures are also required. Small-enterprise exemptions exist (A) |
| **NIS2** | In force | Cybersecurity risk management and incident reporting (B) |
| **GDPR** | In force | Applies to worker-identifiable data. Purpose limitation and retention caps (A) |
| **Machinery Regulation** (EU) 2023/1230 | Fully applicable 2027 | Safety requirements for machinery with digital functions and AI. Includes logging and traceability requirements (C — text not verified) |
| **EU AI Act** | Phased application | Using AI for inspection or verdicts triggers data governance and logging requirements (C) |

> **The EU Data Act is the most important new item in this survey.**
> If you build and sell robots or machines, *"can we hand the customer, in a machine-readable format,
> the data our equipment produced in their plant?"* has been a **legal obligation since 2025-09-12**.
> A **data extraction/export API has to be in the integrated monitoring architecture from day one.** (A)

#### Korea

| Law / scheme | Content |
|---|---|
| **Industrial Digital Transformation Promotion Act** (Act No. 18692, promulgated 2022-01-04) | The framework act on the creation and use of **industrial data**. Rights of **use and profit** in industrial data, promotion of use, and a standard-contract framework. Provides sector-specific data transaction standard contracts and guidelines for automotive, manufacturing, shipbuilding, bio-healthcare, energy, and more (A/B) |
| **Framework Act on Promotion of Data Industry and Use** (2021) | General foundation for data transactions and distribution (A) |
| **Personal Information Protection Act** | Worker personal data (access control, video, biometrics, location) (A) |
| **Special classification for the smart manufacturing technology industry** | Industrial classification scheme for smart factory deployment (B) |
| **Occupational Safety and Health Act · Serious Accidents Punishment Act** | Retention of safety-related records and remediation history. **Robot safety zone event logs become evidence after an accident** (C — text not verified) |

#### United States, by industry

| Law | Scope | Requirement |
|---|---|---|
| **21 CFR Part 11** | Pharma, medical devices | Electronic records and signatures. Six control areas: **system validation, audit trail, electronic signature, access control, record retention, system security**. Audit trails must be **secure, computer-generated, and timestamped**, recording who/what/when/**why** for every create, modify, and delete (A) |
| **EU GMP Annex 11** | 〃 (EU) | The full lifecycle of computerized systems: validation, operation, change control, retirement (A) |
| **PIC/S PI 041** (2021) | 〃 (international) | Adopts **ALCOA+** as the GMP inspection criterion (A) |
| **FSMA 204** | Food | KDEs for at least 2 years, produced within 24 hours (A) |
| **IATF 16949** | Automotive | See §4-2 (A) |
| **OSHA** | US workplaces | See §4-2 (A) |

### 7-4. ALCOA+ — worth using even outside regulated industries

**A**ttributable · **L**egible · **C**ontemporaneous · **O**riginal · **A**ccurate
**+** Complete · Consistent · Enduring · Available. (A)

Even outside pharma, those nine work **directly as a design checklist for monitoring data.**
*Contemporaneous* (no bulk after-the-fact recording) and *Original* (raw data untouched) are
**exactly the same conversation** as the timestamp and downsampling problems raised in §6-3. (C)

---

## 8. Summary — the order of decisions when starting a design

Compressed into an execution order, the survey gives **eight steps**.
**The order matters** — each later item assumes the answer to an earlier one.

| # | Decision | If you get it wrong |
|:---:|---|---|
| 1 | **Which regulations apply** (industry, export regions) | Retention periods and audit trail requirements change entirely. **Changing it later means a rebuild** |
| 2 | **Which of the five data layers** you are dealing with | One policy for all of them → over-engineering or loss |
| 3 | **Rate per layer** — in particular, terminate the kHz band at the edge | Bandwidth collapse |
| 4 | **Namespace design** — ISA-95 levels + Sparkplug B topic rules | Tag chaos in three years |
| 5 | **Time synchronization** — NTP/PTP | Inverted causality. Joins impossible |
| 6 | **Collector placement under 62443 zones & conduits** (read-only, unidirectional) | The monitoring system becomes attack surface |
| 7 | **Retention policy differentiated by resolution** (raw and aggregates separately) | Storage cost explosion or regulatory violation |
| 8 | **Data export API** (EU Data Act) | Legal exposure in the EU market after 2025-09-12 |

---

## What this survey could not confirm

Stated honestly.

- The specific data retention provisions of Korea's **Occupational Safety and Health Act** and
  **Serious Accidents Punishment Act** regarding robots — statutory text not read (left as C)
- The concrete data provisions of the **EU Machinery Regulation 2023/1230** and the **AI Act** —
  applicability needs a judgment call
- The record-keeping requirements of **ISO 10218 / ISO/TS 15066** (robot and collaborative robot
  safety) — outside the scope of this survey
- **Actual tag counts and daily growth on a real floor** — literature cannot tell you.
  **Measurement required**

---

## Sources

**Protocols and architecture** — HiveMQ (OPC UA/MQTT bridge) · EMQ (MQTT Sparkplug) · MTConnect
standard documents · MTCUP (Adapter/Agent protocol) · MachineMetrics (FANUC FOCAS) · MDPI (overview
of industrial robot control and programming)

**Storage and pipeline** — Tiger Data (SCADA data management) · TimescaleDB vs InfluxDB ·
UMH (historian vs. open-source DB) · iFactory (time-series DB selection) · Quix (storage tiering) ·
Oxmaint (IIoT data retention periods)

**Predictive maintenance and high frequency** — Nature Sci Rep (induction motor PdM from current and
vibration) · I-care (vibration analysis) · f7i.ai (predictive maintenance in robotics) ·
Fabrico (industrial robot maintenance software)

**Security and structural standards** — Fortinet (Purdue model) · Industrial Cyber (NIST, Purdue,
IEC 62443) · Shieldworkz (IEC 62443 + NIST SP 800-82) · Kontron AIS (SEMI standards overview, E134,
E147)

**Law** — EUR-Lex (text of Reg. (EU) 2023/2854) · Browne Jacobson (Data Act: manufacturing,
industry, automotive) · Mepca (the Data Act for machine builders) · Korea Law Information Center
(Industrial Digital Transformation Promotion Act) · SPRi (significance and implications of that act) ·
IATF 16949 7.5.3.2.1 · 8.5.2 · eCFR (21 CFR Part 1 Subpart S) · IntuitionLabs (21 CFR Part 11 audit
trails) · Eupry (EU GMP Annex 11) · TotalLab (ALCOA/ALCOA+) · OSHA (29 CFR 1904.33)

---

**Next** → [OPC UA Gives It Structure, MQTT Carries It (2)](../manufacturing-robot-data-02/)
