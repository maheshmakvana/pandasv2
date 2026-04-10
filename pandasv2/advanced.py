"""
pandasv2.advanced — Advanced DataFrame utilities.

New in 2.1.0:
- DataFrameCache: LRU cache keyed on DataFrame content hash
- DataFrameDiff: Track and apply diffs between DataFrame versions
- DataFramePipeline: Chainable, auditable transformation pipeline
- DataFrameValidator: Declarative column validation
- StreamingExporter: Export large DataFrames in chunked batches
- merge_asof_nearest: Nearest-key merge helper
- profile_dataframe: Rich summary statistics for every column
- DataFrameWatcher: Detect changes to a DataFrame over time
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import time
import threading
from collections import OrderedDict
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# DataFrame content hash
# ---------------------------------------------------------------------------

def _df_hash(df: pd.DataFrame) -> str:
    """Fast content-based hash for a DataFrame (shape + first/last rows + dtypes)."""
    sig = (
        str(df.shape)
        + str(df.dtypes.to_dict())
        + str(df.head(3).values.tolist() if len(df) >= 3 else df.values.tolist())
        + str(df.tail(3).values.tolist() if len(df) >= 3 else "")
    )
    return hashlib.md5(sig.encode()).hexdigest()


# ---------------------------------------------------------------------------
# DataFrameCache
# ---------------------------------------------------------------------------

class DataFrameCache:
    """
    Thread-safe LRU cache for DataFrames, keyed by content hash.

    Parameters
    ----------
    maxsize : int
        Maximum number of DataFrames to store.
    ttl : float | None
        Time-to-live in seconds per entry.

    Example
    -------
    >>> cache = DataFrameCache(maxsize=32)
    >>> @cache.memoize
    ... def expensive_transform(df):
    ...     return df.groupby('category').agg({'value': 'sum'})
    """

    def __init__(self, maxsize: int = 64, ttl: Optional[float] = None) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[pd.DataFrame]:
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None
            entry = self._store[key]
            if self._ttl and (time.time() - entry["ts"]) > self._ttl:
                del self._store[key]
                self._misses += 1
                return None
            self._store.move_to_end(key)
            entry["hits"] += 1
            self._hits += 1
            return entry["df"].copy()

    def set(self, key: str, df: pd.DataFrame) -> None:
        with self._lock:
            if len(self._store) >= self._maxsize and key not in self._store:
                self._store.popitem(last=False)
            self._store[key] = {"df": df.copy(), "ts": time.time(), "hits": 0}
            if key in self._store:
                self._store.move_to_end(key)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        with self._lock:
            return {
                "size": len(self._store),
                "maxsize": self._maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total else 0.0,
            }

    def memoize(self, func: Callable) -> Callable:
        """Decorator: cache result based on DataFrame content hash + extra args."""
        def wrapper(df, *args, **kwargs):
            key = _df_hash(df) + "|" + repr(args) + "|" + repr(kwargs)
            cached = self.get(key)
            if cached is not None:
                return cached
            result = func(df, *args, **kwargs)
            if isinstance(result, pd.DataFrame):
                self.set(key, result)
            return result
        wrapper.__name__ = func.__name__
        return wrapper


# ---------------------------------------------------------------------------
# DataFrameDiff
# ---------------------------------------------------------------------------

class DataFrameDiff:
    """
    Track row-level and column-level differences between two DataFrames.

    Example
    -------
    >>> diff = DataFrameDiff(df_before, df_after)
    >>> diff.summary()
    {'added_rows': 2, 'removed_rows': 0, 'modified_cells': 5, 'added_cols': [], 'removed_cols': []}
    >>> df_patched = diff.apply(df_before)
    """

    def __init__(self, before: pd.DataFrame, after: pd.DataFrame) -> None:
        self._before = before.copy()
        self._after = after.copy()
        self._computed: Optional[Dict[str, Any]] = None

    def _compute(self) -> Dict[str, Any]:
        if self._computed is not None:
            return self._computed

        b, a = self._before, self._after
        added_cols = list(set(a.columns) - set(b.columns))
        removed_cols = list(set(b.columns) - set(a.columns))
        common_cols = list(set(b.columns) & set(a.columns))

        # Row-level diff by index
        added_idx = list(set(a.index) - set(b.index))
        removed_idx = list(set(b.index) - set(a.index))
        common_idx = list(set(b.index) & set(a.index))

        modified_cells = []
        for idx in common_idx:
            for col in common_cols:
                bval = b.loc[idx, col]
                aval = a.loc[idx, col]
                try:
                    same = bval == aval
                    if hasattr(same, '__bool__'):
                        same = bool(same)
                except Exception:
                    same = False
                if not same:
                    modified_cells.append({"index": idx, "column": col,
                                           "before": bval, "after": aval})

        self._computed = {
            "added_rows": len(added_idx),
            "removed_rows": len(removed_idx),
            "added_row_indices": added_idx,
            "removed_row_indices": removed_idx,
            "modified_cells": len(modified_cells),
            "modified_cell_details": modified_cells,
            "added_cols": added_cols,
            "removed_cols": removed_cols,
        }
        return self._computed

    def summary(self) -> Dict[str, Any]:
        d = self._compute()
        return {k: v for k, v in d.items() if k != "modified_cell_details"}

    def cell_changes(self) -> List[Dict[str, Any]]:
        return self._compute()["modified_cell_details"]

    def apply(self, base: pd.DataFrame) -> pd.DataFrame:
        """Apply the diff to *base* to reproduce the 'after' state."""
        return self._after.copy()

    def to_json(self) -> str:
        d = self._compute()
        safe = {}
        for k, v in d.items():
            if k == "modified_cell_details":
                safe[k] = [
                    {kk: (str(vv) if not isinstance(vv, (int, float, str, bool, type(None))) else vv)
                     for kk, vv in cell.items()}
                    for cell in v
                ]
            elif isinstance(v, list):
                safe[k] = [str(x) if not isinstance(x, (int, float, str, bool, type(None))) else x for x in v]
            else:
                safe[k] = v
        return json.dumps(safe, indent=2)


# ---------------------------------------------------------------------------
# DataFramePipeline
# ---------------------------------------------------------------------------

class DataFramePipeline:
    """
    Chainable, auditable DataFrame transformation pipeline.

    Every step is logged with name + elapsed time. The audit log is accessible
    after calling run().

    Example
    -------
    >>> pipe = DataFramePipeline(df)
    >>> result = (pipe
    ...     .rename_cols({'old': 'new'})
    ...     .drop_nulls()
    ...     .add_col('score', lambda df: df['value'] / df['value'].max())
    ...     .filter_rows(lambda df: df['score'] > 0.5)
    ...     .run())
    >>> pipe.audit_log
    [{'step': 'rename_cols', 'ms': 0.12}, ...]
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._source = df.copy()
        self._steps: List[Tuple[str, Callable]] = []
        self.audit_log: List[Dict[str, Any]] = []

    def _add(self, name: str, func: Callable) -> "DataFramePipeline":
        self._steps.append((name, func))
        return self

    # --- column operations ---

    def rename_cols(self, mapping: Dict[str, str]) -> "DataFramePipeline":
        return self._add("rename_cols", lambda df: df.rename(columns=mapping))

    def drop_cols(self, cols: List[str]) -> "DataFramePipeline":
        return self._add("drop_cols", lambda df: df.drop(columns=[c for c in cols if c in df.columns]))

    def select_cols(self, cols: List[str]) -> "DataFramePipeline":
        return self._add("select_cols", lambda df: df[[c for c in cols if c in df.columns]])

    def add_col(self, name: str, func: Callable) -> "DataFramePipeline":
        return self._add(f"add_col:{name}", lambda df: df.assign(**{name: func(df)}))

    def cast_col(self, col: str, dtype) -> "DataFramePipeline":
        return self._add(f"cast:{col}", lambda df: df.assign(**{col: df[col].astype(dtype)}) if col in df.columns else df)

    # --- row operations ---

    def filter_rows(self, predicate: Callable) -> "DataFramePipeline":
        return self._add("filter_rows", lambda df: df[predicate(df)].reset_index(drop=True))

    def drop_nulls(self, subset: Optional[List[str]] = None) -> "DataFramePipeline":
        return self._add("drop_nulls", lambda df: df.dropna(subset=subset).reset_index(drop=True))

    def fill_nulls(self, value: Any = 0) -> "DataFramePipeline":
        return self._add("fill_nulls", lambda df: df.fillna(value))

    def sort(self, by: Union[str, List[str]], ascending: bool = True) -> "DataFramePipeline":
        return self._add("sort", lambda df: df.sort_values(by=by, ascending=ascending).reset_index(drop=True))

    def deduplicate(self, subset: Optional[List[str]] = None) -> "DataFramePipeline":
        return self._add("deduplicate", lambda df: df.drop_duplicates(subset=subset).reset_index(drop=True))

    def limit(self, n: int) -> "DataFramePipeline":
        return self._add("limit", lambda df: df.head(n))

    # --- transforms ---

    def apply(self, func: Callable, name: str = "apply") -> "DataFramePipeline":
        return self._add(name, func)

    def normalize_col(self, col: str) -> "DataFramePipeline":
        def _norm(df):
            mn, mx = df[col].min(), df[col].max()
            rng = mx - mn
            df = df.copy()
            df[col] = 0.0 if rng == 0 else (df[col] - mn) / rng
            return df
        return self._add(f"normalize:{col}", _norm)

    def run(self) -> pd.DataFrame:
        """Execute all steps and return the resulting DataFrame."""
        self.audit_log.clear()
        df = self._source.copy()
        for name, func in self._steps:
            t0 = time.perf_counter()
            df = func(df)
            elapsed = round((time.perf_counter() - t0) * 1000, 4)
            self.audit_log.append({"step": name, "ms": elapsed, "shape": list(df.shape)})
        return df


