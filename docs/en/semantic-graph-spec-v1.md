---

## Chapter 1. Design Philosophy

### 1.1 Purpose

This specification defines a method for storing “meaning” in natural language as a **persistent semantic structure independent of statistics, context, and surface expressions**.

The method is designed so that, even under the influence of dictionaries, corpora, humans, AIs, and historical change,
the **meaning itself is preserved as an immutable data structure**.

### 1.2 Core Principles

| Layer        | What is stored           | Nature                                    |
| ------------ | ------------------------ | ----------------------------------------- |
| Meaning      | `core_concept` + triples | Immutable (meaning)                       |
| Context      | `conditions_json`        | Variable (context)                        |
| Evidence     | `triple_evidence`        | Additive / conflicting allowed            |
| Common sense | `triple_stats`           | Can change, decay, or invert              |
| Expression   | `expr_links`             | Language- / region-dependent              |
| Explanation  | 9-slot views             | Must not be stored; generated dynamically |

* Meaning (`core + triple`) is stored as history.
* Common sense, evidence, and expressions are allowed to change.

> The Language OS stores **meaning as relations**, not as “facts written in sentences”.

### 1.3 Representing Meaning as Triples

The OS stores meaning as a triple of three elements:

`(src_concept, rel_concept, dst_concept)`

Example:

```text
(core:knife.kitchen-001, core:use-purpose-001, core:cut.with_blade-001)
```

### 1.4 Separation of Labels and Meaning

* Words (strings) are **not** meaning.

* Words are stored as `expr_node` / `expr_links`,
  and treated as labels attached to meaning cores (`core_concept`).

* Word = language-level expression

* Meaning = the position that a `core_concept` occupies in the network

### 1.5 Immutable vs Mutable Data

| Type      | Example                                                                   | Change        |
| --------- | ------------------------------------------------------------------------- | ------------- |
| Immutable | “kitchen knife”, “cut with blade”, “cooking”; “knife → purpose → cutting” | Never deleted |
| Mutable   | Regional / temporal variation, allowed / forbidden, trends                | May change    |
| Additive  | Evidence, usage counts, statistics                                        | Grows         |
| Decay     | Decrease in usage frequency, becoming archaic                             | Decreases     |
| Inversion | “forbidden” → “allowed”, etc.                                             | Can flip      |

> The OS keeps meaning; only common sense and usage are allowed to change.

---

## Chapter 2. Node Specification

### 2.1 `core_concept` (Meaning Core)

A pure meaning unit that does **not** depend on any particular word.

Examples:

* “kitchen knife”
* “cutting with a blade”
* “steel material”
* “cooking domain”

Characteristics:

* Can be shared across multiple languages.
* Super-/sub-classes are derived from relations between concepts and restrictions on attributes.

**Naming convention (recommended):**

```text
core:<concept-name>.<category>-<number>
```

Examples:

* `core:knife.kitchen-001`
* `core:cut.with_blade-001`
* `core:domain.cooking-001`

### 2.2 `expr_node` (Expression Label)

Represents **surface expressions**, not meaning.

* Dialects, regions, and eras are stored on the `expr_links` side.

Examples:

* `"包丁_ja"`
* `"knife_en"`
* `"大判焼き_ja"`

One `core_concept` can be linked to multiple `expr_node`s.

> Implementation note: we do not store a separate `expr_node` table;
> in practice, `expr_id + expr_label` inside `expr_links` plays the role of an expression node.

### 2.3 `rel_concept` (Relation Core)

**Relation types themselves are also treated as cores.**

Examples: use/purpose, material, category, role, state, part, ingredient, domain membership, etc.

| Type               | Example core ID        |
| ------------------ | ---------------------- |
| Use / purpose      | `core:use-purpose-001` |
| Material           | `core:material-001`    |
| Ingredient         | `core:ingredient-001`  |
| Category           | `core:category-001`    |
| Role               | `core:role-001`        |
| State              | `core:state-001`       |
| Part               | `core:part-001`        |
| Domain (1st layer) | `core:domain-001`      |

### 2.4 Principle of Forward / Reverse Relation Pairs

When storing `(src, rel, dst)`, the OS **automatically generates the reverse triple**.

Example:

```text
(core:knife.kitchen-001, core:domain-001, core:domain.cooking-001)
```

Automatically generated:

```text
(core:domain.cooking-001, core:domain-of-001, core:knife.kitchen-001)
```

* The reverse triple copies **all** of the forward triple’s `conditions` and `polarity`.

### 2.5 Domain Nodes (Semantic Domains)

Domains are also represented as `core_concept`s.

Examples:

* `core:domain.cooking-001`
* `core:domain.medicine-001`
* `core:domain.sports-001`

> “Domain as a meaning” (membership) is stored as a core,
> while “domain as a condition where some relation holds” is stored in `conditions_json` (later).

---

## Chapter 3. Meaning Triple Specification (`meaning_triples`)

### 3.1 Purpose

This chapter defines how to treat `(src, rel, dst)` as an **immutable data structure** for storing meaning propositions.

* `meaning_triples` form the **historical layer** of the OS, and are **not deleted**.
* Changes in interpretation are expressed via **conditions, evidence, and statistics**, not by rewriting triples.

