---
name: dashboard-smoke-test
description: >
  Create smoke-test branches across dashboard tool repos for testing
  skills like /dashboard-local-build with dev versions. Sets up branches,
  pauses for manual testing, then verifies and cleans up.
allowed-tools: [Bash, Read, Glob, Grep, AskUserQuestion]
---

# Dashboard Smoke Test

General-purpose test harness for dashboard skills. Creates `smoke-test` branches across tool repos so the user can test a skill with dev versions, then cleans up.

**Use `AskUserQuestion` at every decision point.**

**Safety rules:**
- **Never modify any files** in any repo. This skill only creates/deletes git branches and empty commits via Bash.
- **Check for uncommitted changes** before switching branches. If there are uncommitted changes, warn the user and ask whether to stash, proceed, or abort.
- The branch name `smoke-test` is **fixed** and cannot be changed.
- Cleanup always switches repos back to `main`.

## Repos in scope

| Repo | Tool group | Role |
|------|-----------|------|
| `dashboard-test-hub-dashboard` | Core | Test dashboard |
| `dashboard-test-hub` | Core | Test hub |
| `hub-dashboard-predtimechart` | Forecasts | Python forecast generator |
| `hub-data` | Forecasts | Python hub data library (hubdata) |
| `hubPredEvalsData` | Evals | R eval scores package |
| `hubEvals` | Evals | R scoring functions |
| `hubPredEvalsData-docker` | Evals | Docker wrapper |
| `predevals` | Site | JS eval visualization |
| `hub-dash-site-builder` | Site | Docker site renderer |

## Locate repo procedure

Reuse the **known repo procedure** from `/dashboard-local-build`. For each repo:

1. Check `~/.claude/dashboard-repos.yml` for a saved path:
   ```bash
   saved_path=$(yq '."<repo-name>"' ~/.claude/dashboard-repos.yml 2>/dev/null)
   ```

2. Use `AskUserQuestion` to locate the repo:
   - header: short repo name
   - Option 1 (only if saved path exists and the directory is valid): "$saved_path" with description "Previously saved path"
   - Next option: "Clone to /tmp/" with description "Clone hubverse-org/<repo-name> into /tmp/"
   - Last option: "Provide a path" with description "Provide a local path to this repo"

3. If cloning:
   ```bash
   git clone "https://github.com/hubverse-org/<repo-name>.git" "/tmp/<repo-name>"
   ```

4. **Save path.** If the resolved path is new or changed, use `AskUserQuestion`:
   - header: "Save path"
   - Option 1: "Yes (Recommended)" with description "Save this path to ~/.claude/dashboard-repos.yml for future runs"
   - Option 2: "No" with description "Don't save, ask again next time"

No branch selection in this procedure (this skill always creates `smoke-test` from `main`).

---

## Phase 1: Setup

### Select repos

Use `AskUserQuestion` with `multiSelect: true`:
- header: "Repos"
- Option 1: "All 9 repos (Recommended)" with description "Create smoke-test branches on all tool repos, test dashboard, and test hub"
- Option 2: "Core only" with description "Test dashboard + test hub only"
- Option 3: "Forecast tools" with description "hub-dashboard-predtimechart + hub-data"
- Option 4: "Eval tools" with description "hubPredEvalsData + hubEvals + hubPredEvalsData-docker"

Note: "Site tools" (predevals + hub-dash-site-builder) can be added as an option if the list permits, otherwise the user can select "All 9 repos" or use "Other" to specify.

### Select mode

Use `AskUserQuestion`:
- header: "Mode"
- Option 1: "Local only" with description "Create branches in local clones only. Faster, no remote changes."
- Option 2: "Push to remote" with description "Push branches to GitHub. Tests clone/fetch paths. Cleanup deletes remote branches."

### Locate repos

For each selected repo, use the **locate repo procedure** above to find or clone a local path.

### Check for existing smoke-test branches

Before creating branches, check each repo:
```bash
git -C "$repo_path" branch --list smoke-test
```

If push-to-remote mode, also check remote:
```bash
git -C "$repo_path" ls-remote --heads origin smoke-test
```

If any `smoke-test` branches already exist, use `AskUserQuestion`:
- header: "Existing branch"
- Option 1: "Delete and recreate" with description "Remove existing smoke-test branches and create fresh ones"
- Option 2: "Abort" with description "Stop setup, keep existing branches"

To delete existing branches:
```bash
git -C "$repo_path" checkout main
git -C "$repo_path" branch -D smoke-test 2>/dev/null
git -C "$repo_path" push origin --delete smoke-test 2>/dev/null  # only if push-to-remote
```