# ---------------------------------------------------------------------------
# DataFrameValidator
# ---------------------------------------------------------------------------

class ColumnValidationError(Exception):
    pass


class ColumnRule:
    """Single-column validation constraint."""

    def __init__(
        self,
        col: str,
        *,
        required: bool = False,
        dtype: Optional[str] = None,
        not_null: bool = False,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allowed_values: Optional[List[Any]] = None,
        regex: Optional[str] = None,
        unique: bool = False,
        custom: Optional[Callable] = None,
        message: Optional[str] = None,
    ) -> None:
        self.col = col
        self.required = required
        self.dtype = dtype
        self.not_null = not_null
        self.min_val = min_val
        self.max_val = max_val
        self.allowed_values = allowed_values
        self.regex = regex
        self.unique = unique
        self.custom = custom
        self.message = message


class DataFrameValidator:
    """
    Declarative validator for DataFrames.

    Example
    -------
    >>> v = DataFrameValidator()
    >>> v.add_rule(ColumnRule('age', not_null=True, min_val=0, max_val=150))
    >>> v.add_rule(ColumnRule('email', regex=r'.+@.+\..+'))
    >>> errors = v.validate(df)
    """

    def __init__(self) -> None:
        self._rules: List[ColumnRule] = []

    def add_rule(self, rule: ColumnRule) -> "DataFrameValidator":
        self._rules.append(rule)
        return self

    def validate(self, df: pd.DataFrame) -> List[str]:
        """Return list of validation error strings (empty = valid)."""
        import re
        errors: List[str] = []
        for rule in self._rules:
            col = rule.col
            if rule.required and col not in df.columns:
                errors.append(rule.message or f"Column '{col}' is required but missing")
                continue
            if col not in df.columns:
                continue

            series = df[col]

            if rule.not_null and series.isna().any():
                n = series.isna().sum()
                errors.append(rule.message or f"Column '{col}' has {n} null value(s)")

            if rule.dtype:
                actual = str(series.dtype)
                if not actual.startswith(rule.dtype):
                    errors.append(rule.message or f"Column '{col}' dtype should be '{rule.dtype}', got '{actual}'")

            if rule.min_val is not None:
                try:
                    bad = (series.dropna() < rule.min_val).sum()
                    if bad:
                        errors.append(rule.message or f"Column '{col}' has {bad} value(s) below {rule.min_val}")
                except TypeError:
                    pass

            if rule.max_val is not None:
                try:
                    bad = (series.dropna() > rule.max_val).sum()
                    if bad:
                        errors.append(rule.message or f"Column '{col}' has {bad} value(s) above {rule.max_val}")
                except TypeError:
                    pass

            if rule.allowed_values is not None:
                bad = (~series.isin(rule.allowed_values)).sum()
                if bad:
                    errors.append(rule.message or f"Column '{col}' has {bad} value(s) not in {rule.allowed_values}")

            if rule.regex:
                try:
                    mask = series.dropna().astype(str).str.match(rule.regex)
                    bad = (~mask).sum()
                    if bad:
                        errors.append(rule.message or f"Column '{col}' has {bad} value(s) not matching pattern '{rule.regex}'")
                except Exception as e:
                    errors.append(f"Column '{col}' regex check error: {e}")

            if rule.unique and series.duplicated().any():
                n = series.duplicated().sum()
                errors.append(rule.message or f"Column '{col}' has {n} duplicate value(s)")

            if rule.custom:
                try:
                    ok = rule.custom(series)
                    if not ok:
                        errors.append(rule.message or f"Column '{col}' failed custom validation")
                except Exception as e:
                    errors.append(f"Column '{col}' custom validator error: {e}")

        return errors

    def assert_valid(self, df: pd.DataFrame) -> None:
        """Raise ColumnValidationError if any rule fails."""
        errors = self.validate(df)
        if errors:
            raise ColumnValidationError("\n".join(f"  • {e}" for e in errors))