### 3.2 Triple Structure

```text
(src_concept_id, rel_concept_id, dst_concept_id)
```

| Field           | Type   | Description                             |
| --------------- | ------ | --------------------------------------- |
| triple_id       | UUID   | Unique ID                               |
| src_concept_id  | core:* | Subject                                 |
| rel_concept_id  | core:* | Relation                                |
| dst_concept_id  | core:* | Object                                  |
| conditions_json | JSON   | Conditions for validity (see Chapter 4) |
| polarity        | enum   | `positive` / `negative`                 |
| status          | enum   | `draft` / `active` / `deprecated`       |
| note            | text   | Optional note                           |

### 3.3 `polarity` (Proposition Sign)

| Value    | Meaning                                                                 |
| -------- | ----------------------------------------------------------------------- |
| positive | S-R-D holds under given conditions                                      |
| negative | S-R-D does **not** hold / forbidden / impossible under given conditions |

Positive example:

```text
(core:knife.kitchen-001, core:use-purpose-001, core:cut.with_blade-001)
polarity = positive
```

Negative example (prohibition):

```text
(core:raw-chicken-001, core:use-purpose-001, core:sashimi-001)
polarity = negative
conditions = {domain:["cooking"], region:["JP"]}
```

### 3.4 Automatic Generation of Reverse Triples

When a triple is registered, the OS **always generates a forward–reverse pair**.

| Input                       | Automatically generated         |
| --------------------------- | ------------------------------- |
| `(A, core:material-001, B)` | `(B, core:material-for-001, A)` |
| `(A, core:domain-001, B)`   | `(B, core:domain-of-001, A)`    |

* Reverse triples copy the forward triple’s `conditions` and `polarity` **exactly**.

### 3.5 Triples Represent Meaning, Not Evidence

**Disallowed operations:**

| Operation                    | Reason                                                            |
| ---------------------------- | ----------------------------------------------------------------- |
| Deleting triples             | Would be historical tampering                                     |
| Overwriting triples          | Interpretation should be updated by conditions / evidence / stats |
| Merging / collapsing triples | Would erase subtle meaning differences                            |

* Triples, including incorrect interpretations by humans or AIs, are preserved as history.
* Their correctness is evaluated **later** by `evidence` and `stats`.

---

## Chapter 4. Condition Specification (`conditions_json`)

### 4.1 Role

`conditions_json` represents **conditions under which a triple holds**.

* It does **not** encode meaning itself, but **the domain of validity**.
* Even if the conditions change, the triple stays the same.

### 4.2 JSON Keys

| Key        | Example values                |
| ---------- | ----------------------------- |
| domain     | `["cooking","medicine"]`      |
| region     | `["JP","JP-Kansai"]`          |
| era        | `["Showa","Heisei"]`          |
| year_range | `[1950,2000]`                 |
| lang       | `"ja"`                        |
| register   | `"slang","academic"`          |
| medium     | `"speech","net","literature"` |
| freq       | `0.8` (tendency / frequency)  |

### 4.3 Condition Combination Semantics

* Conditions are interpreted as **logical AND**.

Example:

```json
{ "domain":["cooking"], "region":["JP-Kansai"] }
```

→ “Holds in **Kansai-region cooking** context.”

* Missing keys = no constraints.
  → `{}` means “generally valid, no explicit restriction”.
* Empty arrays and `null` are **forbidden**.
  → The key should be omitted instead.

### 4.4 Dual Role of `domain` (Important)

| Role                           | Where stored              | Example                                    |
| ------------------------------ | ------------------------- | ------------------------------------------ |
| Which world concept belongs to | Triple: `core:domain-001` | “Knife belongs to cooking domain”          |
| Where a relation holds         | `conditions.domain`       | “Purpose relation holds in cooking domain” |

* “Knife is a cooking tool” → triple.
* “The use-purpose relation holds in cooking domain” → conditions.

### 4.5 Granularity of Region / Era / Lang

* Stored as flat labels:

Example:

```json
"region": ["JP-Kyoto"]
```

* Interpreted as hierarchy at OS runtime:

  * `"JP-Kyoto" ⊂ "JP"`
  * `"Edo"` corresponds to `year_range = [1603, 1868]` in some internal mapping

> The DB remains simple; hierarchical / temporal interpretation is a runtime concern.

### 4.6 `freq` Handling

* `freq` expresses the tendency for the triple to hold (0.0–1.0 recommended).

Examples:

* `{ "freq": 0.9 }` → usually holds
* `{ "freq": 0.3 }` → rarely holds, but has some examples

`freq` is part of **conditions**
and is distinct from “common sense degree” (`stats.confidence`).

### 4.7 Boundaries between Conditions, Evidence, and Stats

| Data       | Represents               | Change type                 |
| ---------- | ------------------------ | --------------------------- |
| triple     | Proposition (meaning)    | Immutable                   |
| conditions | Context / validity range | Immutable or additive       |
| evidence   | Evidence                 | Additive, can conflict      |
| stats      | Common sense / usage     | Can change / decay / invert |

* Conditions: “preconditions for truth”
* Evidence: “support / counter-evidence”
* Statistics: “social change”

