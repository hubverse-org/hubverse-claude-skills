---
name: pre-review
description: Verify a change before asking the team to review it. Runs the checks that apply to the change, then three independent reviews by fresh agents (correctness, parsimony, cold reader), and reports the evidence for the PR body. Use before saying work is ready for review, before drafting a PR body, and on each PR of a stack.
argument-hint: "[base ref or PR number] [related PR numbers...]"
---

Verify the change in the current repository before it goes to human review. Human reviewers spend their time on judgement. They should not be the first to find a bug, a missed path or an unclear paragraph.

Arguments: $ARGUMENTS. The first is the base ref or the PR number. Default to the merge base with `origin/main`. Any further numbers are related or stacked PRs.

## 1. Gather the inputs

- The diff against the base, and the list of changed files.
- The issue or issues the change resolves, read in full with their comments. Read the parent issue and any poster they cite.
- Related and stacked PRs, with their bodies and diffs.
- The PR body draft. Write it to a file in the scratchpad if it exists only in the conversation.
- If the PR is open, its CI runs: `gh pr checks <n>`, then `gh run view <run-id> --log` for each run. Read the logs of passing jobs too. A job can pass while logging an error from code the change touches.

## 2. Run the checks that apply

Decide which of these apply from the diff, the issue and the PR body. For each one that applies, do it and record the evidence. For each one that does not apply, say why in one line.

1. **Claims of coverage.** List every input, path and environment the change or its PR body claims to handle. Examples are "every hub", "each schema version", direct calls as well as calls through `validate_model_data()`, the `error = FALSE` path that the real caller uses, `workflow_dispatch` runs and checkouts from a fork. Confirm that a test or a recorded run exercises each one. Run or test the missing ones, or narrow the claim.
2. **New or changed arguments of exported functions.** Test each argument omitted, passed as an explicit `NULL`, combined with each alternative argument, and malformed (wrong class, mismatched with the other inputs, missing a required column). Confirm that every skip and early return in the function is still reached.
3. **Stricter behaviour.** When the change can reject input that passed before, run the new rule against real hub data and report how many files fail, by hub. This applies to bug fixes too, such as starting to enforce a rule the config always declared: the data may already break it. Name the producer of each failing file, such as a team or a hub workflow, so it can be fixed before the release. Use local clones (see `local/clones.md` in the hubverse index), shallow sparse clones of `model-output/` and `hub-config/`, or a hub's public S3 mirror for large hubs. Cite any existing survey, such as one in a poster, in the PR body.
4. **Dependencies on other repositories.** For each change in another repository that this one needs, check whether it is released, not just merged. Say what a consumer that tracks `@main` or the latest release gets in the meantime, and state the merge and release order in the PR body.
5. **Claims of speed.** When the PR claims a speedup, benchmark every path whose cost changes: direct calls of each changed exported function, files that fail early, and inputs the change skips. When the PR combines more than one optimisation, measure each one on its own. Define every benchmark label used in the PR body.
   - **Vary what the cost depends on.** Read the old and new code and name what each one's cost grows with, which may not be file size. For example, compound task ID set detection grew with the number of samples, not the number of rows, and a benchmark file with few, long samples hid a slowdown of 30 s at 100,000 samples. Measure across that quantity, with a small script if the repository's benchmark holds it fixed, and file an issue to add it as a benchmark axis.
   - **Attribute each benefit to the part that delivers it.** When the change has separable parts, such as building a shared object and rewriting code that reads it, state what each part buys on its own. A rewrite of working code needs its own measured reason.