# ---------------------------------------------------------------------------
# StreamingExporter
# ---------------------------------------------------------------------------

class StreamingExporter:
    """
    Export a large DataFrame as a lazy stream of JSON or CSV chunks.

    Example
    -------
    >>> exporter = StreamingExporter(big_df, chunk_size=500)
    >>> for chunk_str in exporter.to_json_stream():
    ...     send_to_client(chunk_str)
    """

    def __init__(self, df: pd.DataFrame, chunk_size: int = 1000) -> None:
        self._df = df
        self._chunk_size = chunk_size

    def to_json_stream(self) -> Generator[str, None, None]:
        """Yield JSON strings for each chunk (list of records)."""
        for start in range(0, len(self._df), self._chunk_size):
            chunk = self._df.iloc[start: start + self._chunk_size]
            yield chunk.to_json(orient="records", date_format="iso")

    def to_csv_stream(self) -> Generator[str, None, None]:
        """Yield CSV strings for each chunk (header on first chunk only)."""
        for i, start in enumerate(range(0, len(self._df), self._chunk_size)):
            chunk = self._df.iloc[start: start + self._chunk_size]
            buf = io.StringIO()
            chunk.to_csv(buf, index=False, header=(i == 0))
            yield buf.getvalue()

    def to_ndjson_stream(self) -> Generator[str, None, None]:
        """Yield newline-delimited JSON (one JSON object per row)."""
        for _, row in self._df.iterrows():
            yield row.to_json() + "\n"

    def collect_json(self) -> str:
        """Collect all chunks into a single JSON array string."""
        return "[" + ",".join(self.to_json_stream()) + "]"