> Up to this point, we have defined the **immutable layer** (meaning + conditions).

---

## Chapter 5. Evidence Specification (`triple_evidence`)

### 5.1 Purpose

`triple_evidence` stores **pieces of evidence** for meaning triples.

* Multiple pieces of evidence may support or refute the same triple.
* Evidence does **not** modify the triple itself.
* Meaning is **evaluated** by evidence.

### 5.2 Data Structure

**Table: `triple_evidence`**

| Column        | Type      | Description                                               |
| ------------- | --------- | --------------------------------------------------------- |
| evidence_id   | UUID      | Evidence record ID                                        |
| triple_id     | FK        | Reference to `meaning_triples`                            |
| evidence_type | enum      | `dictionary` / `corpus` / `human` / `rule` / `hypothesis` |
| source_kind   | enum      | `reference` / `human` / `corpus` / `ai` / `rule`          |
| stance        | enum      | `positive` / `negative`                                   |
| weight        | float     | Confidence in this evidence (0.0–1.0)                     |
| source_detail | text      | Dictionary ID, URL, citation, sentence ID, etc.           |
| note          | text      | Optional memo                                             |
| created_at    | timestamp | Time of registration                                      |

### 5.3 `evidence_type` (Method)

| Type       | Description                                 |
| ---------- | ------------------------------------------- |
| dictionary | Dictionaries, encyclopedias, lexicons       |
| corpus     | Real usage in texts, web, SNS, etc.         |
| human      | Expert, editor, or user judgments           |
| rule       | Systematic rules (cooking, law, chemistry…) |
| hypothesis | Hypothesis or unverified assumption         |

### 5.4 `source_kind` (Source Attribute)

| Value     | Description                                       |
| --------- | ------------------------------------------------- |
| reference | Authoritative reference (dictionary, paper, etc.) |
| corpus    | Collection of texts / news / SNS                  |
| human     | Individual human                                  |
| ai        | NLP / LLM                                         |
| rule      | Formalized rule systems                           |

### 5.5 `stance` (Support / Opposition)

* `positive`: Evidence that the triple **does** hold.
* `negative`: Evidence that the triple **does not** hold / is forbidden.

Examples:

* Social media post: “Raw chicken sashimi is great.” → `positive`
* Government guideline: “Raw chicken must not be eaten raw.” → `negative`

Both supporting and opposing evidence are valid and stored.

### 5.6 `weight` (Evidence-Level Confidence)

`weight` is a confidence score for the individual evidence, not for the triple.

* Real-valued in [0.0, 1.0]
* Can be set by user or computed automatically

Example heuristics:

| Evidence type      | Typical weight |
| ------------------ | -------------- |
| Dictionary / paper | 0.9            |
| Law / regulation   | 1.0            |
| Personal blog      | 0.3            |
| Generated AI       | 0.4            |
| Systematic rule    | 0.8–1.0        |

### 5.7 Relationship between Triples and Evidence

| Role     | Stores                        | Updates       |
| -------- | ----------------------------- | ------------- |
| triple   | Proposition                   | Immutable     |
| evidence | Supporting / opposing reasons | Additive only |
| stats    | Quantitative social change    | Updatable     |

> Triple = tombstone
> Evidence = court documents
> Stats = public opinion

---

## Chapter 6. Common Sense / Statistics Specification (`triple_stats`)

### 6.1 Purpose

`triple_stats` handles the **degree to which a triple is socially accepted (common sense)**.

* How people currently interpret the triple
* How frequently it is used
* In which conditions it is mainstream

Evidence is “supporting documents”,
while stats are “current public opinion”.

### 6.2 Data Structure

**Table: `triple_stats`**

| Column       | Type      | Description                            |
| ------------ | --------- | -------------------------------------- |
| triple_id    | FK        | Reference to `meaning_triples`         |
| usage_count  | integer   | Number of times used in OS/API/GUI     |
| corpus_count | integer   | Number of occurrences in corpora       |
| stance_score | float     | Support vs. opposition score (0.0–1.0) |
| confidence   | float     | Overall common-sense score (0.0–1.0)   |
| last_used_at | timestamp | Last time the triple was used          |

### 6.3 `confidence` (Common Sense Score)

Example formula:

```text
confidence = (stance_score * 0.7) + (normalized(corpus_count) * 0.3)
```

* This formula is versioned and may improve over time.

### 6.4 Decay over Time

* `corpus_count` and related measures may **decay over time**.
* Past common sense becomes “past common sense”.

Example:

```text
corpus_count = corpus_count * 0.99^(years_elapsed)
```

> Meaning persists; common sense becomes outdated.

### 6.5 Inversion of Common Sense (Example)

| Era  | Proposition                         | Status   |
| ---- | ----------------------------------- | -------- |
| 1960 | “Smoking is allowed in restaurants” | positive |
| 2025 | “Smoking is banned in restaurants”  | negative |

* The triple structure is the same.
* Evidence and stats **reverse** over time.

### 6.6 Role Comparison: Triple / Evidence / Stats

| Layer    | Example                       | Change type         |
| -------- | ----------------------------- | ------------------- |
| triple   | “knife → purpose → cutting”   | Immutable           |
| evidence | Ministry guideline, SNS posts | Additive            |
| stats    | Frequency, “common sense”     | Can change / invert |

