# hubverse-claude-skills

Shared [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) for hubverse development workflows.

## Available skills

| Skill | Description |
|-------|-------------|
| [`dashboard-local-build`](skills/dashboard-local-build) | Build a hub dashboard locally end to end using the three-tool pipeline (predtimechart, predevals, site-builder), with optional swap-in of dev versions of any tool. |
| [`dashboard-smoke-test`](skills/dashboard-smoke-test) | Set up `smoke-test` branches across dashboard tool repos so a skill can be tested against dev versions, then verify and clean up. |
| [`hubverse-release`](skills/hubverse-release) | Walk through the hubverse R package release checklist end to end (version bump, NEWS, release branch and PR, optional CRAN prep, tag, GitHub release, post-release dev bump). |
| [`explore-hub`](skills/explore-hub) | A prototype skill to help hub administrators explore a hub. See [explore-hub/README.md](explore-hub/README.md) for details. |

## Setup

Clone this repository:

```bash
git clone git@github.com:hubverse-org/hubverse-claude-skills.git ~/hubverse-claude-skills
```

Symlink the skills you want into your personal skills directory:

```bash
ln -s ~/hubverse-claude-skills/skills/<skill-name> ~/.claude/skills/<skill-name>
```

To update skills, pull the latest changes:

```bash
cd ~/hubverse-claude-skills && git pull
```

## Shared conventions

[`conventions/hubverse.md`](conventions/hubverse.md) holds the hubverse conventions for Claude Code: code style, branching, PRs and issues, reviewing PRs, the project board, NEWS entries, comments and documentation, and testing.

To load them, add this line to your personal `~/.claude/CLAUDE.md`, or to a `CLAUDE.md` in the directory that holds your hubverse clones:

```
@~/hubverse-claude-skills/conventions/hubverse.md
```

Put personal preferences in that same file, alongside the import. They take precedence over the shared conventions.

## Adding a new skill

1. Create a new directory under `skills/` with a `SKILL.md` file
2. Open a pull request for review
3. Once merged, team members symlink the new skill into their personal skills directory

See the [Claude Code skills documentation](https://docs.anthropic.com/en/docs/claude-code/skills) for details on writing skills.
