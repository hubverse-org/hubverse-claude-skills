# hubverse conventions

Shared conventions for `hubverse-org` work. Import this file from a personal `CLAUDE.md` with one line:

```
@~/hubverse-claude-skills/conventions/hubverse.md
```

Personal preferences go in the importing file. Where a personal instruction conflicts with this file, the personal instruction wins.

## Code style

- R code follows the [tidyverse style guide](https://style.tidyverse.org) and the [tidyverse design principles](https://design.tidyverse.org). Where a repository's established conventions differ, follow the repository.
- [Make inputs explicit](https://design.tidyverse.org/inputs-explicit.html). Do not read environment variables or options inside a function body. Take them as arguments, with the read in the default: `path = Sys.getenv("GITHUB_STEP_SUMMARY")`. Note that top-level constants defined alongside the functions that use them are not hidden inputs.
- Where these conventions differ from the [posit-dev/skills](https://github.com/posit-dev/skills) R skills, these conventions take precedence.

## Hubverse index

`hubverse-org/hubverse-llm-index` indexes every org repository, documentation page and linked resource. Use it to find where something lives instead of searching the org. Read it from a local clone if there is one. Otherwise start from `https://raw.githubusercontent.com/hubverse-org/hubverse-llm-index/main/llms.txt`.

- `overview.md`: concepts, how the pieces fit, which repository does what.
- `llms.txt`: every repository, docs.hubverse.io and hubverse.io page, and each package site's own `llms.txt`.
- `catalog/repos.json`: per repository, the repo, issues, README, docs and `llms.txt` URLs.
- `local/clones.md`: which repositories are cloned locally, and where. It exists only in a local clone, is not committed, and is generated with `python3 scripts/local_clones.py <workspace>`, where `<workspace>` is the directory that holds the hubverse clones.

## Branching

- Branch off `main` (synced to remote first: `git fetch` / pull latest) by default, unless a different branching approach has been agreed for a given repo.
- Branch naming convention: `initials/description/issue_no` (e.g. `ak/enable-cloud-mirroring/7`). Do **not** use `feat/` / `fix/` style prefixes.

## Committing

- **Do not commit until the user has reviewed the work and said to commit.** Finishing an implementation, or the user approving a plan, is not approval to commit. Leave the changes in the working tree, say they are ready for review, and wait. Never bundle a `git commit` into a command that does something else the user asked for (a file fix, a test run): a commit stops being reviewable once it is made.

## Opening PRs and issues

- Before opening a PR in an R package, run these on the changed R files and fix what they report: `air format <files>`, `lintr::lint("<file>")` for each file, and the package tests (`devtools::test()`). hubverse packages carry `air.toml` and `.lintr`, so both tools pick up the repository's configuration.
- Always draft the full PR/issue **title and body first and show them to the user for review**. Only open (`gh pr create` / `gh issue create`) after the user confirms the actual text. Treat "open the PR/issue" as approval to proceed **once the user has seen the body**, not a licence to publish text they have not read. A PR/issue is outward-facing (visible to the team, tags people) and hard to walk back.
- A PR body has, in this order and only as far as the change warrants:
  - **What changed and why** (always). Open with a sentence on the problem being tackled, where there is one, and how the PR addresses it.
  - **How the pieces fit**, when the change adds or reshapes more than a couple of functions:
    - the object or entry point the change revolves around, and its shape;
    - a table of new functions, each with what it does and what uses it;
    - a table of existing functions whose role changed, with before and after;
    - a call tree showing how they connect;
    - a reading order.

    This maps the change, not the files. Describe mechanical changes repeated across files once, in the reading order.
  - **What to check**: the places where a reviewer has to exercise judgement, each with the question to answer, and any behaviour change and its consequences.
  - **Tests**: what they assert, and for a bug fix, that they fail on `main`.
  - **Out of scope**: links to filed issues, never prose to-do lists.

  Do not walk the diff file by file. The diff view does that. A trivial PR gets the first part only.
- **Inline comments on your own PR** give reviewers implementation context where it reads best next to the code: why a piece is shaped the way it is, how two changed pieces connect, or where to start reading. Unlike code comments, they may explain what changed and why. On a larger change, they let a reviewer skim the code and stop only where it matters. Use them sparingly, on the few places that carry the change, and do not repeat the PR body. Draft them with the PR body for the user to review, then post each with:
  ```sh
  gh api repos/{owner}/{repo}/pulls/{number}/comments \
    -f body='<comment>' -f commit_id=<head sha> -f path=<file> -F line=<line> -f side=RIGHT
  ```
- **Do not hard-wrap PR or issue bodies.** Write each paragraph as one long line and let GitHub wrap it. Manual line breaks at ~80 characters render as a narrow column that wastes vertical space and is harder to read, and they make later edits messy. This applies to the body prose only. Keep the line breaks that carry meaning in fenced code blocks, tables and lists.
- Express issue **relationships through GitHub's native links via the API**, not prose. Use **sub-issues** for a tracking/epic issue and its children, and **dependencies** for blockers. Do **not** write "sub-issue of #X", "part of #X", "depends on #Y", or a checklist of children into an issue body or comment. Do not replicate in text a relationship the API can hold, unless it is genuinely unavoidable (e.g. marking a duplicate, or the API rejecting a link). Both endpoints take the issue's **database id** (`gh api repos/{owner}/{repo}/issues/{number} --jq .id`), passed with `-F` so it is typed as an integer; both work cross-repo within the org.
  ```sh
  # add a sub-issue to an epic
  gh api -X POST repos/{owner}/{repo}/issues/{epic}/sub_issues -F sub_issue_id={child_id}
  # remove a sub-issue
  gh api -X DELETE repos/{owner}/{repo}/issues/{epic}/sub_issue -F sub_issue_id={child_id}
  # mark one issue as blocked by another
  gh api -X POST repos/{owner}/{repo}/issues/{blocked}/dependencies/blocked_by -F issue_id={blocker_id}
  ```

## Reviewing PRs

A human review spends its time where judgement matters most, and leaves line-by-line checking to an agent.

1. **Understand the change at a high level.** What problem does it solve or what feature does it add, what had to change to achieve that, and how do the pieces fit together. The PR body and the author's inline comments are the starting point.
2. **Review documentation with two hats on.** Spend the most time on user-facing documentation: roxygen docs, vignettes, NEWS entries, and error and warning messages. Read them as a user would, and check that what the user sees is clear and sensible (see NEWS / changelog entries). Then read developer-facing documentation, such as code comments and `@noRd` docs, as the next person to edit the code (see Comments and documentation).
3. **Leave detailed code review to an agent review**, for example Claude Code's `/code-review`. The reviewer still needs to understand what each piece of the change is and why it is there, even when they do not check it line by line. On larger changes, skim the code and read closely only where the author's inline comments point.

When asked to help with a review, write a reviewer's guide in the same order. Start with the change and how its pieces fit, as a PR body's "How the pieces fit" section does, and build it if the PR body lacks one. Then cover documentation, user-facing first, with the question the reviewer has to answer for each. Then code, separating what to read closely, with `file:line` references, from what to skim. End with the decisions the reviewer has to make.

## Responding to reviews

- **A reviewer's question is answered in the reply, or with a very concise note in the code. Never with paragraphs.** Add a detailed comment only when the review uncovered significant difficulty in understanding the code, not because a question was asked. Confusion about an internal function is best addressed with `@noRd` roxygen documentation on that function, not with block comments at the call site.

## Merging PRs

- Merge with a **merge commit** (`gh pr merge --merge`, GitHub's "Create a merge commit"), which lands as `Merge pull request #NN from ...`. Do **not** squash-merge (no `--squash`) and do not rebase-merge unless agreed for a specific repo.

## Project board

All transitions below use the "hubverse Development overview" project (org project #3): project id `PVT_kwDOBtSuRs4ARi5R`, Status field `PVTSSF_lADOBtSuRs4ARi5RzgLNCAE`. `$item` is the project item id, as returned by `gh project item-add` or found via `gh project item-list 3 --owner hubverse-org`.

| Status | Option id |
|---|---|
| Todo | `f75ad846` |
| In Progress | `47fc9ee4` |
| Ready for Review | `3bd9ef5a` |
| Reviewed/Awaiting Changes | `0bf178f5` |
| Changes Made / Awaiting approval | `6e95b446` |
| Reviewed/Ready to Merge | `d291820a` |

```sh
gh project item-edit \
  --project-id PVT_kwDOBtSuRs4ARi5R \
  --id "$item" \
  --field-id PVTSSF_lADOBtSuRs4ARi5RzgLNCAE \
  --single-select-option-id <option-id>
```

- **Issue opened** in a `hubverse-org` repo: add it to the project with Status = **Todo**. Do this for every issue created there, without being asked.
  ```sh
  item=$(gh project item-add 3 --owner hubverse-org --url <issue-url> --format json --jq '.id')
  ```
- **Work starts** (branch created, implementation begun, or the user says they are picking it up): move the issue's card to **In Progress** and assign the issue to the person doing the work. Do this **at branch creation, before opening a PR**.
  ```sh
  gh issue edit <issue-url> --add-assignee @me
  ```
- **PR opened with a linked issue** (e.g. body says "Resolves #46"): GitHub **automatically** moves the issue's card to **Ready for Review**. Do not set it, do not override it back to In Progress, and do not add the PR to the project separately.
- **PR opened with no linked issue**: add the PR itself to the project with Status = **Ready for Review**.
- **Review submitted** on someone else's PR: if it requests changes, move the card to **Reviewed/Awaiting Changes**. If it approves, move the card to **Reviewed/Ready to Merge**. A review with comments only leaves the card where it is. The card is the linked issue's, or the PR's own when no issue is linked.
- **Review answered** (responses posted or changes pushed addressing the reviewer's comments): move the card for the linked issue/PR to **Changes Made / Awaiting approval**.

## NEWS / changelog entries

- `NEWS.md` entries are **user-facing**: describe the change in terms of what a user observes.
  - **Include** observable behaviour and output: corrected values, what now appears in output files (including columns that appear/disappear or change name, and any conditions under which the output shape differs), changed errors/warnings. If a fix changes the output in some cases, say so. That is exactly what a user needs to know.
  - **Exclude** implementation mechanics: internal or upstream functions and their arguments, refactors, internal data-flow, and which upstream PR/version supplies something (e.g. do not write "the count now comes from `otherpkg::fn(flag = TRUE)`"). That belongs in the code and the PR, not NEWS.
  - **Rewording an error or warning is not an entry.** "Changed errors/warnings" above means a *changed condition*: a message a user now gets where they did not before, or no longer gets where they did. If the same input still fails in the same situation and only the prose is clearer, nothing changed for the user. The commit carries it; NEWS does not.
  - Keep it to the shortest clear statement, but do not drop a user-visible output change to make it shorter.

## Comments and documentation

Comments and docs are read by people who did not write the code, including colleagues who do not speak English as a first language. Write for them.

Clear and concise, but also **professional**: this is software documentation, and it should read like the reference docs and source comments of a well maintained package. Plain does not mean chatty or breezy. No jokes, no filler, no addressing the reader as "you" where a statement about the code will do, no rhetorical questions, no exclamation marks. Prefer the vocabulary a developer would expect to see over an everyday paraphrase of it, but only where that vocabulary is the accurate word rather than decoration.

- **One idea per sentence.** Do not stack subordinate clauses.
- **Explain a chain as a chain.** When several facts have to connect before a consequence makes sense, give each its own sentence and keep them in order: the situation, then the mechanism, then what follows. Do not open with the mechanism and assert the outcome, leaving the reader to reconstruct the middle. Put the fact the code actually depends on last, where it lands hardest.
- **Mark asides with "Note".** A comment often carries two registers: what a reader must know to use or change the code, and a detail that explains an obscure corner. Lead with the fundamental part, unqualified, and open the aside with "Note that" so the reader can see at a glance which is which and skip it if they do not need it. Do not open the main point with "Note", or the signal stops meaning anything.
- **Concrete over abstract.** Name the thing. "Leave out derived task IDs" beats "a derived value cannot separate rows the others leave together".
- **Watch pronouns.** If "it", "they" or "them" could point at more than one thing in the sentence, repeat the noun instead.
- **Say why, not what.** The code already says what it does. A comment earns its place by giving a reason, a constraint, or a consequence that is not visible from the code. Identify the feature of the code being explained, then say as concisely as possible why it is that way.
- **Do not narrate the refactor.** A comment describes the code as it is now, not what it replaced, what it used to do, or what was tried. Describe current behaviour only where it might confuse a reader and needs additional context. Context about the change itself belongs in the PR body or an inline PR comment.
- **Account for the whole line.** A comment that describes only part of what the code below it does is wrong, not merely incomplete.
- **Do not explain what the reader already knows.** Standard R, common package functions, general programming ideas. Do not justify a choice nobody would question.
- **Name another function only if the reader has to act on it.** Not for colour, not for history. If two functions must be changed together, say that plainly and say which.
- **A title is a title.** `@title` names what the function is or returns. It is not a sentence about how it works.
- **Verbs must match the name.** Do not say a function "summarises" when it builds a table. Say what it produces and what uses it.
- **Keep comment lines under 80 characters.** `air` does not reflow comments and `.lintr` allows 120, so nothing else will catch this.
- **A documentation pass covers every changed file**, not a sample of them.

Worked example of the chain rule. Opens with the mechanism and asserts the outcome, so the reader has to work out for themselves why both sides hold `NA`:

> `%in%` matches `NA` to `NA`, as the grid join this replaced did. That is how a task ID a modeling task does not use passes: the config allows it only `NA`, and the submitted rows hold `NA` there too.

As a chain, marked as an aside, situation first and the load-bearing fact last:

> Note that a modeling task that does not use a task ID either lists it as null in the config or leaves it out, and config processing turns the expected value of both situations into `NA`. Correctly submitted model output carries `NA` in that column too. `%in%` matches `NA` to `NA`, unlike `==`, so those rows match.

Shorter is usually right. If a rewrite makes a comment longer, re-read it rather than continuing. A comment rewritten more than twice is usually one that should not exist.

## Testing (R)

- Before using `testthat::local_mocked_bindings()` (or `with_mocked_bindings()`), read its docs / `vignette("mocking", package = "testthat")`. Do **not** reach for `.package = "otherpkg"` to mock a dependency called via `otherpkg::fun()`. The docs discourage it (it modifies a namespace we don't own and affects all callers). Instead import the function (`@importFrom otherpkg fun`), call it unqualified, and mock it in our own namespace with no `.package`.