**Summary so far (Immutable + Evaluation Layers)**

| Layer            | Entity                       | Nature                |
| ---------------- | ---------------------------- | --------------------- |
| Immutable layer  | `core + triple + conditions` | Stored only           |
| Evaluation layer | `evidence + stats`           | Add / update / invert |

> ⛓ The OS is a **semantic history archive**;
> evaluation is left to society and its changes.

---

## Chapter 7. Expression Specification (`expr_links`)

### 7.1 Purpose

`expr_links` is the layer that attaches **surface expressions (words, notations)** to `core_concept`s.

* Words are **human-facing labels**, not meaning.
* The OS performs reasoning based on **concept IDs**, not on words.

### 7.2 Data Structure

**Table: `expr_links`**

| Column          | Type   | Description                                                              |
| --------------- | ------ | ------------------------------------------------------------------------ |
| expr_id         | UUID   | Persistent ID for the expression link                                    |
| expr_label      | string | Expression string (word / notation)                                      |
| core_concept_id | core:* | Linked meaning core                                                      |
| conditions_json | JSON   | Conditions under which this expression is used (lang / region / era / …) |
| source_kind     | enum   | `reference` / `human` / `corpus` / `ai` / `rule`                         |
| source_detail   | text   | Source information                                                       |
| note            | text   | Internal memo                                                            |

### 7.3 Word vs Meaning (Separation Rules)

| Role       | Where stored               | Change allowed               |
| ---------- | -------------------------- | ---------------------------- |
| Words      | `expr_node` + `expr_links` | Can be renamable / deletable |
| Meaning    | `core + triple`            | Immutable                    |
| Usage bias | `stats`                    | Mutable                      |

* Changes in words (name changes, trends, obsolescence) are allowed.
* Meaning (`core`) is kept stable.

### 7.4 Regional / Dialect / Temporal Differences

Example:

```text
expr_label: "今川焼"
conditions: {lang:"ja", region:["JP-Kanto"]}

expr_label: "大判焼き"
conditions: {lang:"ja", region:["JP-Hokkaido"]}

expr_label: "回転焼き"
conditions: {lang:"ja", region:["JP-Kansai"]}
```

All can be linked to the same core:

```text
core:imagawa-yaki-001
```

### 7.5 Difference between Expression Conditions and Triple Conditions

| Purpose                  | Stored in         | Example                                             |
| ------------------------ | ----------------- | --------------------------------------------------- |
| Where expression is used | `expr_links`      | “大判焼き” is used in Hokkaido                          |
| Where meaning holds      | `meaning_triples` | “Raw chicken cannot be sashimi (in cooking domain)” |

### 7.6 Polysemy (Multiple Meanings per Word)

Polysemous words (e.g., *bank*) are simply linked to multiple cores:

```text
"bank_en" → core:bank.river-001
"bank_en" → core:bank.finance-001
```

In the OS, one word can correspond to multiple meanings;
each meaning is represented as an independent `core_concept`.

---

## Chapter 8. 9-Slot View (Reading Model)

### 8.1 Role of the View

The 9 slots (WHO / WHAT / WHY / HOW / WHERE / WHEN / OUTCOME / STATE + TARGET / DISC)
are **output / explanation structures**, not stored data.

* What is stored: triples
* What explains: views

The view is constructed on the fly from triples.

> Implementation rule: views must **only** be generated at **API / UI rendering time**,
> and must never be stored as persistent data.

### 8.2 “View Must Not Be Stored” Rule

| Operation                     | Status      |
| ----------------------------- | ----------- |
| Persisting 9-slot views in DB | ❌ Forbidden |
| Manual editing of views       | ❌ Forbidden |
| Generating views from triples | ✔ Allowed   |

A view is a **function** that renders meaning, not a data record itself.

### 8.3 Focus (Choosing the “Main Actor”)

When generating a view, the OS selects which `core` is treated as the focus.

* The focus determines how the triple is phrased.

Example: focusing on the knife:

```text
(core:knife.kitchen-001, core:material-001, core:steel-001)
→ HOW: made of steel
```

Focusing on the steel:

```text
(core:steel-001, core:material-for-001, core:knife.kitchen-001)
→ OUTCOME / TARGET: steel is used for knives
```

> The triple is the same, but the meaning changes depending on which concept is the focus.

### 8.4 Mapping `rel_concept` → Slots

| Relation    | Typical slot(s) for the focus     |
| ----------- | --------------------------------- |
| use-purpose | OUTCOME / TARGET                  |
| material    | HOW                               |
| ingredient  | WHAT / HOW                        |
| category    | WHAT                              |
| role        | WHY / WHAT                        |
| part        | WHERE / STATE                     |
| state       | STATE                             |
| domain      | DISC (domain / field description) |

* The slot assigned to the focus differs between forward and reverse relations.

### 8.5 Difference in Display between Forward / Reverse

Example:

```text
(core:knife, use-purpose, core:cut)
```

| Focus | Display          |
| ----- | ---------------- |
| knife | Purpose: cutting |
| cut   | Tool: knife      |