# ---------------------------------------------------------------------------
# profile_dataframe
# ---------------------------------------------------------------------------

def profile_dataframe(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Return rich summary statistics for every column in a DataFrame.

    For numeric columns: count, mean, std, min, p25, median, p75, max, nulls, unique
    For string/object columns: count, nulls, unique, top, top_freq

    Example
    -------
    >>> report = profile_dataframe(df)
    >>> report['age']
    {'count': 100, 'mean': 35.2, 'nulls': 0, ...}
    """
    report: Dict[str, Dict[str, Any]] = {}
    for col in df.columns:
        series = df[col]
        n_total = len(series)
        n_null = int(series.isna().sum())
        n_unique = int(series.nunique(dropna=True))
        info: Dict[str, Any] = {
            "count": n_total,
            "nulls": n_null,
            "null_pct": round(n_null / n_total * 100, 2) if n_total else 0.0,
            "unique": n_unique,
            "dtype": str(series.dtype),
        }
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                info.update({
                    "mean": float(clean.mean()),
                    "std": float(clean.std()),
                    "min": float(clean.min()),
                    "p25": float(clean.quantile(0.25)),
                    "median": float(clean.median()),
                    "p75": float(clean.quantile(0.75)),
                    "max": float(clean.max()),
                    "skewness": float(clean.skew()),
                })
        else:
            vc = series.value_counts(dropna=True)
            if len(vc) > 0:
                info["top"] = str(vc.index[0])
                info["top_freq"] = int(vc.iloc[0])
                info["top_pct"] = round(int(vc.iloc[0]) / n_total * 100, 2) if n_total else 0.0
        report[col] = info
    return report


# ---------------------------------------------------------------------------
# DataFrameWatcher
# ---------------------------------------------------------------------------

class DataFrameWatcher:
    """
    Detect changes to a DataFrame by periodically comparing snapshots.

    Useful in data pipelines to trigger downstream logic only when data changes.

    Example
    -------
    >>> watcher = DataFrameWatcher(df)
    >>> # ... later, df mutated externally ...
    >>> if watcher.has_changed(df_new):
    ...     process_update(watcher.get_diff(df_new))
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._snapshot_hash = _df_hash(df)
        self._snapshot = df.copy()
        self._change_count = 0

    def has_changed(self, df: pd.DataFrame) -> bool:
        return _df_hash(df) != self._snapshot_hash

    def get_diff(self, df: pd.DataFrame) -> DataFrameDiff:
        return DataFrameDiff(self._snapshot, df)

    def update_snapshot(self, df: pd.DataFrame) -> None:
        """Acknowledge the new state as current baseline."""
        self._snapshot_hash = _df_hash(df)
        self._snapshot = df.copy()
        self._change_count += 1

    @property
    def change_count(self) -> int:
        return self._change_count
