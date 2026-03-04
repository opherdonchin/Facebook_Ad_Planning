# Weekly Prompt for processing facebook ads

This prompt is pasted in every week to process data on previous ad runs and plan the ad run for the coming week.

## Assumed uploads (hard stop if violated)

This prompt assumes that files are uploaded in **two batches**. If any required file in a batch is missing or unreadable, **stop processing, notify the user, and wait for instructions**. Verify that each file can actually be read. Make sure that you have read each file and processed it and notify the user that it has been succesfully processed.

**Batch 1 (ad level, receive first — do not begin analysis yet)**

1. `ad_weekly_performance.csv`
2. `ad_run_summary.csv`
3. `performance_data.json`
4. `decision_log.md`

**Batch 2 (components + assets + lifetime — only after this batch is fully processed may analysis begin)**

1. `component_tags.csv`
2. `attachments_manifest.json`
3. `attachments.tar`
4. `ad_lifetime_summary.csv`
5. `component_media_lifetime.csv`
6. `component_headline_lifetime.csv`
7. `component_text_lifetime.csv`

When Batch 1 arrives, read and acknowledge it, then **wait** for Batch 2 without performing any analysis or drafting outputs. When Batch 2 arrives, confirm **both batches** are fully processed before beginning any analysis or preparing a response.

All uploaded data files (except `decision_log.md`) are described in `data_schema.md`.

Agents must consult `data_schema.md` to understand:

- the purpose perof each file
- table grain and column semantics
- which file is the canonical source for each type of information

The required structure and formatting rules for decision-log entries are defined in `decision_log_format.md`.

We have encountered past situations with this process where agents made decisions without checking actual file contents. Thus, it is important to make extra sure that the information is up to date.

You should also review `PROJECT_GUIDE.md` to confirm alignment with current intentions, updating it if necessary.

---

## Mandatory clarifications (read before analysis)

1. **Week disambiguation is mandatory**
   
   * Explicitly distinguish between:
     
     * (a) the **latest completed data week** (being assessed)
     * (b) the **decision week** (being planned)
     * (c) the **current contiguous run** for each ad
   
   * These must never be conflated.

2. **Decision-log format compliance is mandatory**
   
   * Read `decision_log_format.md` before doing any week identification or writing any decision-log output.
   * Any new entry written to `decision_log.md` must follow the required heading structure defined there:
     * Decision week (planned)
     * Assessed week (data)
     * Ads active in assessed week
     * Ads planned for decision week
   * If older entries in `decision_log.md` conflict with the format, do **not** imitate them—follow `decision_log_format.md`.
   * If you cannot determine the assessed week or decision week unambiguously, **stop** and ask for clarification before proceeding.

3. **Separate processing from output**
   
   * Put all thought processes and interim conclusions in the chat. Use a discursive, conversational format designed to give insight rather than support conclusions.
   * Actual output should go in canvases. These are specified in the **Required output** section below.
   * Keep processing and outputs separate.

4. **Creative uniqueness per week**
   
   * In a given week, the **same media, headline, or primary text may not appear in more than one ad of a campaign**

5. **New‑material constraint**
   
   * **At most one ad per week may contain new material** (new headline, new text, or new media).
   * Up to **two additional ads** may:
     * shuffle existing materials, or
     * reuse a previously run ad that is not currently active.

6. **Media provenance requirement**
   
   * Any existing media used must:
     
     * correspond to a **specific file in `attachments.tar`**, and
     * be referenced using its canonical name from `attachments_manifest.json`.

7. **Image–text semantic check (mandatory)**
   
   * Before proposing or finalizing any ad, verify that the **actual image content** (not just its tags or filename) matches the proposed headline and text.
   * If there is a mismatch, flag it and revise.

8. **Tag reuse discipline**
   
   * Before assigning hooks, promises, tone, or structure, review existing tag tables in `components_tags.csv`, including:
     
     * `Hook_types`
     * existing headline/text tag assignments
     * `Derived_Tag_Lifetime_Rollups`
   
   * New tags should be introduced **only if no existing tag fits**, and must be explicitly marked as new.

9. **Formatting requirements for new text**
   
   * New text must follow the agreed AIDA structure:
     
     * **A**: Attention → carried primarily by the image
     * **I**: Interest → headline + first line
     * **D**: Desire → exactly three bullet points
     * **A**: Action → explicit, low‑pressure CTA
   
   * Bullet points must be parallel in structure.
   
   * Emojis are allowed only if calm, neutral, and consistent.

10. **Cooling rules (mandatory)**
   
   * **Full‑ad cooling:** an ad cannot be reused unless it has been inactive for **at least 3 months**.
   * **Component cooling:** any component (media, headline, text) from a **replaced** ad cannot be reused for **1 week**.
   * Treat cooling rules as hard constraints; if they block a preferred option, choose the next‑best eligible alternative.

---

## Goals for this conversation

Work sequentially. Use chat for reasoning and interim decisions; place finalized outputs in canvases using the specification in **Required outputs**