### 8.6 Example: Knife Profile (Auto-Generated View)

For example, focusing on `core:knife.kitchen-001`,
the 9-slot view might be:

* WHO: (none; tools are not agents)
* WHAT: kitchen knife (cooking blade tool)
* WHY: to accomplish cooking tasks
* HOW: made of steel / ceramic, etc.
* WHERE: used in kitchen / restaurant kitchen
* WHEN: during food preparation
* OUTCOME: cutting
* STATE: sharpness, rust, hardness
* DISC: cooking domain

All of these are derivable from triples.
The view is the **commentator** for triples.

> This is where the OS provides a complete semantic inspection for a concept.

---

## Chapter 9. Design Principles Summary

### 9.1 What the OS Stores

| Type              | Stored? | Nature                             |
| ----------------- | ------- | ---------------------------------- |
| `core_concept`    | ✔       | Immutable                          |
| `meaning_triples` | ✔       | Immutable                          |
| `conditions_json` | ✔       | Immutable or additive only         |
| `triple_evidence` | ✔       | Additive only                      |
| `triple_stats`    | ✔       | Updatable / decaying / invertible  |
| `expr_links`      | ✔       | Add / modify / soft-delete allowed |
| 9-slot view       | ❌       | Must not be stored (render only)   |

> The OS stores **only meaning** in the immutable layer,
> and leaves interpretation to the mutable layers.

### 9.2 Definition of Meaning

* Meaning is the **network position** of a `core_concept` as defined by `meaning_triples`.
* No standalone “definition sentences” are stored.
* Meaning emerges from the **structure of relations to other concepts**.

### 9.3 Separation of Words and Meaning

| Words            | Meaning                |
| ---------------- | ---------------------- |
| Expressions      | Concepts               |
| Change over time | Do not change          |
| Region-dependent | Not affected by region |
| May be deleted   | May **not** be deleted |

* Words are labels.
* Meaning is network structure.

### 9.4 Principle of Reverse Triple Generation

* Humans (and AIs inserting data) **only input forward triples**.
* Reverse triples are always automatically generated by the OS.
* Conditions and polarity are copied as-is.

Goal:

* Humans only have to care about direction.
* The OS can perform **multi-directional reasoning**.

### 9.5 Two-Layer Structure of `domain`

| Purpose                 | “What kind of domain?”                  | Where stored |
| ----------------------- | --------------------------------------- | ------------ |
| Concept membership      | “Knife is a cooking tool”               | Triple       |
| Validity of proposition | “The purpose relation holds in cooking” | Conditions   |

* Domain appears both as a **concept** and as a **condition**,
  but with different roles.

### 9.6 Common Sense Is Not Fact

| Kind       | Content                   | Change                  |
| ---------- | ------------------------- | ----------------------- |
| meaning    | Propositions, not “facts” | Immutable               |
| evidence   | Supporting information    | Additive                |
| stats      | Common sense              | Changing                |
| expression | Words / labels            | Changing, can disappear |

> The OS is not a dictionary; it is a **semantic history archive**.
> Common sense is a transient “state of society”.

### 9.7 Future Models of the OS

| Model | Description                                                   | Current project stage |
| ----- | ------------------------------------------------------------- | --------------------- |
| A     | Manual entry – hand-crafted meaning                           | Current status        |
| B     | Semi-automatic generation from statistics / UD / dictionaries | Short-term goal       |
| C     | Autonomous reasoning – self-proposed cores / triples          | Long-term goal        |
| D     | Scientific reasoning – meaning → inference → world model      | Conceptual future     |

At present, we are designing A robustly with a view toward B.
In future models C/D, the OS itself may propose new meanings.

---

## 📎 Appendix A: Prohibited Operations

| Operation                                 | Reason                                                             |
| ----------------------------------------- | ------------------------------------------------------------------ |
| Deleting triples                          | Historical tampering                                               |
| Overwriting triples                       | Interpretation should be changed via conditions / evidence / stats |
| Persisting views                          | Freezing explanations causes contradictions                        |
| Deleting cores                            | Would destroy all linked triples                                   |
| Using empty arrays / `null` in conditions | Makes meaning ambiguous                                            |

---

## 📎 Appendix B: Recommended Implementation Priorities

| Priority | Target                                                                     |
| -------- | -------------------------------------------------------------------------- |
| 1        | `core_concept` / `rel_concept` registration and forward–reverse generation |
| 2        | `meaning_triples` (with conditions)                                        |
| 3        | `expr_links` (regional / orthographic variants)                            |
| 4        | `triple_evidence` (dictionary → human → corpus → AI, in that order)        |
| 5        | `triple_stats` (can be implemented later)                                  |
| 6        | Views (rendering only, no persistence)                                     |

---

## 📎 Appendix C: Recommended Query Examples (Early Implementations)

**List all purposes of the kitchen knife**

```sql
SELECT dst_concept_id
FROM meaning_triples
WHERE src_concept_id = 'core:knife.kitchen-001'
  AND rel_concept_id = 'core:use-purpose-001';
```

**All concepts classified as “blade tools”**

```sql
SELECT src_concept_id
FROM meaning_triples
WHERE rel_concept_id = 'core:category-001'
  AND dst_concept_id = 'core:knife.blade-tool-001';
```