### Create branches

For each repo:

1. Check for uncommitted changes:
   ```bash
   git -C "$repo_path" status --porcelain
   ```
   If there are uncommitted changes, use `AskUserQuestion`:
   - header: "Uncommitted"
   - Option 1: "Stash and continue" with description "Stash changes, create branch, will restore on cleanup"
   - Option 2: "Skip this repo" with description "Don't create a smoke-test branch on this repo"
   - Option 3: "Abort" with description "Stop setup entirely"

2. Create the branch:
   ```bash
   git -C "$repo_path" fetch origin
   git -C "$repo_path" checkout main
   git -C "$repo_path" checkout -b smoke-test
   git -C "$repo_path" commit --allow-empty -m "smoke-test: marker commit for skill testing"
   ```

3. If push-to-remote mode:
   ```bash
   git -C "$repo_path" push origin smoke-test
   ```

### Report setup results

List all repos where `smoke-test` was created:
```bash
echo "Repo: $repo_name"
echo "  Path: $repo_path"
echo "  SHA: $(git -C "$repo_path" rev-parse --short HEAD)"
echo "  Mode: local|pushed"
```

### Print test instructions

Tell the user what to do next. Include:

1. The exact paths to provide when the test skill asks for repo locations
2. Instruction to select `smoke-test` as the branch for every repo
3. Instruction to select "Test dev versions" and choose all tools
4. Instruction to return to this conversation when done

Example output:

> **Smoke-test branches created.** Now run the skill you want to test in a new conversation.
>
> **Repo paths to use:**
> - Test dashboard: `$dash_path`
> - Test hub: `$hub_path`
> - predtimechart: `$ptc_path`
> - hub-data: `$hubdata_path`
> - (etc.)
>
> **When prompted:**
> - For branches: select `smoke-test` on every repo
> - For dev versions: select "Test dev versions" and choose all tools
> - For each tool repo location: use the paths listed above
>
> Come back to this conversation when you're done and say "ready".

---

## Phase 2: Pause

Use `AskUserQuestion`:
- header: "Test status"
- Option 1: "Verify + clean up" with description "Check results and remove all smoke-test branches"
- Option 2: "Just clean up" with description "Remove all smoke-test branches without checking results"
- Option 3: "Keep branches" with description "Leave smoke-test branches in place for further testing"

If "Keep branches", end the skill.

---

## Phase 3: Verify + Cleanup

### Verify (if requested)

For each repo, confirm the branch still exists:
```bash
git -C "$repo_path" branch --list smoke-test
```

Report which branches are present and which are missing (a missing branch might indicate the test skill deleted it, which would be unexpected).

Use `AskUserQuestion`:
- header: "Results"
- Option 1: "All passed" with description "Build succeeded, version reporting showed smoke-test for all tools"
- Option 2: "Some failures" with description "Some steps failed or reported wrong versions"
- Option 3: "Build failed" with description "The build did not complete"

If "Some failures" or "Build failed", the user can provide details via the "Other" free text option. Report the results summary.

### Cleanup

For each repo:

1. Switch back to main and delete the branch (use `-D` because the empty marker commit will always trigger a "not fully merged" warning with `-d`):
   ```bash
   git -C "$repo_path" checkout main
   git -C "$repo_path" branch -D smoke-test
   ```

2. If push-to-remote mode, delete the remote branch:
   ```bash
   git -C "$repo_path" push origin --delete smoke-test 2>/dev/null
   ```

3. If changes were stashed during setup, restore them:
   ```bash
   git -C "$repo_path" stash pop
   ```

If any cleanup step fails, report the failure and continue with other repos. The user can clean up manually later.

### Sanity check

After cleanup, verify that no unexpected changes ended up on main. For each non-`/tmp/` repo:

```bash
echo "=== $repo_name ==="
echo "Branch: $(git -C "$repo_path" branch --show-current)"
echo "Working tree:"
git -C "$repo_path" status --short
echo "Local commits ahead of origin:"
git -C "$repo_path" log origin/main..HEAD --oneline
```

If any repo shows working tree changes that were not present before setup (compare against the uncommitted changes noted during the setup phase), or commits ahead of origin, warn the user.

### Report cleanup results

For each repo, report:
- Branch deleted (local): yes/no
- Branch deleted (remote): yes/no/not applicable
- Stash restored: yes/no/not applicable
- Sanity check: clean / issue found
