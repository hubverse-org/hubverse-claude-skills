---
name: hubverse-release
description: Release a hubverse R package following the hubverse release checklist
disable-model-invocation: true
argument-hint: "[major|minor|patch]"
---

Release the R package in the current repository following the hubverse release checklist.

If a bump level was provided as an argument, use it: $ARGUMENTS
If no argument was provided, you will determine the bump level in the setup phase below.
Valid bump levels are: major, minor, patch.

## Setup — gather context before doing anything

1. **Check out main and pull latest**: Run `git checkout main && git pull` to ensure you are working from the latest state of the main branch.

2. **Identify the package** by reading `DESCRIPTION` in the repo root. Extract the package name and current version (ignoring any `.9000` dev suffix).

3. **Determine the bump level** (if not provided as an argument):
   - Read `NEWS.md` and review the changes listed under the development heading.
   - Based on the nature of the changes, suggest a bump level:
     - **patch**: bug fixes, minor documentation updates
     - **minor**: new features, non-breaking enhancements
     - **major**: breaking changes
   - Show the user the current version, your suggested bump level, and what the resulting version number would be.
   - The user can accept your suggestion or provide a different bump level.
   - The confirmed bump level is referred to as `$BUMP_LEVEL` in the steps below.

4. **Calculate the target version** from the current version and confirmed `$BUMP_LEVEL` using semver arithmetic (e.g. 0.1.0 + minor = 0.2.0). This is `$VERSION` in the steps below.

5. **Detect author initials**: Try to find the user's branch naming initials by scanning branch names from their commits: `git log --author="$(git config user.email)" --all --format=%D`. Look for branch name patterns like `xx/something/...` and extract the initials prefix. If initials are found, ask the user to confirm them (e.g. "I found `xx` from your recent branches, use these? Or provide different initials:"). If no initials are found, ask the user to provide their initials.

6. **Check if the package is on CRAN** (e.g. check for `cran-comments.md` in the repo, or query CRAN). If the package is on CRAN, ask the user whether they also want to prepare a CRAN submission for this release. The user can say no, in which case skip all CRAN steps entirely. If the package is not on CRAN, skip all CRAN steps without asking.

## Phase 1 — Prepare the release branch

7. **Create release branch** named `<initials>/release/$VERSION` from `main`.

8. **Update version** by running in R:
   ```r
   usethis::use_version("$BUMP_LEVEL")
   ```
   Then verify the `Remotes:` field in `DESCRIPTION` is current.

9. **Update NEWS.md**: Proofread the existing development section. Ensure it has a heading for this version and that entries are accurate and complete. Ask the user to review.

10. **Update contributors**: Check recent git history for new contributors and ensure they appear in `DESCRIPTION` if appropriate.

11. **Commit and push** the release branch.

12. **Create a PR** to `main`. Title: `Release <package name> $VERSION`. In the body, include a summary of changes from NEWS.md. Do NOT include a "Test plan" section in release or post-release PRs — they're version bumps, not feature work, and CI covers the checks.

## Phase 1a — CRAN submission prep (only if user opted in during setup)

If the user opted in to preparing a CRAN submission, perform these steps BEFORE requesting review. The reviewer should see the final submission-ready state of the package. IMPORTANT: Never actually run `devtools::release()` or submit to CRAN — only prepare the submission and show the user the command to run manually.

13. Run `devtools::check(remote = TRUE, manual = TRUE)` locally.

14. Run `devtools::check_win_devel()` for Windows checks.

15. Document check results in `cran-comments.md` (create with `usethis::use_cran_comments()` if needed).

16. Commit the updated `cran-comments.md` and push to the release branch.

## Phase 2 — Review

17. **Pause**: Tell the user to get the PR reviewed by another Hubverse developer. The reviewer should be signing off on the final state of the package (including CRAN prep if applicable). Remind the user to invoke `/hubverse-release` again (or resume the conversation) to continue after approval.

## Phase 2a — CRAN submission (only if user opted in during setup)

After the PR is approved, but BEFORE merging, the user submits to CRAN. Do NOT merge or tag until CRAN has accepted the package.

18. Temporarily remove the `Remotes` field (do NOT commit):
    ```r
    desc::desc()$del("Remotes")$write()
    ```

19. **Show the user the manual submission command** and tell them to run it themselves:
    ```r
    devtools::release()
    ```
    Then **pause** and wait for the user to confirm they have submitted.

20. **After user confirms submission**, pick back up and:
    - Restore DESCRIPTION: run `git restore DESCRIPTION`. This brings the `Remotes:` field back by restoring DESCRIPTION from HEAD, which works because the removal in step 18 was never committed.
    - Commit the `CRAN_SUBMISSION` file and push

21. **If the user reports a CRAN rejection**:
    - Update `cran-comments.md` with the rejection feedback
    - Bump patch version with `usethis::use_version("patch")`
    - Re-prepare the submission (repeat steps 13-16)
    - Re-request review on the PR
    - Once re-approved, retry submission (repeat steps 18-20)

22. **Pause**: Tell the user to wait for the email confirming the package is on its way to CRAN before proceeding.

## Phase 3 — Merge, tag, and release (only after PR approval and, if CRAN, acceptance)

IMPORTANT: Confirm with the user that the PR is approved (and, if a CRAN release, that CRAN has accepted the package) before proceeding.

23. **Create a signed tag**:
    ```
    git tag -s v$VERSION -m '<short summary of changes>'
    ```
    Ask the user to confirm the tag message before creating it.

24. **Push the tag**: `git push --tags` — confirm with the user before running.

25. **Create GitHub release** by running in R:
    ```r
    usethis::use_github_release()
    ```

## Phase 4 — Post-release

26. **Create post-release branch** named `post-release-$VERSION` from `main`.

27. **Set development version** by running in R:
    ```r
    usethis::use_dev_version()
    ```
    This appends `.9000` to the version and adds a development heading to `NEWS.md`.

28. **Commit, push, and create a PR** for the post-release bump. Merge on approval.

29. **Clean up local branches**: After the post-release PR is merged, run `git fetch --prune` and then identify local branches whose remote tracking branch no longer exists (i.e. `git branch -vv` entries marked `[gone]`). NEVER include `main` or `master` in the deletion list. List the branches to the user and ask for confirmation before deleting them with `git branch -D`.

## Important notes

- Do NOT add `Co-Authored-By` lines to commits created by this skill.
- Pause for user confirmation before any destructive or hard-to-reverse action (tagging, pushing tags, creating releases).
- When asking the user to confirm something (e.g. bump level, tag message, pushing tags), use the `AskUserQuestion` tool with `"yes"` as the first option in `options` so the user can just press Enter to accept.
- Never run `devtools::release()` or submit to CRAN directly. Only prepare and show the user the command.
- Run R commands via `Rscript -e '...'` in the shell.
- If any step fails, stop and discuss with the user rather than retrying blindly.

## Slack review messages

After creating each PR, compose a short Slack review request message in Slack markdown and copy it to the clipboard. The tone should be casual and friendly. Examples:

- Release PR: "Hi all! Can I get a quick rubber stamp review on the PR to release <package> v$VERSION? <PR URL>"
- Post-release PR: "Any chance I can get another rubber stamp PR to bump to dev version? <PR URL>"

Pick a clipboard tool based on what's available on the user's system. Try in this order and use the first one that exists:

1. macOS: `pbcopy`
2. Linux (Wayland): `wl-copy`
3. Linux (X11): `xclip -selection clipboard` or `xsel --clipboard --input`
4. Windows / WSL: `clip.exe`

If none are available, print the message in the chat instead and tell the user to copy it manually. Do not install a clipboard tool.