**“Cutting tools” group (view logic)**

```sql
SELECT src_concept_id
FROM meaning_triples
WHERE rel_concept_id = 'core:use-purpose-001'
  AND dst_concept_id = 'core:cut.with_blade-001';
```

---

## Chapter 10. Data Management Specification (Storage & Editing)

This chapter defines how the logical model of Chapters 1–9 is managed in actual data form.

* **Storage format (internal)**:
  The tables / CSV structures that the OS keeps persistently.
  Immutable layer (`core`, `triple`, `conditions`) + mutable layers (`evidence`, `stats`, `expr`).

* **Editing format (editor view)**:
  Views used by humans for editing / browsing.
  IDs and JSON are hidden as much as possible; instead, humans see words, labels, and decomposed columns.

> This chapter is primarily intended for implementers.

### 10.1 Basic Type Policy

| Type name | Description                                                      |
| --------- | ---------------------------------------------------------------- |
| string    | Arbitrary UTF-8 string                                           |
| uuid      | UUID or unique ID string (e.g., `t00000001`)                     |
| core_id   | Reference to `core_concepts.core_id`                             |
| json      | JSON string; structured internally, edited via flattened columns |
| enum      | One of a predefined set of strings                               |
| int       | Integer                                                          |
| float     | Floating point; typically 0.0–1.0 in this spec                   |
| bool      | 0/1 or true/false                                                |
| timestamp | Date + time                                                      |

### 10.2 Managing `core_concepts` (Meaning Nodes)

#### 10.2.1 Storage (Internal)

📌 **1) `core_concepts_editor` (human-facing editing)**

| Column           | Description                                        | Type         | Example                       |
| ---------------- | -------------------------------------------------- | ------------ | ----------------------------- |
| core_id          | Core ID (persistent, immutable)                    | string       | `core:knife.kitchen-001`      |
| can_be_relation  | Whether it can be used as a relation               | bool (0/1)   | 1                             |
| status_view      | Status for human viewing                           | enum         | `active`                      |
| domain           | Main domains (`;` separated)                       | string(list) | `cooking;weapons`             |
| region           | Main regions (`;` separated)                       | string(list) | `JP;US`                       |
| era              | Main eras (`;` separated)                          | string(list) | `Showa;Heisei;Reiwa`          |
| concept_strength | Concept strength (degree of cultural independence) | float        | 0.95                          |
| note             | Internal memo                                      | text         | e.g., “kitchen tool category” |

📌 **2) `core_concepts_internal` (OS storage)**

| Column               | Description                                              | Source                     |
| -------------------- | -------------------------------------------------------- | -------------------------- |
| core_id              | Same as editor                                           | from editor                |
| can_be_relation      | Same as editor                                           | from editor                |
| status_view          | Same as editor                                           | from editor                |
| core_conditions_json | JSON containing domain / region / era / concept_strength | auto-generated from editor |
| note                 | Same as editor                                           | from editor                |

---

### 10.3 Managing `meaning_triples` (Triples)

#### 10.3.1 Storage (Internal)

**Table: `meaning_triples`**

| Column          | Type                                | Req | Description                                                      |
| --------------- | ----------------------------------- | --- | ---------------------------------------------------------------- |
| triple_id       | uuid                                | ✔   | Persistent triple ID, immutable                                  |
| src_core_id     | core_id                             | ✔   | Subject core                                                     |
| rel_core_id     | core_id                             | ✔   | Relation core (`can_be_relation = 1`)                            |
| dst_core_id     | core_id                             | ✔   | Object core                                                      |
| conditions_json | json                                | ✔   | Conditions for validity; `{}` is allowed                         |
| polarity        | enum(`positive`,`negative`)         | ✔   | Positive / negative proposition                                  |
| status          | enum(`draft`,`active`,`deprecated`) | ✔   | Draft / active / deprecated; deletion forbidden                  |
| is_reverse      | bool                                | ✔   | 0 = forward triple; 1 = auto-generated reverse                   |
| reverse_of      | uuid or null                        | opt | For reverse triples, ID of the original triple; null for forward |
| created_at      | timestamp                           | ✔   | Registration time                                                |
| note            | string                              | opt | Internal memo; not part of meaning                               |

#### 10.3.2 Editing Format (Editor View)

**Table / View: `meaning_triples_editor`**

