# AGENTS.md

## Setup and checks

- Use `uv sync --locked` from the repo root; `.python-version` pins 3.12 even though `pyproject.toml` allows newer versions.
- No test or lint runner is configured. For a download-free smoke check, run `uv run --locked python -m compileall -q scripts` and use `--help` on the MITMA and AEMET CLIs.

## Ingestion and modelling

- The entrypoints are the individual `scripts/download_*.py` files; `main.py` is a placeholder, not a pipeline. Downloads live under ignored `data/`, so a fresh checkout has no input data.
- MITMA: preview one district day with `uv run --locked python scripts/download_mitma.py --start 2024-01-01 --end 2024-01-01 --levels distritos --auxiliares --dry-run`. Dry-run still queries public S3 and exits nonzero for missing objects. End dates are inclusive; `--mode mensual` takes `YYYY-MM` and saves TARs without extracting them.
- `docs/modelling.md` specifies MITMA districts as the modelling grain. For INE joins, `--auxiliares` fetches the many-to-one section-to-district crosswalk to `data/mitma/zonificación/relacion_ine_zonificacionMitma.csv` (accented local directory).
- AEMET: `uv run --locked python scripts/download_aemet.py --start YYYY-MM-DD --end YYYY-MM-DD` uses inclusive dates and writes JSON in chunks of up to 15 days. It reads `AEMET_API_KEY` from the environment first, then a plain `AEMET_API_KEY=...` line in the root `.env`.
- DGT and Copernicus start downloading on import or execution, even with `--help`; both hard-code 2022–2024. Copernicus uses `cdsapi` credentials (`~/.cdsapirc` or `CDSAPI_URL` and `CDSAPI_KEY`), not AEMET's `.env` loader.
