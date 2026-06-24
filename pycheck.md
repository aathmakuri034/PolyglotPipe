Mypy: The Type Checker
Ruff: The Blazing-Fast Linter + Formatter
pyflakes	Find unused variables/imports : Does it work right
Ruff is written in Rust and combines all of the above into a single tool : Does it look right
.pre-commit-config.yaml - pre commit check

# .pre-commit-config.yaml
repos:
  # Ruff: Lint + Format
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.1    # use latest version; run `pre-commit autoupdate` to update
    hooks:
      # Run linter first (with auto-fix)
      - id: ruff-check
        args: [--fix]
      # Then run formatter
      - id: ruff-format

  # Mypy: Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0    # use latest version
    hooks:
      - id: mypy
        args: [--strict, --ignore-missing-imports]
        # If your code uses typed third-party packages, add them here
        additional_dependencies:
          - pydantic
          - types-requests

# Install hooks into .git/hooks/
pre-commit install


“I’m on a deadline — can I skip the hooks?”

git commit --no-verify -m "hotfix: emergency patch"

pyproect.toml 

/clear