| Column        | Type                     | Edit | Description                                                                                                       |
| ------------- | ------------------------ | ---- | ----------------------------------------------------------------------------------------------------------------- |
| focus_expr    | string                   | ✔    | Expression label on subject side (e.g., “包丁” / “knife”). Resolved to `src_core_id`.                               |
| rel_label     | string                   | ✔    | Relation label (e.g., “用途” / “purpose”, “素材” / “material”). Resolved to `rel_core_id`.                            |
| value_expr    | string                   | ✔    | Expression label on object side (e.g., “鋼” / “steel”, “刃物で切る” / “cutting with blade”). Resolved to `dst_core_id`. |
| src_core_id   | core_id                  | auto | Resolved ID; read-only                                                                                            |
| rel_core_id   | core_id                  | auto | Resolved ID; read-only                                                                                            |
| dst_core_id   | core_id                  | auto | Resolved ID; read-only                                                                                            |
| domain        | string                   | ✔    | For `conditions.domain`. Multiple values: `"cooking;medicine"`.                                                   |
| region        | string                   | ✔    | For `conditions.region`. e.g., `"JP;JP-Kansai"`.                                                                  |
| era           | string                   | ✔    | For `conditions.era`. e.g., `"Showa;Heisei"`.                                                                     |
| year_from     | int or null              | ✔    | Maps to `conditions.year_range[0]`; null = unspecified                                                            |
| year_to       | int or null              | ✔    | Maps to `conditions.year_range[1]`; null = unspecified                                                            |
| lang          | string                   | ✔    | Maps to `conditions.lang`; empty → key omitted                                                                    |
| register      | string                   | ✔    | Maps to `conditions.register`; multiple values allowed                                                            |
| medium        | string                   | ✔    | Maps to `conditions.medium`; multiple values allowed                                                              |
| freq          | float or null            | ✔    | Maps to `conditions.freq`; 0.0–1.0; null = key omitted                                                            |
| polarity_view | enum(`肯定`,`否定`)          | ✔    | Human-facing; mapped to `polarity` on save                                                                        |
| status_view   | enum(`ドラフト`,`有効`,`廃止候補`) | ✔    | Human-facing; mapped to `status` on save                                                                          |
| note          | string                   | ✔    | Internal memo; stored in `meaning_triples.note`                                                                   |

Saving rules:

* Labels → resolved to `core_id`
* `domain` / `region` / `era` / `year_*` / `lang` / `register` / `medium` / `freq` → merged into `conditions_json`
* `polarity_view` → `"positive"` / `"negative"`
* `status_view` → `"draft"` / `"active"` / `"deprecated"`
* Only **forward triples** are inserted; reverse triples are generated automatically (`is_reverse = 1`)

---

### 10.4 `conditions_json` (Context Conditions) Specification

#### 10.4.1 Storage Format (JSON)

Stored in:

* `meaning_triples.conditions_json`
* `expr_links.conditions_json`

Example:

```json
{
  "domain": ["cooking"],
  "region": ["JP-Kansai"],
  "era": ["Showa", "Heisei"],
  "year_range": [1950, 2000],
  "lang": "ja",
  "register": ["slang"],
  "medium": ["speech", "net"],
  "freq": 0.8
}
```

| Key        | Type      | Notes                           |
| ---------- | --------- | ------------------------------- |
| domain     | [string]  | Domains where proposition holds |
| region     | [string]  | Regions (hierarchy is runtime)  |
| era        | [string]  | Era labels                      |
| year_range | [int,int] | Gregorian year range            |
| lang       | string    | Main language                   |
| register   | [string]  | Style / register                |
| medium     | [string]  | Medium                          |
| freq       | float     | 0.0–1.0 tendency                |

Rules:

* Conditions are interpreted as AND.
* Missing keys = no constraint.
* Empty arrays / `null` are forbidden (omit the key instead).
* `freq` is clipped to [0.0,1.0].
* Conversion between editor columns and JSON follows 10.3.2.

---

### 10.5 Managing `expr_links` (Expression ↔ Core Links)

#### 10.5.1 Storage Format (Internal)

**Table: `expr_links`**

| Column          | Type                                           | Req | Description                                      |
| --------------- | ---------------------------------------------- | --- | ------------------------------------------------ |
| expr_id         | uuid                                           | ✔   | Persistent ID of expression link                 |
| expr_label      | string                                         | ✔   | Expression string                                |
| core_id         | core_id                                        | ✔   | Linked core                                      |
| conditions_json | json                                           | ✔   | Conditions under which this expression is used   |
| source_kind     | enum(`reference`,`corpus`,`human`,`ai`,`rule`) | ✔   | Source type                                      |
| source_detail   | string                                         | opt | Source information (dictionary name, URL, etc.)  |
| status          | enum(`active`,`deprecated`,`draft`)            | ✔   | Status; can use `deprecated` instead of deletion |
| created_at      | timestamp                                      | ✔   | Registration time                                |
| updated_at      | timestamp                                      | ✔   | Last update time                                 |
| note            | string                                         | opt | Internal memo                                    |

#### 10.5.2 Editing Format (Editor View)

**View: `expr_links_editor`**

| Column            | Type                    | Edit | Description                                               |
| ----------------- | ----------------------- | ---- | --------------------------------------------------------- |
| expr_label        | string                  | ✔    | Expression string                                         |
| core_id_or_search | string                  | ✔    | Specify or search for core; resolved to `core_id` on save |
| lang              | string                  | ✔    | Maps to `conditions.lang`; usually required               |
| region            | string                  | ✔    | Maps to `conditions.region`; multiple via `;` separated   |
| era               | string                  | ✔    | Maps to `conditions.era`; multiple allowed                |
| register          | string                  | ✔    | Maps to `conditions.register`; multiple allowed           |
| medium            | string                  | ✔    | Maps to `conditions.medium`; multiple allowed             |
| freq              | float or null           | ✔    | Maps to `conditions.freq`; optional                       |
| source_kind       | enum                    | ✔    | Source type                                               |
| source_detail     | string                  | ✔    | Source detail                                             |
| status            | enum(`ドラフト`,`有効`,`非推奨`) | ✔    | Mapped to internal `status` enum on save                  |
| note              | string                  | ✔    | Internal memo                                             |

