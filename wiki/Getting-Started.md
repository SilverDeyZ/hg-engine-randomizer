# Getting Started

This page is a short onboarding guide for anyone opening `hg-engine` for the first time and wanting a practical order to read the wiki.

## Recommended Reading Order

If you are brand new to the project, this is a good path through the documentation:

1. Read [AI Context Guide](./AI-Context-Guide.md) if you want the shortest possible AI-friendly map of the wiki.
2. Read the [repository README](https://github.com/BluRosie/hg-engine/blob/main/README.md) for build setup and base project expectations.
3. Read [Troubleshooting](./Troubleshooting.md) if your repository does not build cleanly before making changes.
4. Read [Editing Pokemon Data](./Editing-Pok%C3%A9mon-Data.md) if your first goal is to add or modify species data.
5. Read [Move Data Structure Documentation](./Move-Data-Structure-Documentation.md) and [Move Scripting Systems Documentation](./Move-Scripting-Systems-Documentation.md) for move behavior work.
6. Read [Item System Documentation](./Item-System-Documentation.md) for item-related additions.
7. Read [Trainer Pokemon Structure Documentation](./Trainer-Pok%C3%A9mon-Structure-Documentation.md) if you plan to edit trainer parties or battle setup.
8. Read [Wild Pokemon Table Documentation](./Wild-Pok%C3%A9mon-Table-Documentation.md) for encounter editing.
9. Read [Form System Documentation](./Form-System-Documentation.md) and [New Evolution Methods Documentation](./New-Evolution-Methods-Documentation.md) for more advanced content work.

## Suggested Workflow

When making changes, this workflow keeps things manageable:

1. Start from a repository state that already builds successfully.
2. Make one focused change at a time instead of batching multiple system edits together.
3. Rebuild and test after each change so breakages are easier to isolate.
4. If a system has dedicated wiki documentation, follow that page's macros, structures, and examples exactly.
5. When something behaves strangely, compare your edits against the documented format before assuming the engine code is wrong.

## Common First Tasks

New contributors usually begin with one of these:

- Adjusting Pokemon stats, typings, abilities, learnsets, or evolutions
- Adding or editing moves and their battle scripts
- Updating item data or item effects
- Editing wild encounters
- Customizing trainer teams

Each of those already has a dedicated documentation page in this wiki, so this page is meant to point you to the right one quickly rather than replace the detailed references.

## Before Asking For Help

Before opening an issue or asking in Discord, it helps to gather:

- The exact file or table you edited
- The exact error message, if there is one
- The steps needed to reproduce the problem
- Whether the repository built successfully before your change
- Whether the relevant wiki page was followed exactly

That information makes troubleshooting much faster for everyone involved.
