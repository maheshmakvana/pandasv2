# pandasv2 — Claude Code Context

## What this package does

Full pandas drop-in replacement with built-in JSON serialization and web framework integration. Users replace `import pandas as pd` with `import pandasv2 as pd`.

**Install:** `pip install pandasv2`  
**Usage:** `import pandasv2 as pd`

## Source files (only read/edit these)

| File | Responsibility |
|------|---------------|
| `pandasv2/core.py` | Core serialization logic |
| `pandasv2/dataframe.py` | DataFrame subclass — adds `to_json_safe()`, `to_web()`, `from_json_safe()` |
| `pandasv2/series.py` | Series subclass with web methods |
| `pandasv2/converters.py` | Type converters, dtype handling |
| `pandasv2/integrations.py` | FastAPI/Flask/Django helpers, `setup_json_encoder(app)` |
| `pandasv2/analytics.py` | Analytics helpers |
| `pandasv2/io.py` | I/O helpers |
| `pandasv2/groupby.py` | GroupBy extensions |
| `pandasv2/reshape.py` | Reshape helpers |
| `pandasv2/styling.py` | DataFrame styling extensions |
| `pandasv2/plotting.py` | Plotting helpers |
| `pandasv2/window.py` | Rolling/expanding window ops |
| `pandasv2/accessors.py` | pandas `.web` / `.json_safe` accessor |
| `pandasv2/arrays.py` | Custom array extensions |
| `pandasv2/api_types.py` | Type definitions |
| `pandasv2/testing.py` | Testing utilities |
| `pandasv2/excel_writer.py` | Excel export helpers |
| `pandasv2/offsets_ext.py` | Date offset extensions |
| `pandasv2/__init__.py` | Public API |
| `tests/test_core.py` | Test suite |
| `setup.py` | Package config (name=pandasv2, version=2.0.0) |
| `README.md` | PyPI description |

## Ignore completely

`venv/`, `.git/`, `dist/`, `__pycache__/`, `*.egg-info/`

## Key API additions over pandas

```python
df.to_json_safe()           # DataFrame → JSON string (no serialization errors)
df.to_web()                 # DataFrame → web-ready dict/response
DataFrame.from_json_safe(s) # JSON string → DataFrame with dtypes restored
setup_json_encoder(app)     # patch FastAPI/Flask/Django app encoder once
```

## Dependencies

- numpy >= 1.20.0
- pandas >= 1.3.0 (wraps pandas, not a rewrite)
- Optional: fastapi, flask, django