Saving:

* `lang` / `region` / `era` / `register` / `medium` / `freq` → merged into `conditions_json`
* `core_id_or_search` → resolved to `core_id`
* Human-friendly `status` → internal enum

---

### 10.6 Managing `triple_evidence` (Evidence)

#### 10.6.1 Storage Format (Internal)

**Table: `triple_evidence`**

| Column        | Type                                                    | Req | Description                         |
| ------------- | ------------------------------------------------------- | --- | ----------------------------------- |
| evidence_id   | uuid                                                    | ✔   | Evidence record ID                  |
| triple_id     | uuid                                                    | ✔   | Target `meaning_triples.triple_id`  |
| evidence_type | enum(`dictionary`,`corpus`,`human`,`rule`,`hypothesis`) | ✔   | Type of evidence                    |
| source_kind   | enum(`reference`,`corpus`,`human`,`ai`,`rule`)          | ✔   | Source attribute                    |
| stance        | enum(`positive`,`negative`)                             | ✔   | Supports / opposes the triple       |
| weight        | float                                                   | ✔   | Confidence (0.0–1.0)                |
| source_detail | string                                                  | opt | Citation / URL / dictionary ID etc. |
| note          | string                                                  | opt | Comment                             |
| created_at    | timestamp                                               | ✔   | Time of registration                |

#### 10.6.2 Editing Format (Editor View)

**View: `triple_evidence_editor`**

| Column         | Type            | Edit | Description                                          |
| -------------- | --------------- | ---- | ---------------------------------------------------- |
| triple_summary | string          | auto | Human-readable summary (“knife / purpose / cutting”) |
| triple_id      | uuid            | auto | Triple ID; not editable                              |
| evidence_type  | enum            | ✔    | Type of evidence                                     |
| source_kind    | enum            | ✔    | Source type                                          |
| stance         | enum(`支持`,`否定`) | ✔    | Mapped to `"positive"` / `"negative"` on save        |
| weight         | float           | ✔    | Confidence                                           |
| source_detail  | string          | ✔    | Source info                                          |
| note           | string          | ✔    | Comment                                              |

---

### 10.7 Managing `triple_stats` (Common Sense / Statistics)

#### 10.7.1 Storage Format (Internal)

**Table: `triple_stats`**

| Column       | Type      | Req | Description                                                 |
| ------------ | --------- | --- | ----------------------------------------------------------- |
| triple_id    | uuid      | ✔   | Target triple; PK and FK                                    |
| usage_count  | int       | ✔   | Number of times referred in OS/API/GUI                      |
| corpus_count | int       | ✔   | Frequency in corpora                                        |
| stance_score | float     | ✔   | Score derived from supporting / opposing evidence (0.0–1.0) |
| confidence   | float     | ✔   | Overall common sense score (0.0–1.0)                        |
| last_used_at | timestamp | ✔   | Last time used                                              |

* Usually **auto-computed and updated** only.
  Direct manual editing by humans is not expected.

#### 10.7.2 Viewing (Read-Only View)

**View: `triple_stats_view`**

| Column         | Description                          |
| -------------- | ------------------------------------ |
| triple_summary | Human-readable summary of the triple |
| triple_id      | Triple ID                            |
| usage_count    | How often this triple is accessed    |
| corpus_count   | How often it appears in corpora      |
| stance_score   | Degree of support                    |
| confidence     | Strength as common sense             |
| last_used_at   | Last usage timestamp                 |

---

### 10.8 Views (9-Slot) and Persistence

The 9-slot views (WHO / WHAT / WHY / HOW / WHERE / WHEN / OUTCOME / STATE / DISC) are **dynamic views only**.

* They are never stored in tables.
* They are generated at runtime from:

  * `meaning_triples`
  * `conditions_json`
  * `expr_links`

> Views exist only as **API / UI rendering outputs**, not as persistent entities.

---

### 10.9 Summary: Mapping Editing Format ↔ Storage Format

| Layer            | Storage table             | Editing view             | Editable?                          |
| ---------------- | ------------------------- | ------------------------ | ---------------------------------- |
| core_concept     | `core_concepts`           | `core_concepts_view`     | Mostly read-only (ID + flags)      |
| meaning (triple) | `meaning_triples`         | `meaning_triples_editor` | Forward triples only               |
| conditions       | `conditions_json` columns | Multiple editor columns  | JSON generated by OS               |
| expressions      | `expr_links`              | `expr_links_editor`      | Add / modify / delete expressions  |
| evidence         | `triple_evidence`         | `triple_evidence_editor` | Additive (deletion is operational) |
| stats            | `triple_stats`            | `triple_stats_view`      | Auto-update only                   |
| view (9-slot)    | Not stored                | UI rendering only        | Persistence forbidden              |

> With Chapter 10, the abstract model of Chapters 1–9
> is fully mapped to concrete tables / CSVs for the Language OS.

---
