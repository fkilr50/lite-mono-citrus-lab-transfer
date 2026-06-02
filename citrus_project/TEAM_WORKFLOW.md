# Team Workflow

This file is the short collaboration guide for human teammates and their AI assistants.

Read order for a new helper:

1. `AGENTS.md`
2. `citrus_project/TEAM_WORKFLOW.md`
3. `citrus_project/TASK_BOARD.md`
4. the task-specific note or milestone README

## Current Team Setup

- The user is the main integrator for core Citrus pipeline work.
- Friend A should focus on literature scouting, idea ranking, and related-work intake.
- Friend B should focus on scene taxonomy, example selection, and qualitative/paper-support material.

## Edit Boundaries

Safe for the main integrator:

- `citrus_project/dataset_workspace/`
- repo-root training/evaluation code if Lite-Mono integration changes are needed
- final project-wide decisions in `AGENTS.md`

Safe for Friend A:

- `citrus_project/research/literature_tracker.md`
- milestone note files that clearly belong to model-improvement scouting

Safe for Friend B:

- `citrus_project/research/scene_taxonomy.md`
- `citrus_project/milestones/00_dataset_audit/sample_pack/`
- small writing-support or example-selection notes

Avoid parallel edits unless coordinated:

- `citrus_project/dataset_workspace/`
- shared repo-root model code
- `AGENTS.md`

## Low-Storage Rule

Teammates with storage-limited devices should not be asked to download or extract the full dataset workspace unless that becomes truly necessary.

Prefer this instead:

1. work from `AGENTS.md` and the team docs
2. use the small shared sample pack under `citrus_project/milestones/00_dataset_audit/sample_pack/`
3. contribute through note files and bounded research tasks

## Update Rule

When someone finishes meaningful work:

1. update `citrus_project/TASK_BOARD.md`
2. update the task-specific note file
3. update `AGENTS.md` if the work changes project status, defaults, milestones, or decisions

## Goal

The collaboration system should reduce merge chaos, not create multiple overlapping versions of the same pipeline or experiment.
