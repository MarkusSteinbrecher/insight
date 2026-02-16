# /analyze <topic>

Run the Phase 1 data analysis pipeline for a topic — raw segmentation, claim alignment, critical analysis, and cross-source comparison.

## Arguments

$ARGUMENTS — The topic slug to analyze (e.g., "ai-agents-enterprise")

## Prerequisites

The topic must exist at `knowledge-base/topics/{topic}/` with sources in the `sources/` directory. Run `/research <topic>` first if needed.

## Process

### 1. Check progress and determine next step

- Read `_index.md` to get `phase`, `completed_steps`, and `current_step`
- Determine which step to run next based on what's already completed:
  - No completed Phase 1 steps → start at **Step 1.1**
  - `"1.1"` completed → run **Step 1.2**
  - `"1.2"` completed → run **Step 1.3**
  - `"1.3"` completed → run **Step 1.4**
  - `"1.4"` completed → Phase 1 is done, inform user
- Tell the user which step will run and ask for confirmation before proceeding

### 2. Run the next incomplete step

---

#### Step 1.1 — Raw Segmentation

Break each source into numbered segments, classify each segment by type, and calculate composition statistics.

**Input**: All source files in `sources/` that don't yet have a corresponding `raw/source-NNN-raw.yaml` file.

**Process** (per source):
1. Read the source note
2. Split content into segments following the segmentation rules in CLAUDE.md (one segment per sentence, bullet, heading, etc.)
3. Classify each segment using the 10-type taxonomy (claim, statistic, evidence, definition, recommendation, context, methodology, example, attribution, noise)
4. Calculate composition breakdown and signal ratio
5. Write `raw/source-NNN-raw.yaml` following the Raw File Format schema in CLAUDE.md

**Token management**: Process sources one at a time. After each source, write the raw file immediately. Do not accumulate multiple sources in context.

**On completion**: Update `_index.md` — add `"1.1"` to `completed_steps`, set `current_step: "1.2"`, set `phase: 1` if not already. Run `python3 scripts/build-overview.py` to update source pipeline status.

---

#### Step 1.2 — Cross-Source Claim Alignment

Deduplicate claims across all raw files. Identify consensus positions, unique claims, and contradictions.

**Input**: All `raw/source-NNN-raw.yaml` files.

**Process**:
1. Extract only `claim`-type and `recommendation`-type segments from all raw files (skip noise, context, headings, etc.)
2. Group similar claims by theme — look for claims making the same core point across different sources
3. For each theme with 2+ sources agreeing, create a canonical claim (`cc-NNN`) with:
   - Theme label, summary statement
   - Source segments with segment IDs and representative quotes
   - Strength (strongly-supported / supported)
   - Claim type (normative / empirical / predictive / definitional)
4. For claims held by only one source, create unique claims (`uc-NNN`)
5. Where sources disagree, create contradictions (`ct-NNN`) with each source's position
6. Write `extractions/claim-alignment.yaml` following the Claim Alignment Schema in CLAUDE.md

**Token management**: If there are more than 30 sources, process in batches of 15-20 sources at a time. Write intermediate results and merge.

**On completion**: Update `_index.md` — add `"1.2"` to `completed_steps`, set `current_step: "1.3"`.

---

#### Step 1.3 — Critical Analysis

Assess each canonical claim from the claim alignment with critique, practical value, action steps, and bottom line.

**Input**: `extractions/claim-alignment.yaml`

**Process**:
1. Read the claim alignment file
2. For each canonical claim, assess:
   - **critique**: What's strong, what's missing, what would make it stronger (following Writing Guidelines — objective, no snark)
   - **practical_value**: What a practitioner can do with this
   - **action_steps**: 2-3 concrete actions
   - **bottom_line**: One-sentence assessment
3. Write `extractions/critical-analysis.yaml`

**Token management**: Process claims in batches of 15-20. Write the full file after all batches are complete. If you are approaching output limits, write what you have and note the last completed claim ID — the user can re-run `/analyze` to continue.

**On completion**: Update `_index.md` — add `"1.3"` to `completed_steps`, set `current_step: "1.4"`.

---

#### Step 1.4 — Cross-Source Comparison

Generate a narrative comparison across all sources, organized by theme.

**Input**: `extractions/claim-alignment.yaml`, `extractions/critical-analysis.yaml`

**Process**:
1. Organize themes from the claim alignment into logical sections
2. For each theme section, write a narrative comparison:
   - What sources agree on
   - Where they diverge
   - What's missing from the discussion
   - Quality and strength of evidence
3. Write `extractions/cross-source-analysis.md`

**On completion**: Update `_index.md` — add `"1.4"` to `completed_steps`, set `current_step: "2.1"`. Set `phase: 1` status as complete.

### 3. Present results and suggest next steps

After completing a step, present:
- Summary of what was produced
- Key statistics (segment counts, claim counts, etc.)
- Any issues encountered

Suggest the next action:
- After 1.1: "Run `/analyze {topic}` again to proceed to claim alignment (step 1.2)."
- After 1.2: "Run `/analyze {topic}` again to proceed to critical analysis (step 1.3)."
- After 1.3: "Run `/analyze {topic}` again to proceed to cross-source comparison (step 1.4)."
- After 1.4: "Phase 1 complete. Run `/baseline {topic}` to evaluate claim novelty, or `/discuss {topic}` to begin insight refinement."

## Example

```
/analyze ai-agents-enterprise
```

Checks progress, runs the next Phase 1 step, and presents results.
