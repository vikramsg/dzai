## Python

1. Always use uv for Python projects.
    - `uv run main.py` not `uv run python main.py`
    - `uv run -m main` not `uv run python -m main`
    - `uv` will only run from folders where the `pyproject.toml` exists. Make sure you are at the correct location.
2. Follow Python best practices.
  - Prefer functions over classes.
  - Explicit over implicit.
  - Modern practices `str | None` over `Optional[str]`.
3. DO NOT introduce any `try-except` unless you are explicitly asked.
4. THINK HARD. Write simple code. Understand the requirements properly.
5. You do not always know the lates API's. Use your web search tool to understand what is required.
6. DO NOT stop after just making code changes. Run it to make sure it works.
    - Unless explicitly asked otherwise.
7. DO NOT write nested functions.
8. Prefer not using any metaprogramming like using `hasattr` and `getattr`. Always prefer dealing with Pydantic BaseModel.
