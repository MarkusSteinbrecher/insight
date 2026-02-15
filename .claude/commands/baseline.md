# /baseline <topic>

Establish a common-knowledge baseline for a topic, then evaluate each canonical claim against it. This surfaces which claims are already widely known versus genuinely novel.

## Arguments

$ARGUMENTS — The topic slug (e.g., "EA for AI")

## Modes

This command has three modes, selected based on the current state of baseline files:

1. **Create baseline** — If `baseline.md` does not exist, create it via web search
2. **Evaluate claims** — If `baseline.md` exists but `baseline-evaluation.yaml` does not, evaluate claims
3. **Review evaluations** — If `baseline-evaluation.yaml` exists, review and adjust

## Mode 1: Create Baseline

1. Check if `knowledge-base/topics/{topic}/baseline.md` exists
2. If not, ask the user for a search question using AskUserQuestion:
   - "What question should we search to establish the common knowledge baseline?"
   - Suggest a default based on the topic title (e.g., "How does Enterprise Architecture change because of AI?")
3. Run the baseline search script:
   ```bash
   python3 scripts/baseline-search.py "{topic}" "{question}"
   ```
4. Read the generated `baseline.md` and present a summary:
   - Number of search results found
   - Key themes that appeared across results
   - Note that the user can edit `baseline.md` manually to add or refine content
5. Ask the user: "Ready to evaluate claims against this baseline, or do you want to review/edit baseline.md first?"

## Mode 2: Evaluate Claims

1. Read `knowledge-base/topics/{topic}/baseline.md`
2. Read `knowledge-base/topics/{topic}/extractions/claim-alignment.yaml` (canonical claims)
3. Read all `knowledge-base/topics/{topic}/extractions/critical-analysis-part*.yaml` (bottom_line for each claim)
4. For each canonical claim, evaluate against the baseline using these categories:

   - **common**: The claim's core point is well-represented in baseline search results. A practitioner Googling the topic would find this.
   - **additional**: The claim relates to baseline topics but adds specific detail, a new angle, quantitative data, or practitioner-specific guidance not in the baseline.
   - **new**: The claim addresses something not present in the baseline — a genuinely novel observation or connection.

5. Process claims in batches of 20-30 to maintain evaluation quality. For each batch:
   - Present the baseline content as context
   - Evaluate each claim's statement and bottom_line against the baseline
   - Assign a category and write a one-sentence rationale

6. Write evaluations to `knowledge-base/topics/{topic}/extractions/baseline-evaluation.yaml`:

   ```yaml
   meta:
     baseline_question: "How does Enterprise Architecture change because of AI?"
     baseline_created: 2026-02-15
     evaluated: 2026-02-15
     total_claims: 136
     common: 45
     additional: 62
     new: 29

   evaluations:
     - id: cc-001
       category: common
       rationale: "Multiple baseline sources discuss the need for new architecture designs for GenAI."
     - id: cc-002
       category: additional
       rationale: "Baseline mentions reference architectures generally but not the multi-layer pattern."
   ```

7. After all batches are complete, present a summary:
   ```
   Baseline evaluation complete:
     Common:     45 (33%) — already widely known
     Additional: 62 (46%) — adds detail or angle
     New:        29 (21%) — genuinely novel
   ```

## Mode 3: Review Evaluations

1. Read `knowledge-base/topics/{topic}/extractions/baseline-evaluation.yaml`
2. Read critical analysis files for bottom_line text
3. Present claims grouped by category, starting with **new** (most interesting), then **additional**, then **common**
4. For each group, show:
   - Total count and percentage
   - Each claim: ID, bottom_line, and evaluation rationale
5. Ask the user using AskUserQuestion: "Would you like to reclassify any claims?"
   - If yes, ask which claims and what their new category should be
   - Update the YAML file with changes and recalculate the meta counts
6. Present the final summary after any changes

## Evaluation Guidelines

When evaluating claims against the baseline:

- **Be generous with "common"**: If someone searching this topic would encounter the core idea within the first page of results, it's common — even if the specific framing differs.
- **"Additional" is the middle ground**: The topic area appears in the baseline, but the specific claim adds meaningful detail — concrete numbers, specific frameworks, practitioner-oriented guidance, or a non-obvious angle.
- **"New" should be genuinely surprising**: A practitioner familiar with the baseline content would not have encountered this claim or connection. Reserve this for claims that represent original analysis, unexpected contradictions, or novel synthesis across sources.
- **Evaluate the claim, not the wording**: Two differently-worded claims about the same core idea should get the same category.

## Important Notes

- The baseline is a snapshot of easily-accessible common knowledge, not a comprehensive literature review
- The user can edit `baseline.md` manually before evaluation — they may want to add context from their own experience
- Evaluation should be conservative: when in doubt between "additional" and "new", prefer "additional"
- This step does not change the claims themselves — it adds metadata for downstream use

## Example

```
/baseline EA for AI
```

If no baseline exists, prompts for a search question and creates one. If baseline exists but claims haven't been evaluated, runs the evaluation. If evaluations exist, enters review mode.
