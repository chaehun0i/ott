# GitHub Actions Automatic Trigger Pause Plan

## Purpose

Temporarily prevent failing workflows from running automatically while keeping
each workflow available for controlled manual diagnosis and verification.

## Execution Checklist

- [x] Inventory all workflow files and their automatic triggers.
- [x] Replace pull request, push, tag and schedule triggers with `workflow_dispatch`.
- [x] Preserve workflow job definitions and avoid changing their verification behavior.
- [x] Document the paused triggers and objective reactivation gates.
- [x] Verify no workflow retains an automatic trigger.
- [x] Record the change in AI-DLC state and audit artifacts.

## Result

All four workflows are manual-only. Automatic execution can be restored one
workflow at a time after each workflow passes a controlled manual run.
