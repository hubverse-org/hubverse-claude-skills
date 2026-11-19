---
name: respond-to-review
description: Answer review comments on a PR you authored. Triages each comment (valid, misreading, question, out of scope), fixes the work, re-reads the rewritten parts with a fresh agent, and drafts the replies, inline where an answer belongs to one line and in the main reply for wider changes. Use when your PR has new review comments to address.
argument-hint: "[PR number]"
---

Answer the reviews on your own PR. The judgement is yours and the user's. This skill covers the steps around it, which are the ones that get missed.

The conventions on writing replies are in the "Responding to reviews" section of `conventions/hubverse.md`. The board transitions are in its "Project board" section.

Show the user each result once. Later steps report only what is new, and refer to earlier results by comment rather than repeating them. A request for input lists only the comments that need a decision.

## 1. Gather

- Every review, inline thread and conversation comment, with the replies already posted:
  ```sh
  gh api repos/{owner}/{repo}/pulls/{n}/reviews
  gh api repos/{owner}/{repo}/pulls/{n}/comments --paginate   # inline, with in_reply_to_id
  gh api repos/{owner}/{repo}/issues/{n}/comments
  ```
- The commit each review saw (`commit_id`) against the current head. A comment on an older commit may already be addressed.
- The PR body, the linked issue, and every earlier reply by the author on the PR. A fix can contradict something already posted.

## 2. Triage

Give each comment one verdict. Before changing anything, present the verdicts in a single table (reviewer, `file:line`, the point, verdict, action), which is also the request for the user's confirmation:

| Verdict | Action |
|---|---|
| Valid | Fix it. |
| Misreading | Treat it as a clarity bug. Fix the text, and explain the intended meaning in the reply. |
| Question | Answer it in the reply. Change the work only if the answer shows a gap. |
| Out of scope | Say so in the reply, and file an issue if there is work to do. |

Judge each comment against the work as its reader meets it, for example the rendered page for documentation, not against what the author knows. State each verdict plainly, including when the reviewer is right.

The user confirms the verdicts before any fix is made. Raise a fix that changes the design with the user first.

## 3. Fix

- Make the fixes. For each one, sweep the whole change for the same pattern, not only the passage the comment cites.
- Search the earlier replies, the PR body and the linked issue for statements the fix makes wrong. Correct them in the reply, and update the PR body.
- For documentation, check the result rendered, in both light and dark themes where styling changed.

## 4. Re-read

Run one fresh cold-reader agent on the rewritten passages only, with the cold-reader prompt from the `pre-review` skill. Run the full `pre-review` only when the fixes were large.

## 5. Draft the replies

- Answer each comment where it reads best. A fix to one passage gets an inline reply on its thread. A change that spans several comments or alters the approach is described in the main reply.
- One main reply in the PR conversation. When most answers are inline, it is a short high-level summary. It corrects any earlier statement the fix contradicts.
- For documentation, link the rendered preview, anchored to each changed section, when the change has significant visual components, such as diagrams or styled tables. Text and simple tables read well enough in the diff.
- Show the drafts to the user without restating the triage. Post only after approval, and post exactly what the approved draft says.

## 6. Post

- Push first, so the reply describes what the reviewer will see. When the reply links the preview, wait for the preview build to pass and check that it includes the latest commit.
- Post the replies.
- Move the card to **Changes Made / Awaiting approval**.
- Leave resolving threads to the user.