1. **Assess** performance from the previous week
2. **Highlight new** or surprising information
3. Restate **current understanding** in light of new information
4. Make **keep decisions** based on previous week information
5. Make **change decisions** based on ad lifetime information and constraints
6. Generate a **decision‑log entry**
7. **Summarize** key points for the human decision‑maker

---

## Assess performance from the previous week

* Determine the latest completed week using `performance_data.json` and `decision_log.md`

* Identify ads with spend or leads in that week

* For each such ad, summarize:
  
  * weekly spend and CPL
  * run‑level spend and CPL
  * lifetime spend and CPL

* If more than four ads show activity:
  
  * Identify the four **intentionally run** ads using spend magnitude and the decision log
  * If intent is unclear or contradictory, **stop and ask for clarification**

---

## Highlight new or surprising information

* Compare results against:
  
  * previous weeks
  * prior decision rationales

* Label each notable event as:
  
  * *possibly noise*
  * *actionable observation*
  * *learning signal*

---

## Restate current understanding

Summarize what is currently known about:

* Ads
* Tags and tag combinations
* Headlines
* Texts
* Media
* Notable headline–text–media combinations

Each category of interest should be considered briefly, but if component‑level effects cannot be isolated, they may be
omitted to avoid being overly influenced by speculation.

This section is for context only.
Insights here may inform which winners to exploit or which probes to run, but must not justify diagnostic or interpretive choices unless explicitly allowed by the decision priority order.

---

## Make keep decisions

* Keep ads with **weekly CPL < 50**

* If an ad has no leads or if its CPL ≥ 50:
  
  * Check current run CPL and current run spend
    * Keep ads with current run CPL < 30
    * Keep ads with current run spend < 80

* Always keep **at least one ad**
  
  * If no ads meet keep criteria, make a judgement call: which is the ad most likely to succeed next week?

---

## Make change decisions

* All change decisions must be based on this strict priority order:
  1. Exploit historical winners:
     * Reuse ads, headlines or texts with strong historical evidence (low CPL at meaningful spend).
       * This is the default and preferred action
  2. Probe uncertainty
     * Prioritize components with low total spend and plausible fit that have not yet received sufficient delivery to rule out success
  3. Stabilize and interpret
     * Select components for interpretability and variance control
* Every non‑kept ad must be replaced
* Base change decisions on lifetime information only
  * Review tables of lifetime performance for ads and components and tags
  * Review summary of current understanding
  * For exploitation, use a **strict <50 CPL threshold** at meaningful spend.
* Apply the new‑material constraint strictly: maximum of one ad with new content.
  * If there is new material, check decision log
    * If last new material was text, use new media
    * If last new material was media, use new text
* Each change must be to one of the following (described in detail below):
  * Previously used ad
  * Reshuffled content
  * New text
  * New media
* Never allow any component to appear in more than one ad in a given week

### Previously used ad

* Only if the ad performed reasonably in the past
* And has not been used in at least 6 weeks

### Reshuffled content

* Choose one media, one headline, and one text that are likely to work together
* Do not use a combination that has been used before
  * Do not use any component that is used in another ad this week
* When combining components, there needs to be a balance between compatibility between components and selection of individual components
  * Select a single component with good exploitation if possible
    * Otherwise high uncertainty
    * Otherwise good interpretability
  * Match it with other components that are judged good fits (a requirement)
    * According to the priority: exploitation, uncertainty, interpretatability  

### New text

* Choose an existing media asset according to the priorities
  * Exploitation followed by uncertainty followed by interpretability
  * Never use media that is being used in another ad this week
* Create both new text and new headline to match it
* Ensure image–text alignment
* Specify hook, promise, tone, structure, and grammar using tags.
  * Review both tag taxonomy and tag list tables and actual tag use in performance_data.json before choosing.
  * Use existing tags if appropriate.
  * Expand tags list where it is appropriate but make sure to flag this and explain.

### New media

* Choose existing headline + text
  * Can be an existing combination or a new combination
    * Maximize exploitation followed by uncertainty followed by interpretability
      * Either of a single component or a previously used combination
    * Never use any component that is being used in another ad this week
* Suggest two existing media to use as inspiration
  * Can be media used with these headline and text or different existing media
* Explain how new media might differ from the inspiration
* Suggest tags for the new media to help convey the idea

---

## Required outputs (every week)

All outputs must be placed in a canvas and formatted in Markdown.

### 1) Performance summary

* Table of spend, leads, cpl and week over week detlas
* Explicit flags for low sample size or low delivery
* Summary of ke ypoints that are improtant, surprising or unexpected.

### 2) Summary of current situation

* Bullet points of key undersatndings to be used in planning and decisions
* Separate setions with key things for agent to remember and key things for human to notice

### 3) Key decisions

* Tables with one line per item
* Tables:
  * Ads to keep
  * Ads generated from existing materials
  * Ads generated with new material
* Make sure to specify tags and brief justificaiton
  * Although everything must fit on one reasonably sized line
* For new media specify
  * Inspiration media
  * Suggested variation
  * Suggested tag
  * 

### 4) Decision‑log entry
