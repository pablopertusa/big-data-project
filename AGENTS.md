# Repository guidance

## Environment and execution
- Use Python 3.12 (`.python-version`) and `uv sync --locked` to install the locked environment. Run scripts with `uv run python ...`; select `.venv/bin/python` as the notebook interpreter.
- The working entrypoint is `notebooks/00_lectura_datos.ipynb`, using an in-memory DuckDB connection. `main.py` only prints a greeting; there is no implemented ingestion CLI or persisted database.
- Start the notebook from the repository root or `notebooks/`: its data-path detection only checks the current directory and its parent.
- No test suite, lint/typecheck configuration, or CI workflow exists. Verify data-reading changes with the affected notebook cells, executing prerequisite cells first; `uv run python main.py` does not verify the analysis.

## Data layout and scope
- Actual inputs are under `data/mitma/`, including the accented directory `zonificación/`. Levels are case-sensitive: `distritos`, `municipios`, `GAU`; GAU auxiliary filenames use `gaus` (e.g. `zonificacion_GAU/nombres_gaus.csv`).
- Local daily files and the notebook default use `20230101`. `config/datasets.json` instead describes a `2023-03-06`, municipalities-only profile; it is not a reliable inventory of downloaded files or wired into the notebook.
- The `.gitignore` comment about regenerating files with a CLI is stale: no downloader exists. Its `/data/raw/` exclusion does not cover the current `data/mitma/` inputs.
- `docs/esquema_datos_mitma.md` documents the logical schema, source dictionary, and semantic caveats; it is not an implemented Bronze/Silver/Gold schema. Read it before changing transformations or joins.

## Parsing and aggregation pitfalls
- Follow the notebook's DuckDB reader: `delim='|'`, `all_varchar=true`, `nullstr='__NULL_NO_PUBLICADO__'`. Preserve leading zeros, literal `NA`, and empty strings rather than allowing automatic type/null inference. Cast measures explicitly when computing.
- `poblacion_*.csv` files have no header (`header=false`); `nombres_municipios.csv` has an extra unnamed index column that is not a territorial key.
- Zone identity is `(nivel, codigo)`; `nivel` is derived from the folder. Use the INE–MITMA crosswalk, not names or assumed equal codes; validate/deduplicate mappings before joins to avoid multiplying measures.
- Mobility rows are aggregates: sum `viajes`, not row counts. Do not sum territorial levels together or join indicator tables at incompatible grains. Privacy `NA` categories must not be silently dropped.
- Keep original age categories: local values differ from the official dictionary. `distancia` is a categorical straight-line distance band, not an exact road distance; do not reconstruct `viajes_km` from band midpoints.
- Keep shapefile components (`.shp`, `.shx`, `.dbf`, `.prj`, etc.) together; they are not separate datasets.
