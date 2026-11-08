# Contributing

This guide describes how work is planned, written and delivered in this repository. It formalizes the conventions already used in the history.

## Workflow

1. Every change starts as an issue on the project board.
2. Create a branch for the issue and make small, atomic commits.
3. Open a pull request that closes the issue and merge it.
4. Move the card on the board and close the issue.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Released code. Receives `dev` through a merge pull request. |
| `dev` | Default branch. Integrates finished work. |
| `epic/<n>-<name>` | Groups the issues of an epic. Merges into `dev` when the epic is complete. |
| `<type>/<n>-<name>` | Work for one issue, for example `feat/4-accounts-backend` or `docs/9-project-documentation`. |

- `<n>` is the issue number and `<name>` is a short description in kebab-case.
- `<type>` is one of the commit types below.
- A branch for a sub-issue of an epic branches from the epic branch and targets it. Any other branch starts from `dev` and targets it.

## Commits

Commits follow Conventional Commits, without a scope:

```text
<type>: <description>
```

- Types: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `build` (dependencies and the Docker image), `ci` (the pipeline) and `chore`.
- The description is lowercase, in the imperative mood, in English, without a final period, and ideally up to 72 characters.
- Each commit is atomic: it contains one logical change and leaves the project working.
- Use `style` only for formatting that changes no behavior.

## Issues

- The title uses the same `<type>: <description>` format. Issues that cover a single layer end with `- backend` or `- frontend`. Epics and cross-layer issues have no suffix.
- The body has a `## Description` section that explains the problem and what the issue changes, followed by a `## Features` section with one bullet per deliverable.
- Labels: `enhancement`, `bug`, `documentation`, `refactor` or `test` for the type, `epic`, `backend`, `frontend` or `database` for the area.
- Sub-issues are linked to their epic. The milestone is the sprint.

## Pull requests

- The title is the main commit subject followed by the issue number: `feat: add database relations and tables for social system (#3)`.
- The body starts with `Closes #<issue>` and follows the pull request template.
- Copy the labels, milestone and assignee from the issue.
- The CI workflow runs the tests and `pip-audit` on every pull request. Branch protection on `dev` and `main` requires both checks to pass and the branch to go through a pull request, for administrators too.
- Merge with **Rebase and merge** to keep the history linear. Merged branches are kept, so the repository does not delete them automatically.
- Releases are the exception: `dev` is merged into `main` with a merge commit.
- GitHub closes issues automatically only when the pull request reaches the default branch. For pull requests into an epic branch, close the issue manually after the merge.
- A pull request with a change people notice adds a line under `Unreleased` in `CHANGELOG.md`, in the section that fits: Added, Changed, Deprecated, Removed, Fixed or Security.

## Releases

Versions follow [Semantic Versioning](https://semver.org): a breaking change raises the major version, a new feature the minor version and a fix the patch version.

1. Move the `Unreleased` entries in `CHANGELOG.md` to a new version heading with the date, and update the comparison links at the end of the file.
2. Merge that change into `dev`, then open a pull request from `dev` to `main` titled `chore: release version X.Y.Z` and merge it with a merge commit.
3. Tag the merge commit on `main` as `vX.Y.Z` and publish a GitHub release with the notes of that version.

## Board

The columns of the **Status** field describe the flow:

`Backlog` → `Ready` → `In progress` (`General`, `Frontend` or `Backend`) → `In review` → `Done`

- **Backlog**: ideas and future work that are not scoped yet.
- **Ready**: scoped, sized and prioritized, with dependencies met or in progress.
- **In progress**: someone is working on it. `General` is for epics and cross-cutting work.
- **In review**: a pull request is open.

**Priority**

- `P0`: blocks other issues or the epic.
- `P1`: core scope, needed for the epic to be complete.
- `P2`: nice to have, can move to the next sprint.

**Size** (effort for one person)

- `XS`: under half a day.
- `S`: about one day, one layer.
- `M`: two to three days, or a change across both layers.
- `L`: three to five days, several pages or modules.
- `XL`: an epic, split into sub-issues.

Start and target dates feed the roadmap view. The target date of a sub-issue never passes the target date of its epic.

## Code conventions

- Code, comments, commit messages and documentation are written in English. The application interface is in Brazilian Portuguese.
- Python uses `snake_case`, four spaces, type hints on new code and `str | None` instead of `Optional`.
- JavaScript uses `camelCase` and four spaces.
- CSS follows BEM (`block__element--modifier`) and the `u-` prefix for utility classes.
- Database tables are uppercase and plural (`USERS`, `ARTICLES`, `LIKES`), and columns use `snake_case`.
- REST endpoints use plural nouns and no verbs.
- Environment variables use `SCREAMING_SNAKE_CASE`.
- SQL always uses parameterized queries. Never build a query by concatenating input.
- Comments are rare and brief. Explain why, not what.
- Use guard clauses and early returns instead of deep nesting.
- Never swallow errors: log them with context or let them propagate.
- Never commit secrets or `.env`. Add any new variable to `TEMPLATE.env` and to the README.
- Every file ends with exactly one newline. `.editorconfig` applies the formatting rules in compatible editors.

## Definition of done

- The application starts with `docker compose up --build` and the changed behavior was tested by hand.
- `docker compose --profile test run --rm tests` passes. New behavior has tests, and a bug fix has a test that fails without it.
- The README and `TEMPLATE.env` are updated when behavior or configuration changes.
- `CHANGELOG.md` has the change under `Unreleased` when people will notice it.
- The commits and the pull request follow this guide.
- The issue is closed and the card is in `Done`.