6. **Test rewrites.** Pair every removed snapshot or assertion with its replacement and record a verdict for each, as the conventions require.
7. **The same fault elsewhere.** For each bug fixed, search the whole package, and its siblings in the org where relevant, for the same pattern. Fix it, or file an issue and link it.
8. **User-facing additions.** Check that `NEWS.md` covers each user-visible change. Check that new exported functions link related ones with `@seealso`, and that related functions link back.
9. **Notification.** Decide whether hub administrators, modelers or maintainers of downstream tools need to hear about the change before or at release. They do when the change makes files fail that passed before, changes what an output or file contains, or needs anyone to act. A scan of some hubs does not cover every hub, so a change that can fail files anywhere needs an announcement even when the scan found no failures. If it does, draft an entry for the Announcements category of the org Discussions (https://github.com/orgs/hubverse-org/discussions) with a "What you need to do" row for each audience, and a short email for the mailing list (https://groups.io/g/hubverse) that links to it. Say in the PR body that the change needs announcing.
10. **Repository history.** For each line the change removes or loosens, such as a version pin, a guard or a skipped test, read its `git log -L` or `git blame` to find why it was added. Keep it unless that reason no longer holds.

## 3. Run three independent reviews

Spawn three agents in parallel with the Agent tool. Give each one only the inputs from step 1 and the path to `conventions/hubverse.md` in this repository. Do not give them the reasoning behind the design, the alternatives that were rejected, or your own view of the change. A reviewer that knows why each choice was made tends to accept it.

**Correctness.**

> Review the change in `<repo>` against `<base>` for correctness. The issue it resolves is `<issue>`, and the related PRs are `<PRs>`. Find bugs that a real caller or a real hub would hit. Try caller-shaped inputs: an argument forwarded as an explicit `NULL`, both or neither of a pair of alternative arguments, an object built from a different table or round, and a missing column. Check every skip and early-return path, every error path, and what the user sees when an internal step fails. Check that information reported in more than one place, such as a message and a table, agrees. Look for the same fault in code the change did not touch. Run code to confirm a finding wherever you can, and say which findings you ran and which come from reading. Report each finding with `file:line`, the input that triggers it, and the wrong result.

**Parsimony.**

> Read issue `<issue>`, then the change in `<repo>` against `<base>`, and the related PRs `<PRs>`. Decide whether this is the smallest change that resolves the issue. Search the repository and the hubverse org for functions, options or mechanisms that already do part of the job. The hubverse index lists every repository (`<index path>`). Identify parts of the change that the issue does not need, parts that could be a separate PR, and claims of benefit that the PR does not measure. For each part that rewrites working code, say what the rewrite buys that the rest of the change does not already deliver, and whether the PR shows it. Flag helpers that add indirection without being reused, as well as duplicated blocks. For each finding, say what the simpler option is and what it would cost to adopt it.

**Cold reader.**

> You are a hubverse team member who has not followed this work. Read the PR body `<path>`, then the user-facing documentation the change adds or edits (roxygen, vignettes, NEWS, error and warning messages), then the code comments. List:
> - every term that is used before it is defined, including benchmark labels and shorthand for functions;
> - every hubverse term used differently from how docs.hubverse.io defines it, for example calling a task ID "compound" when the compound task ID set is what the docs define;
> - every passage you had to read twice, with what you understood it to mean;
> - every rule or behaviour explained in the abstract, with no realistic example from an actual hub;
> - every passage longer than it needs to be, and what it would say in one or two sentences;
> - every claim that the PR body does not back with evidence.
> Quote the passage for each finding. Rank the findings by how much each one would slow a reviewer down, and report at most the top 10.

## 4. Triage

- Reproduce each finding before acting on it. Some findings are wrong. Record why a finding was rejected.
- Fix the bugs and the cheap cleanups. For each fix, sweep the whole change for the same pattern.
- List refactors and redesigns as optional, each with what it would cost. Do not do them unasked.
- Raise any finding that changes the design with the user before changing the code.

## 5. Report

Report to the user:

- A table of each check in step 2 and each review in step 3, with what it found, what was fixed and what was rejected.
- The evidence to carry into the PR body: coverage of the claims, the real-hub results, the release order and the benchmarks, each in one or two lines.
- The optional refactors, with their costs.

Do not say the work is ready for review until the user has seen this report.
