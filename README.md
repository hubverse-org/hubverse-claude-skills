# hubverse-claude-skills

Shared [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) for hubverse development workflows.

## Available skills

| Skill | Description                                                                                                                                                                   |
|-------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`hubverse-release`](skills/hubverse-release) | Walk through the hubverse R package release checklist end to end (version bump, NEWS, release branch and PR, optional CRAN prep, tag, GitHub release, post-release dev bump). |
| [`explore-hub`](skills/explore-hub) | A prototype skill to help hub administrators explore a hub. See [explore-hub/README.md](explore-hub/README.md) for details.                                                   |

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

## Adding a new skill

1. Create a new directory under `skills/` with a `SKILL.md` file
2. Open a pull request for review
3. Once merged, team members symlink the new skill into their personal skills directory

See the [Claude Code skills documentation](https://docs.anthropic.com/en/docs/claude-code/skills) for details on writing skills.
