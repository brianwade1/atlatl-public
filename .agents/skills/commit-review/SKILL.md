---
name: commit-review
description: Review pending Git changes before a user-managed commit, recommend the exact files to include, and draft a Conventional Commits 1.0.0 message. Use when asked to prepare a commit, review commit contents, or suggest a commit message. Never stage or commit changes.
---

# Commit review

Produce a read-only recommendation for the user's next commit. The user handles staging and committing. This skill is invoked in conversation; it does not install or act as a Git hook.

## Boundaries

- Do not edit files, stage or unstage changes, create commits, amend history, stash, switch branches, or push. Do not run hooks, formatters, generators, or tests that could change files as part of this review.
- Use read-only inspection. Report fixes or missing validation as recommendations, without applying them.
- Treat staged contents as evidence of intent, not automatic approval to include everything. Preserve the user's existing index and working tree.

## Review

1. Read applicable `AGENTS.md` instructions and establish the requested commit scope from the conversation. If no scope is given, inspect all pending changes and propose coherent commit groups rather than assuming they belong together.
2. From the repository root, inspect staged, unstaged, and untracked files. Useful commands:

   ```sh
   git --no-optional-locks status --short --untracked-files=all
   git diff --no-ext-diff --no-textconv --name-status
   git diff --no-ext-diff --no-textconv
   git diff --cached --no-ext-diff --no-textconv --name-status
   git diff --cached --no-ext-diff --no-textconv
   git log -5 --format=%s
   ```

   Inspect untracked file contents separately; they are absent from `git diff`. Expand directories to individual files. For large changes, inspect summaries and then focused diffs; disclose any files or binary contents that could not be reviewed. Use literal paths and safe quoting, and use NUL-delimited Git output if parsing filenames programmatically. An empty history in a new repository is not a blocker.
3. Compare the actual changes with the requested scope. Include necessary implementation, tests, documentation, configuration, and lockfile changes together. Account for deletions and renames, showing both old and new paths for renames. Do not attribute pre-existing work to the agent or discard it merely because it predates the current task.
4. Identify unrelated work, generated outputs, local settings, and potentially sensitive material. Consult `.gitignore` and repository guidance. Do not list ignored files by default; investigate a specific ignored path only if needed to explain a missing dependency. Never reproduce secret values in the report.
5. Distinguish staged-only, unstaged-only, untracked, and partially staged files. For a partially staged file, say whether the recommendation covers its staged version, its complete current contents, or selected hunks; describe selected changes precisely. Flag staged changes that fall outside the proposed commit.
6. Identify unresolved conflicts, missing companion files, and obvious inconsistencies that prevent a coherent commit. Recommend holding affected files when necessary. Use available validation evidence and clearly distinguish completed checks from checks merely suggested; do not claim tests passed without evidence.
7. Recheck status before reporting. If files changed during the review, inspect the affected diffs again or disclose that the recommendation is incomplete.

## Commit message convention

Use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) for every proposed message, even when earlier commits use another format.

- Format the subject as `type(scope): description`; omit `(scope)` when unnecessary. Prefer lowercase types and concise imperative descriptions.
- Use `feat` for features and `fix` for bug fixes. For other changes, choose an appropriate type such as `docs`, `test`, `refactor`, `perf`, `build`, `ci`, or `chore`; these additional types are conventions, not a required exhaustive list.
- An optional scope names the affected area, such as `scenarios` or `skills`. Follow established scope names where useful.
- Mark breaking changes with `!` immediately before the colon or an uppercase `BREAKING CHANGE:` footer (or both). Explain the incompatibility; when using only `!`, the subject must describe the break. `BREAKING-CHANGE:` is also valid.
- Separate an optional body and footer section with blank lines. Footers use `Token: value` or `Token #value`; multiword tokens use hyphens except `BREAKING CHANGE`. Include only verified references.
- For independent changes of different types, recommend separate commits. Keep supporting tests and documentation with the behavior they support.

## Report

- **Recommended files:** A table with one row per repository-relative path, its Git state, and a short reason for inclusion. List every recommended file explicitly; do not substitute directory names or wildcards. Specify staged versions or selected hunks where relevant.
- **Leave out or hold:** List other pending files with a brief reason, including unrelated work that belongs in a separate commit. If several commits are warranted, give explicit file lists and a message for each, without recommending the same full file for conflicting groups.
- **Suggested commit message:** A copyable text block following the commit message convention above, with an optional body explaining the meaningful changes. Describe only the recommended contents, and omit unsupported validation claims. Check the type, optional scope and breaking marker, colon-space separator, and any body/footer spacing before presenting it.
- **Validation and blockers:** Briefly state known checks, any needed checks, unresolved issues, and inspection limits. End by confirming that files, staging, and commits were left unchanged.

If there are no pending changes, say there is nothing to commit and do not invent a message. If the user's intended scope remains ambiguous, present the useful grouping you can establish and ask only the question needed to resolve the ambiguity.
