# AGENTS.md

## Language

- Respond in Russian unless the user explicitly asks for another language.
- Keep answers concise, practical, and focused on the current task.

## Project workflow

- Do not scan the whole repository unless it is necessary.
- Before editing, identify the exact files that need changes.
- Prefer minimal, targeted changes over large rewrites.
- Preserve the existing project structure, style, naming, and formatting.
- Do not modify unrelated files.
- Do not change public APIs, configuration formats, database schemas, or behavior unless the task explicitly requires it.
- If a task is ambiguous, make the safest reasonable assumption and state it briefly.

## Token-efficient file access

- Do not read large files entirely unless required.
- Prefer targeted commands:
  - `rg` for search
  - `sed -n 'start,endp' file` for partial reads
  - `head` / `tail` for previews
  - `find . -maxdepth N` for limited discovery
- Avoid reading generated, cached, dependency, or build files:
  - `.git/`
  - `.venv/`
  - `venv/`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.mypy_cache/`
  - `.ruff_cache/`
  - `dist/`
  - `build/`
  - `htmlcov/`
  - `.coverage`
  - `*.egg-info/`
  - lock files, unless dependency resolution is part of the task

## Python standards

- Write clear, idiomatic Python.
- Prefer simple code over clever abstractions.
- Use type hints for new or changed public functions.
- Keep functions small and focused.
- Use explicit names for variables, functions, and classes.
- Avoid broad `except Exception` unless there is a clear reason.
- Do not silently swallow errors.
- Prefer standard library solutions when they are sufficient.
- Do not introduce new dependencies unless clearly justified.

## Testing and validation

- When changing behavior, add or update tests if the project already has tests.
- Prefer running the smallest relevant test first.
- Use targeted commands such as:
  - `pytest tests/test_specific_file.py`
  - `pytest tests/test_specific_file.py::test_specific_case`
  - `ruff check path/to/file.py`
  - `mypy path/to/file.py`
  - `pylint *.py`
- Do not run expensive full test suites unless necessary.
- If tests cannot be run, explain exactly why and what should be run manually.

## Formatting and linting

- Follow the formatting tools already used by the project.
- If configuration exists, respect it:
  - `pyproject.toml`
  - `setup.cfg`
  - `tox.ini`
  - `.ruff.toml`
  - `.flake8`
  - `mypy.ini`
- Do not reformat unrelated files.
- Do not introduce style-only changes in files unrelated to the task.

## Dependencies

- Do not edit dependency files unless required:
  - `requirements.txt`
  - `requirements-dev.txt`
  - `pyproject.toml`
  - `poetry.lock`
  - `Pipfile.lock`
  - `uv.lock`
- If adding a dependency, explain why the standard library is not enough.

## Security

- Do not hardcode secrets, tokens, passwords, API keys, private URLs, or credentials.
- Do not print sensitive values in logs.
- Validate and sanitize external input where relevant.
- Be careful with shell execution, file paths, deserialization, SQL, templates, and network requests.
- Prefer safe APIs over manual string concatenation for commands, paths, SQL, and URLs.

## Git behavior

- Do not create commits unless explicitly asked.
- Do not rewrite git history.
- Do not run destructive commands such as `git reset --hard`, `git clean -fd`, or mass deletes unless explicitly asked.
- Before making risky changes, inspect the current diff.

## Response format

- Start with the result or the recommended action.
- Mention changed files.
- Mention tests or checks performed.
- If something was not done, say so clearly.
