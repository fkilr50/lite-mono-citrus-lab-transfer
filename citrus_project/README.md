# Citrus Project Workspace

This folder contains the project-owned work for the Citrus Farm + Lite-Mono research effort.

The original Lite-Mono repository code remains at the repo root. Custom project work is grouped here so it is easier to see what belongs to the research fork versus the upstream model code.

## Structure

- `dataset_workspace/` - Citrus dataset download, extraction, audit, densification, and build scripts plus the local dataset workspace
- `research/` - research notes, paper shortlist, beginner Q&A, and ignored generated artifacts
- `milestones/` - milestone-specific folders for future implementation, experiments, notes, and outputs
- `TEAM_WORKFLOW.md` - team onboarding and collaboration rules
- `TASK_BOARD.md` - current owner/status/next-action board

## Working Rule

When possible:

1. keep Citrus-specific pipeline code and data workflow under `dataset_workspace/`
2. keep paper/support notes under `research/`
3. place milestone-specific code, experiment helpers, and notes under the matching folder in `milestones/`

This keeps the custom research work separate from the original Lite-Mono codebase.
