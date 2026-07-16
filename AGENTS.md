# Repository Guidelines

## Project Structure & Module Organization

- `app/` contains the FastAPI service. `main.py` defines HTTP routes, `convert.py` contains JCL conversion logic, and `models.py` contains data models.
- `app/static/index.html` is the bundled browser UI.
- `tests/` contains pytest tests; reusable JCL/JSON inputs are in `tests/fixtures/`.
- `build_local.py` and `local_launcher.py` build and launch the Windows standalone executable.

## Build, Test, and Development Commands

Create a development environment and install dependencies:

```bash
pip install -e ".[dev]"
```

Run the service locally on port 8080:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Run the full test suite:

```bash
pytest tests/
```

Build the Windows executable (requires the sibling `Formulator/` checkout):

```bash
pip install -r requirements-build.txt
python build_local.py
```

## Coding Style & Naming Conventions

Use Python 3.11+ with four-space indentation, type-aware, focused functions, and descriptive `snake_case` names. Use `PascalCase` for test classes and `test_...` for test methods. Keep API field names and exported JSON keys compatible with the existing contract. No formatter or linter is configured; keep imports clean and follow standard PEP 8 conventions.

## Testing Guidelines

Use pytest and FastAPI’s `TestClient`. Add conversion behavior tests in `tests/test_convert.py` and endpoint/validation tests in `tests/test_api.py`; add representative inputs under `tests/fixtures/` when needed. Run `pytest tests/` before submitting changes. Preserve coverage for validation, diagnostics, timelines, and output compatibility.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Add Windows standalone build` and `Fix: ...`. Follow that style, keeping each commit focused. Pull requests should explain the behavior change, list validation commands and results, identify API or output-schema changes, and include screenshots for visible UI changes. Link the relevant issue when one exists.

## Security & Configuration Tips

Do not commit secrets, and review upload-size and file-type validation when changing the conversion endpoint.
