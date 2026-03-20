# AI Context Guide

This page is a compact entry point for an AI assistant that needs wiki context for `hg-engine` without spending tokens on low-signal files.

## What To Read First

Start here when the AI is lost:

1. [AI_CONTEXT.md](./AI_CONTEXT.md) for the compressed one-file recovery guide.
2. [Home](./Home.md) for project scope and the list of systems documented in this wiki.
3. [Getting Started](./Getting-Started.md) for a practical reading order.
4. [Troubleshooting](./Troubleshooting.md) if the repository does not build cleanly or a known migration issue appears.

After that, jump only to the page that matches the current task:

- Species, stats, learnsets, typings, forms in data files: [Editing Pokemon Data](./Editing-Pok%C3%A9mon-Data.md)
- Trainer parties and battle setup: [Trainer Pokemon Structure Documentation](./Trainer-Pok%C3%A9mon-Structure-Documentation.md)
- Wild encounters and encounter forms: [Wild Pokemon Table Documentation](./Wild-Pok%C3%A9mon-Table-Documentation.md)
- Evolution behavior: [New Evolution Methods Documentation](./New-Evolution-Methods-Documentation.md)
- Items: [Item System Documentation](./Item-System-Documentation.md)
- Forms: [Form System Documentation](./Form-System-Documentation.md)
- Move data fields: [Move Data Structure Documentation](./Move-Data-Structure-Documentation.md)
- Move battle behavior: [Move Scripting Systems Documentation](./Move-Scripting-Systems-Documentation.md)
- Move visuals and particles: [Move Animation Scripting System Documentation](./Move-Animation-Scripting-System-Documentation.md)
- Overworld systems: [Overworld System Documentation](./Overworld-System-Documentation.md)

## High-Signal Files

These are generally worth indexing for AI context:

- `AI_CONTEXT.md`
- All top-level `.md` files except the ones called out below as low value or outdated
- Especially `Getting-Started.md`, `Troubleshooting.md`, and the task-specific system docs

## Low-Signal Or Skip-By-Default Content

These should usually be ignored unless the task explicitly needs them:

- `.git/`
  - Pure repository metadata, history, hooks, and pack files
- `resources/`
  - Mostly screenshots, gifs, palettes, and binary examples
  - Useful for humans following tutorials, usually not useful for an AI editing code
- `Notepad---ARM-Language-Highlighting.md`
  - Editor XML, not engine behavior

## Outdated Or Use-With-Care Pages

- `Move-Scripting-Systems-Documentation.md`
  - High value conceptually, but it explicitly says parts of the command naming and format are outdated after script refactors
  - Use it for architecture and examples, then verify details in the main repository before editing
- `Move-Animation-Scripting-System-Documentation.md`
  - Useful for concepts, but some sections are exploratory and less certain than the core battle scripting docs

## Best Token Budget Strategy

If context is tight, prefer this order:

1. Read `AI_CONTEXT.md`
2. Read exactly one task-specific doc
3. Read `Troubleshooting.md` only if the problem looks like setup, migration, or build breakage
4. Ignore `resources/` unless the task is specifically about sprites, particles, palettes, or tutorial screenshots

## Recommended Packaging For AI Use

If you want to turn this wiki into an AI recovery pack, the best compact set is:

- `AI_CONTEXT.md`
- `Getting-Started.md`
- `Troubleshooting.md`
- One or more system docs chosen per task

Avoid bundling the entire `resources/` folder into the default context package.

## Practical Rule

When unsure, prefer markdown pages that describe data structures, macros, tables, or workflow steps. Ignore images, gifs, editor configuration, and repository internals unless the current task directly depends on them.
