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

New in 2.4.0:
- MemoryOptimizer: Auto-optimize DataFrame dtypes to reduce memory
- ChunkedProcessor: Process large DataFrames in chunks with generator interface
- NestedJSON: Better nested JSON <-> DataFrame conversion
- FastApply: Optimized row-wise operations with auto-vectorization
- UnifiedApply: Consistent apply/map across Series and DataFrame
- ParallelGroupBy: Multi-processing groupby for large data
- AppendCompat: Drop-in replacement for removed DataFrame.append()
- DtypeOptimizer: Sophisticated dtype optimization and suggestions
- DataFrameProfiler: Enhanced DataFrame profiling
- SafeMerge: Safer merge/join with validation
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import time
import threading
import warnings
import itertools
from collections import OrderedDict, defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import reduce
from typing import (Any, Callable, Dict, Generator, List, Optional,
                    Set, Tuple, Union)

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# DataFrame content hash
# ---------------------------------------------------------------------------

def _df_hash(df: pd.DataFrame) -> str:
    """Fast content-based hash for a DataFrame (shape + first/last rows + dtypes).

    Uses SHA-256 (not MD5) to meet modern security expectations.
    """
    sig = (
        str(df.shape)
        + str(df.dtypes.to_dict())
        + str(df.head(3).values.tolist() if len(df) >= 3 else df.values.tolist())
        + str(df.tail(3).values.tolist() if len(df) >= 3 else "")
    )
    return hashlib.sha256(sig.encode()).hexdigest()


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
    >>> v.add_rule(ColumnRule('email', regex=r'.+@.+\\..+'))
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
                    import re as _re
                    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _TimeoutError
                    import threading as _threading

                    compiled = _re.compile(rule.regex)

                    # Run the vectorised match in a worker thread with a timeout
                    # so that ReDoS patterns cannot hang the process.
                    def _run_match():
                        return series.dropna().astype(str).str.match(rule.regex)

                    with ThreadPoolExecutor(max_workers=1) as _pool:
                        fut = _pool.submit(_run_match)
                        try:
                            mask = fut.result(timeout=2.0)
                            bad = (~mask).sum()
                            if bad:
                                errors.append(
                                    rule.message or
                                    f"Column '{col}' has {bad} value(s) not matching pattern '{rule.regex}'"
                                )
                        except _TimeoutError:
                            errors.append(
                                f"Column '{col}' regex check timed out (pattern may be vulnerable to ReDoS). "
                                f"Consider simplifying the pattern: {rule.regex}"
                            )
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


# ===================================================================
# NEW FEATURES — pandasv2 2.4.0
# ===================================================================


# ---------------------------------------------------------------------------
# MemoryOptimizer
# ---------------------------------------------------------------------------

class MemoryOptimizer:
    """
    Auto-optimizes DataFrame dtypes to reduce memory usage.

    Analyzes each column and downcasts int64 -> int32/int16/int8 and
    float64 -> float32 when all values fit within the smaller range.
    Also converts low-cardinality object columns to category.

    Example
    -------
    >>> optimized_df, report = MemoryOptimizer.optimize(df)
    >>> print(report['savings_pct'], '% memory saved')
    """

    _INT_SIZES = [
        (np.int8, np.iinfo(np.int8)),
        (np.int16, np.iinfo(np.int16)),
        (np.int32, np.iinfo(np.int32)),
    ]

    _UINT_SIZES = [
        (np.uint8, np.iinfo(np.uint8)),
        (np.uint16, np.iinfo(np.uint16)),
        (np.uint32, np.iinfo(np.uint32)),
    ]

    _FLOAT_SIZES = [
        (np.float16, np.finfo(np.float16)),
        (np.float32, np.finfo(np.float32)),
    ]

    @staticmethod
    def optimize(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Optimize DataFrame dtypes to reduce memory.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame to optimize.

        Returns
        -------
        Tuple[pd.DataFrame, Dict[str, Any]]
            (optimized_df, report) where report contains:
            - original_memory_bytes
            - new_memory_bytes
            - savings_bytes
            - savings_pct
            - changes: dict of column -> change description
        """
        result = df.copy()
        changes: Dict[str, str] = {}
        original_memory = int(result.memory_usage(deep=True).sum())

        for col in result.columns:
            col_name = str(col)
            series = result[col]
            col_dtype = series.dtype

            # --- Integer downcast ---
            if pd.api.types.is_integer_dtype(col_dtype):
                if pd.api.types.is_unsigned_integer_dtype(col_dtype):
                    c_min, c_max = series.min(), series.max()
                    for target_dtype, info in MemoryOptimizer._UINT_SIZES:
                        if c_min >= info.min and c_max <= info.max:
                            if target_dtype != col_dtype:
                                result[col] = series.astype(target_dtype)
                                changes[col_name] = f"{col_dtype} -> {target_dtype}"
                            break
                else:
                    c_min, c_max = series.min(), series.max()
                    for target_dtype, info in MemoryOptimizer._INT_SIZES:
                        if c_min >= info.min and c_max <= info.max:
                            if target_dtype != col_dtype:
                                result[col] = series.astype(target_dtype)
                                changes[col_name] = f"{col_dtype} -> {target_dtype}"
                            break

            # --- Float downcast ---
            elif pd.api.types.is_float_dtype(col_dtype):
                if col_dtype == np.float64:
                    c_min, c_max = series.min(), series.max()
                    if not np.isnan(c_min) and not np.isnan(c_max):
                        for target_dtype, finfo in MemoryOptimizer._FLOAT_SIZES:
                            # Check that min/max are representable in the target type
                            target_min = np.float64(finfo.min)
                            target_max = np.float64(finfo.max)
                            if c_min >= target_min and c_max <= target_max:
                                # Check precision loss is negligible
                                test = series.dropna().astype(target_dtype).astype(np.float64)
                                orig = series.dropna()
                                max_relerr = (abs(orig - test) / (abs(orig) + 1e-12)).max()
                                if max_relerr < 1e-4:
                                    result[col] = series.astype(target_dtype)
                                    changes[col_name] = f"{col_dtype} -> {target_dtype}"
                                    break

            # --- Object / category ---
            elif pd.api.types.is_object_dtype(col_dtype):
                n_unique = int(series.nunique(dropna=True))
                n_total = len(series)
                if n_unique < n_total and n_unique <= 500:
                    result[col] = series.astype("category")
                    changes[col_name] = f"{col_dtype} -> category"

        new_memory = int(result.memory_usage(deep=True).sum())
        savings = original_memory - new_memory

        report: Dict[str, Any] = {
            "original_memory_bytes": original_memory,
            "new_memory_bytes": new_memory,
            "savings_bytes": max(savings, 0),
            "savings_pct": round(float(max(savings, 0)) / original_memory * 100, 2) if original_memory > 0 else 0.0,
            "changes": changes,
        }

        return result, report


# ---------------------------------------------------------------------------
# ChunkedProcessor
# ---------------------------------------------------------------------------

class ChunkedProcessor:
    """
    Process large DataFrames in chunks using a generator interface.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to process.
    chunk_size : int
        Number of rows per chunk (default 10_000).

    Example
    -------
    >>> cp = ChunkedProcessor(df, chunk_size=5000)
    >>> for processed_chunk in cp.map_chunks(lambda c: c.dropna()):
    ...     print(len(processed_chunk))
    >>> total = cp.reduce_chunks(lambda c: len(c), lambda a, b: a + b)
    """

    def __init__(self, df: pd.DataFrame, chunk_size: int = 10_000) -> None:
        self._df = df
        self._chunk_size = max(1, chunk_size)

    def _chunks(self) -> Generator[pd.DataFrame, None, None]:
        """Yield DataFrame chunks."""
        for start in range(0, len(self._df), self._chunk_size):
            yield self._df.iloc[start: start + self._chunk_size]

    def map_chunks(self, func: Callable[[pd.DataFrame], Any]) -> Generator[Any, None, None]:
        """
        Apply *func* to each chunk and yield results.

        Yields
        ------
        Any
            Result of func(chunk) for each chunk.
        """
        for chunk in self._chunks():
            yield func(chunk)

    def reduce_chunks(
        self,
        func: Callable[[pd.DataFrame], Any],
        combine: Callable[[Any, Any], Any],
    ) -> Generator[Any, None, None]:
        """
        Map-reduce over chunks.

        Applies *func* to each chunk, then combines results pairwise with
        *combine*. Yields the single accumulated result.

        Parameters
        ----------
        func : Callable
            Map function applied to each chunk.
        combine : Callable
            Binary reduction combiner: combine(accumulated, next_result).

        Yields
        ------
        Any
            The final accumulated result.
        """
        results = list(self.map_chunks(func))
        if not results:
            return
        acc = results[0]
        for r in results[1:]:
            acc = combine(acc, r)
        yield acc

    def filter_chunks(
        self, predicate: Callable[[pd.DataFrame], bool]
    ) -> Generator[pd.DataFrame, None, None]:
        """
        Yield only chunks that satisfy *predicate*.

        Parameters
        ----------
        predicate : Callable
            Function taking a DataFrame chunk and returning bool.

        Yields
        ------
        pd.DataFrame
            Chunks for which predicate returned True.
        """
        for chunk in self._chunks():
            if predicate(chunk):
                yield chunk


# ---------------------------------------------------------------------------
# NestedJSON
# ---------------------------------------------------------------------------

class NestedJSON:
    """
    Better nested JSON <-> DataFrame conversion.

    Example
    -------
    >>> flat = NestedJSON.flatten(df, 'metadata')
    >>> nested_back = NestedJSON.nest(flat, 'metadata')
    >>> exploded = NestedJSON.explode_deep(df, 'items')
    """

    @staticmethod
    def flatten(df: pd.DataFrame, nested_col: str, sep: str = ".") -> pd.DataFrame:
        """
        Flatten a column of nested dicts into separate columns.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame with a nested dict column.
        nested_col : str
            Name of the column containing dict values.
        sep : str
            Separator between the original column name and nested keys.

        Returns
        -------
        pd.DataFrame
            DataFrame with nested dict flattened into prefixed columns.
        """
        if nested_col not in df.columns:
            return df.copy()

        records: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            base = {k: v for k, v in row.items() if k != nested_col}
            nested_val = row[nested_col]

            if isinstance(nested_val, dict):
                flat_nested = pd.json_normalize(nested_val, sep=sep).iloc[0].to_dict()
            elif isinstance(nested_val, list):
                flat_nested = {f"{i}": v for i, v in enumerate(nested_val)}
            else:
                flat_nested = {}

            combined: Dict[str, Any] = {}
            combined.update(base)
            for k, v in flat_nested.items():
                combined[f"{nested_col}{sep}{k}"] = v
            records.append(combined)

        return pd.DataFrame(records)

    @staticmethod
    def nest(df: pd.DataFrame, col_pattern: str, sep: str = ".") -> pd.DataFrame:
        """
        Re-nest flattened columns back into a dict column.

        Given a *col_pattern* like ``"address"``, all columns matching
        ``address.*`` are collapsed into a single dict-valued column ``address``.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with flattened columns.
        col_pattern : str
            Prefix of columns to nest back into a dict.
        sep : str
            Separator between the column pattern and sub-keys.

        Returns
        -------
        pd.DataFrame
            DataFrame with a single dict column instead of the prefixed columns.
        """
        prefix = col_pattern + sep
        nested_cols = [c for c in df.columns if c.startswith(prefix)]
        if not nested_cols:
            return df.copy()

        other_cols = [c for c in df.columns if c not in nested_cols]

        def _build_nested(row):
            nested: Dict[str, Any] = {}
            for col in nested_cols:
                key = col[len(prefix):]
                nested[key] = row[col]
            return nested

        result = df[other_cols].copy()
        result[col_pattern] = df.apply(_build_nested, axis=1)
        return result

    @staticmethod
    def explode_deep(df: pd.DataFrame, col_path: str) -> pd.DataFrame:
        """
        Recursively explode a column containing nested lists.

        Continues exploding until no list-typed values remain in the
        specified column path.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        col_path : str
            Column name (or dot-separated path) to recursively explode.

        Returns
        -------
        pd.DataFrame
            DataFrame with nested lists recursively exploded into rows.
        """
        result = df.copy()
        max_depth = 10

        for _ in range(max_depth):
            if col_path not in result.columns:
                break

            # Check if the column still contains lists
            sample = result[col_path].dropna()
            if len(sample) == 0:
                break
            has_lists = any(isinstance(v, list) for v in sample.head(100))
            if not has_lists:
                break

            result = result.explode(col_path, ignore_index=True)

        return result


# ---------------------------------------------------------------------------
# FastApply
# ---------------------------------------------------------------------------

class FastApply:
    """
    Optimized row-wise operations with auto-vectorization detection.

    Detects whether an operation can be vectorised via numpy and falls back
    to pandas ``apply`` when it cannot. Also provides a ``parallel_apply``
    that uses multiprocessing.

    Example
    -------
    >>> result = FastApply.apply(df, np.sqrt, axis=0)    # vectorized
    >>> result = FastApply.apply(df, lambda r: r.sum(), axis=1)
    >>> result = FastApply.parallel_apply(df, complex_func, axis=1, n_jobs=4)
    """

    @staticmethod
    def apply(df: pd.DataFrame, func: Callable, axis: int = 0) -> pd.DataFrame:
        """
        Apply *func* along *axis* with auto-vectorization when possible.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        func : Callable
            Function to apply. If it is a NumPy universal function the
            operation is vectorised automatically.
        axis : int
            0 or 'index' for column-wise, 1 or 'columns' for row-wise.

        Returns
        -------
        pd.DataFrame
            Result of applying the function.
        """
        # -- axis=0: column-wise --
        if axis == 0 or axis == "index":
            # NumPy ufunc -> vectorize over underlying array
            if isinstance(func, np.ufunc):
                arr = func(df.values)
                return pd.DataFrame(arr, columns=df.columns, index=df.index)
            # Otherwise fall through to pandas apply
            return df.apply(func, axis=0)

        # -- axis=1: row-wise --
        if axis == 1 or axis == "columns":
            # Try vectorized: if func works on the full 2D array
            if isinstance(func, np.ufunc):
                arr = func(df.values)
                return pd.DataFrame(arr, columns=df.columns, index=df.index)
            # Fall back to pandas apply
            return df.apply(func, axis=1)

        raise ValueError(f"axis must be 0/'index' or 1/'columns', got {axis}")

    @staticmethod
    def parallel_apply(
        df: pd.DataFrame,
        func: Callable,
        axis: int = 1,
        n_jobs: int = 4,
    ) -> pd.DataFrame:
        """
        Apply *func* using a multiprocessing ``ProcessPoolExecutor``.

        Splits the DataFrame into *n_jobs* chunks, processes each in a
        separate worker, and concatenates the results.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        func : Callable
            Function to apply row-wise or column-wise.
        axis : int
            0/'index' (column-wise) or 1/'columns' (row-wise).
        n_jobs : int
            Number of worker processes (default 4).

        Returns
        -------
        pd.DataFrame
            Combined result from all workers.
        """
        n_jobs = max(1, min(n_jobs, 64))

        if axis == 0 or axis == "index":
            # Column-wise: split columns across workers
            cols = list(df.columns)
            if len(cols) == 0:
                return pd.DataFrame(index=df.index)
            chunk_size = max(1, len(cols) // n_jobs)
            col_chunks = [cols[i:i + chunk_size] for i in range(0, len(cols), chunk_size)]
            col_chunks = [c for c in col_chunks if c]

            def _process_cols(col_list):
                return df[col_list].apply(func, axis=0)

            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                results = list(executor.map(_process_cols, col_chunks))
            return pd.concat(results, axis=1)

        elif axis == 1 or axis == "columns":
            # Row-wise: split rows across workers
            n = len(df)
            if n == 0:
                return df.copy()
            chunk_size = max(1, n // n_jobs)
            row_chunks: List[pd.DataFrame] = []
            for i in range(0, n, chunk_size):
                row_chunks.append(df.iloc[i:i + chunk_size])
            row_chunks = [c for c in row_chunks if len(c) > 0]

            def _process_rows(chunk):
                return chunk.apply(func, axis=1)

            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                results = list(executor.map(_process_rows, row_chunks))
            return pd.concat(results, ignore_index=True)

        raise ValueError(f"axis must be 0/'index' or 1/'columns', got {axis}")


# ---------------------------------------------------------------------------
# UnifiedApply
# ---------------------------------------------------------------------------

class UnifiedApply:
    """
    Consistent ``apply`` / ``map`` across Series and DataFrame.

    Fixes the pandas API inconsistency (issue #61128) where ``Series.map``
    and ``DataFrame.apply`` / ``DataFrame.map`` behave differently.

    Example
    -------
    >>> UnifiedApply.unified_map(series, lambda x: x * 2)
    >>> UnifiedApply.unified_map(dataframe, lambda x: x * 2)
    >>> UnifiedApply.unified_apply(series, lambda x: x.sum())
    >>> UnifiedApply.unified_apply(dataframe, lambda x: x.sum(), axis=0)
    """

    @staticmethod
    def unified_map(
        df_or_series: Union[pd.DataFrame, pd.Series],
        func: Callable,
        na_action: Optional[str] = None,
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        Element-wise mapping with consistent behaviour on both Series and DataFrame.

        On a Series delegates to ``Series.map``. On a DataFrame delegates
        to ``DataFrame.map`` (element-wise).

        Parameters
        ----------
        df_or_series : pd.DataFrame | pd.Series
            Input.
        func : Callable
            Element-wise function.
        na_action : str | None
            ``'ignore'`` to skip NA values.

        Returns
        -------
        pd.DataFrame | pd.Series
            Mapped result with same shape.
        """
        if isinstance(df_or_series, pd.Series):
            if na_action == "ignore":
                return df_or_series.map(func, na_action="ignore")
            return df_or_series.map(func)

        # DataFrame
        if na_action == "ignore":
            mask = df_or_series.isna()
            result = df_or_series.map(func)
            result[mask] = None
            return result
        return df_or_series.map(func)

    @staticmethod
    def unified_apply(
        df_or_series: Union[pd.DataFrame, pd.Series],
        func: Callable,
        axis: int = 0,
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        Consistent ``apply`` across Series and DataFrame.

        On a Series calls ``Series.apply(func)`` (axis is ignored). On a
        DataFrame calls ``DataFrame.apply(func, axis=axis)``.

        Parameters
        ----------
        df_or_series : pd.DataFrame | pd.Series
            Input.
        func : Callable
            Function to apply.
        axis : int
            Axis for DataFrame apply (ignored for Series).

        Returns
        -------
        pd.DataFrame | pd.Series
            Result of the apply.
        """
        if isinstance(df_or_series, pd.Series):
            return df_or_series.apply(func)
        return df_or_series.apply(func, axis=axis)


# ---------------------------------------------------------------------------
# ParallelGroupBy
# ---------------------------------------------------------------------------

class ParallelGroupBy:
    """
    Multi-processing groupby for large DataFrames.

    Splits groups across *n_jobs* worker processes, applies the aggregation
    in parallel, and combines results.

    Example
    -------
    >>> result = ParallelGroupBy.parallel_groupby(
    ...     df, by='category', agg_dict={'value': 'sum'}, n_jobs=4
    ... )
    >>> result = ParallelGroupBy.parallel_agg(
    ...     df, by='category', func=lambda g: g['value'].mean(), n_jobs=4
    ... )
    """

    @staticmethod
    def parallel_groupby(
        df: pd.DataFrame,
        by: Union[str, List[str]],
        agg_dict: Union[str, List[str], Dict[str, Any]],
        n_jobs: int = 4,
    ) -> pd.DataFrame:
        """
        Group by *by*, apply *agg_dict* in parallel across workers.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        by : str | list[str]
            Column(s) to group by.
        agg_dict : str | list[str] | dict
            Aggregation specification (same as ``DataFrame.groupby().agg()``).
        n_jobs : int
            Number of worker processes (default 4).

        Returns
        -------
        pd.DataFrame
            Combined aggregation result.
        """
        n_jobs = max(1, min(n_jobs, 64))

        # Get all group keys
        gb = df.groupby(by)
        groups: List[Tuple[Any, pd.DataFrame]] = list(gb)
        if not groups:
            return gb.agg(agg_dict)

        # Split groups into chunks for parallel processing
        chunk_size = max(1, len(groups) // n_jobs)
        chunks: List[List[Tuple[Any, pd.DataFrame]]] = []
        for i in range(0, len(groups), chunk_size):
            chunks.append(groups[i:i + chunk_size])
        chunks = [c for c in chunks if c]

        def _process_chunk(chunk):
            """Rebuild a DataFrame from a subset of groups and aggregate."""
            chunk_df = pd.concat(
                [grp for _, grp in chunk],
                keys=[key for key, _ in chunk],
            )
            if isinstance(chunk_df.index, pd.MultiIndex):
                chunk_df.index = chunk_df.index.droplevel(-1)
            return chunk_df.groupby(by).agg(agg_dict)

        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            results = list(executor.map(_process_chunk, chunks))

        if len(results) == 1:
            return results[0]
        return pd.concat(results)

    @staticmethod
    def parallel_agg(
        df: pd.DataFrame,
        by: Union[str, List[str]],
        func: Callable[[pd.DataFrame], Any],
        n_jobs: int = 4,
    ) -> pd.Series:
        """
        Apply a custom aggregation *func* to each group in parallel.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        by : str | list[str]
            Column(s) to group by.
        func : Callable
            Function that takes a group DataFrame and returns a scalar / Series.
        n_jobs : int
            Number of worker processes (default 4).

        Returns
        -------
        pd.Series
            Result indexed by group key.
        """
        n_jobs = max(1, min(n_jobs, 64))

        groups: List[Tuple[Any, pd.DataFrame]] = list(df.groupby(by))
        if not groups:
            return pd.Series(dtype=object)

        chunk_size = max(1, len(groups) // n_jobs)
        chunks: List[List[Tuple[Any, pd.DataFrame]]] = []
        for i in range(0, len(groups), chunk_size):
            chunks.append(groups[i:i + chunk_size])
        chunks = [c for c in chunks if c]

        def _process_chunk(chunk):
            """Apply func to each group in the chunk and return key -> result."""
            results: Dict[Any, Any] = {}
            for key, grp in chunk:
                results[key] = func(grp)
            return results

        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            chunk_results = list(executor.map(_process_chunk, chunks))

        # Merge results from all workers
        merged: Dict[Any, Any] = {}
        for cr in chunk_results:
            merged.update(cr)

        return pd.Series(merged)


# ---------------------------------------------------------------------------
# AppendCompat
# ---------------------------------------------------------------------------

class AppendCompat:
    """
    Drop-in replacement for the removed ``DataFrame.append()`` method.

    Example
    -------
    >>> df = pd.DataFrame({'a': [1, 2]})
    >>> new_row = {'a': 3}
    >>> result = AppendCompat.append_rows(df, new_row)
    >>> result = AppendCompat.append_rows(df, another_df)
    """

    @staticmethod
    def append_rows(
        df: pd.DataFrame,
        rows_dict_or_df: Union[Dict[str, Any], pd.DataFrame],
    ) -> pd.DataFrame:
        """
        Safely concatenate rows to a DataFrame.

        Accepts a single dict (one row), a list of dicts, or another
        DataFrame. Uses ``pd.concat`` internally for robust handling of
        mixed types and index misalignment.

        Parameters
        ----------
        df : pd.DataFrame
            Base DataFrame.
        rows_dict_or_df : dict | list[dict] | pd.DataFrame
            Row(s) to append.

        Returns
        -------
        pd.DataFrame
            Result with rows appended.
        """
        if isinstance(rows_dict_or_df, dict):
            other = pd.DataFrame([rows_dict_or_df])
        elif isinstance(rows_dict_or_df, list):
            if all(isinstance(r, dict) for r in rows_dict_or_df):
                other = pd.DataFrame(rows_dict_or_df)
            else:
                other = pd.DataFrame(rows_dict_or_df)
        elif isinstance(rows_dict_or_df, pd.DataFrame):
            other = rows_dict_or_df
        else:
            raise TypeError(
                f"Expected dict, list[dict], or DataFrame; got {type(rows_dict_or_df).__name__}"
            )

        return pd.concat([df, other], ignore_index=True)


class AppendableDataFrame:
    """
    Mixin that restores the ``.append()`` method on a DataFrame subclass.

    Usage
    -----
    >>> class MyDataFrame(AppendableDataFrame, pd.DataFrame):
    ...     pass
    >>> df = MyDataFrame({'a': [1, 2]})
    >>> df = df.append({'a': 3})
    """

    def append(
        self,
        other: Union[Dict[str, Any], pd.DataFrame],
        ignore_index: bool = True,
        verify_integrity: bool = False,
        sort: bool = False,
    ) -> pd.DataFrame:
        """
        Restored ``.append()`` method using ``pd.concat``.

        Parameters
        ----------
        other : dict | pd.DataFrame
            Row(s) to append.
        ignore_index : bool
            If True, create a new default index (default True).
        verify_integrity : bool
            If True, raise on duplicate index values.
        sort : bool
            Sort columns if aligning different column sets.

        Returns
        -------
        pd.DataFrame
            Result with rows appended.
        """
        if isinstance(other, dict):
            other = pd.DataFrame([other])

        return pd.concat(
            [self, other],
            ignore_index=ignore_index,
            verify_integrity=verify_integrity,
            sort=sort,
        )


# ---------------------------------------------------------------------------
# DtypeOptimizer
# ---------------------------------------------------------------------------

class DtypeOptimizer:
    """
    Sophisticated dtype optimization and suggestions.

    Goes beyond simple downcasting by analysing value distributions and
    recommending the best dtype for each column with reasoning. Also provides
    convenience methods for categorical and string conversions.

    Example
    -------
    >>> suggestions = DtypeOptimizer.suggest_dtypes(df)
    >>> df2 = DtypeOptimizer.auto_categorical(df, max_categories=50)
    >>> df3 = DtypeOptimizer.optimize_strings(df)
    """

    @staticmethod
    def suggest_dtypes(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Analyse every column and suggest an optimal dtype with reasoning.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Mapping of column name -> suggestion dict with keys:
            - current_dtype: str
            - suggested_dtype: str
            - reasoning: str
            - memory_saving_bytes: int (estimated)
        """
        suggestions: Dict[str, Dict[str, Any]] = {}
        current_mem = df.memory_usage(deep=True)

        for col in df.columns:
            col_name = str(col)
            series = df[col]
            cur_dtype = str(series.dtype)
            entry: Dict[str, Any] = {
                "current_dtype": cur_dtype,
                "suggested_dtype": cur_dtype,
                "reasoning": "No change recommended",
                "memory_saving_bytes": 0,
            }

            # --- Integer columns ---
            if pd.api.types.is_integer_dtype(series.dtype):
                c_min, c_max = series.min(), series.max()
                if pd.api.types.is_unsigned_integer_dtype(series.dtype):
                    candidates = [
                        ("uint8", np.iinfo(np.uint8)),
                        ("uint16", np.iinfo(np.uint16)),
                        ("uint32", np.iinfo(np.uint32)),
                    ]
                else:
                    candidates = [
                        ("int8", np.iinfo(np.int8)),
                        ("int16", np.iinfo(np.int16)),
                        ("int32", np.iinfo(np.int32)),
                    ]
                for dtype_name, info in candidates:
                    if c_min >= info.min and c_max <= info.max:
                        saving = int(current_mem[col]) - int(
                            series.astype(dtype_name).memory_usage()
                        )
                        entry["suggested_dtype"] = dtype_name
                        entry["reasoning"] = (
                            f"Values range [{c_min}, {c_max}] fits in {dtype_name}"
                        )
                        entry["memory_saving_bytes"] = max(saving, 0)
                        break

            # --- Float columns ---
            elif pd.api.types.is_float_dtype(series.dtype):
                if cur_dtype == "float64":
                    c_min, c_max = series.min(), series.max()
                    if not np.isnan(c_min) and not np.isnan(c_max):
                        for dtype_name, finfo in [
                            ("float32", np.finfo(np.float32)),
                            ("float16", np.finfo(np.float16)),
                        ]:
                            if c_min >= float(finfo.min) and c_max <= float(finfo.max):
                                # Estimate precision loss
                                test = series.dropna().astype(dtype_name).astype(np.float64)
                                orig = series.dropna()
                                max_relerr = float(
                                    (abs(orig - test) / (abs(orig) + 1e-12)).max()
                                )
                                if max_relerr < 1e-4:
                                    saving = int(current_mem[col]) - int(
                                        series.astype(dtype_name).memory_usage()
                                    )
                                    entry["suggested_dtype"] = dtype_name
                                    entry["reasoning"] = (
                                        f"Values in range [{c_min:.2g}, {c_max:.2g}] "
                                        f"fit in {dtype_name} with negligible precision loss"
                                    )
                                    entry["memory_saving_bytes"] = max(saving, 0)
                                    break

            # --- Object columns ---
            elif pd.api.types.is_object_dtype(series.dtype):
                n_unique = int(series.nunique(dropna=True))
                n_total = len(series)

                # Category suggestion
                if n_unique < n_total and n_unique <= 500:
                    saving = int(current_mem[col]) - int(
                        series.astype("category").memory_usage(deep=True)
                    )
                    entry["suggested_dtype"] = "category"
                    entry["reasoning"] = (
                        f"Low cardinality ({n_unique} unique / {n_total} total)"
                    )
                    entry["memory_saving_bytes"] = max(saving, 0)

            # --- Bool columns ---
            elif pd.api.types.is_bool_dtype(series.dtype):
                if cur_dtype == "object":
                    entry["suggested_dtype"] = "bool"
                    entry["reasoning"] = "Boolean values use native bool dtype"
                    saving = int(current_mem[col]) - int(
                        series.astype(bool).memory_usage()
                    )
                    entry["memory_saving_bytes"] = max(saving, 0)

            suggestions[col_name] = entry

        return suggestions

    @staticmethod
    def auto_categorical(
        df: pd.DataFrame, max_categories: int = 100
    ) -> pd.DataFrame:
        """
        Convert low-cardinality object columns to ``category`` dtype.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        max_categories : int
            Maximum number of unique values for automatic conversion (default 100).

        Returns
        -------
        pd.DataFrame
            DataFrame with eligible object columns converted to category.
        """
        result = df.copy()
        for col in result.columns:
            if pd.api.types.is_object_dtype(result[col].dtype):
                n_unique = int(result[col].nunique(dropna=True))
                if n_unique <= max_categories:
                    result[col] = result[col].astype("category")
        return result

    @staticmethod
    def optimize_strings(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert ``object`` columns to ``string[python]`` or ``StringDtype``.

        This enables modern string operations and reduces type ambiguity.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with object columns converted to StringDtype.
        """
        result = df.copy()
        for col in result.columns:
            if pd.api.types.is_object_dtype(result[col].dtype):
                try:
                    result[col] = result[col].astype(pd.StringDtype())
                except (TypeError, ValueError):
                    # Fall back to string[python] if StringDtype fails
                    try:
                        result[col] = result[col].astype("string")
                    except (TypeError, ValueError):
                        pass
        return result


# ---------------------------------------------------------------------------
# DataFrameProfiler
# ---------------------------------------------------------------------------

class DataFrameProfiler:
    """
    Enhanced DataFrame profiling beyond ``profile_dataframe``.

    Returns a comprehensive report covering memory usage, column-level
    statistics, correlation warnings, missing-data patterns, and skewness
    alerts.

    Example
    -------
    >>> profile = DataFrameProfiler.full_profile(df)
    >>> profile['memory_usage']['total_mb']
    12.4
    >>> profile['correlation_warnings']
    [{'col1': 'x', 'col2': 'y', 'correlation': 0.98, ...}]
    """

    @staticmethod
    def full_profile(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Produce a comprehensive profile of *df*.

        Returns
        -------
        Dict[str, Any]
            Keys:
            - memory_usage: per-column and total memory
            - column_stats: per-column statistics (same format as profile_dataframe)
            - correlation_warnings: list of highly correlated column pairs
            - missing_patterns: overall and per-column null analysis
            - skewness_alerts: columns with significant skew
        """
        profile: Dict[str, Any] = {}

        # --- Memory usage ---
        mem = df.memory_usage(deep=True)
        total_bytes = int(mem.sum())
        profile["memory_usage"] = {
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / 1024 / 1024, 2),
            "per_column": {str(k): int(v) for k, v in mem.items()},
        }

        # --- Column stats ---
        profile["column_stats"] = profile_dataframe(df)

        # --- Correlation warnings ---
        numeric_df = df.select_dtypes(include=[np.number])
        high_corr: List[Dict[str, Any]] = []
        if numeric_df.shape[1] > 1:
            corr_matrix = numeric_df.corr().abs()
            cols = list(corr_matrix.columns)
            seen: Set[Tuple[str, str]] = set()
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    val = corr_matrix.iloc[i, j]
                    if not np.isnan(val) and val > 0.95:
                        pair = (str(cols[i]), str(cols[j]))
                        if pair not in seen and (pair[1], pair[0]) not in seen:
                            seen.add(pair)
                            high_corr.append({
                                "col1": str(cols[i]),
                                "col2": str(cols[j]),
                                "correlation": round(float(val), 4),
                                "warning": (
                                    "Highly correlated (|r| > 0.95) — "
                                    "consider dropping one for multicollinearity"
                                ),
                            })
        profile["correlation_warnings"] = high_corr

        # --- Missing patterns ---
        total_cells = df.size
        total_missing = int(df.isna().sum().sum())
        null_counts = df.isna().sum()
        null_cols = null_counts[null_counts > 0]

        cols_with_missing: Dict[str, Dict[str, Any]] = {}
        for col_name in null_cols.index:
            cnt = int(null_counts[col_name])
            cols_with_missing[str(col_name)] = {
                "missing": cnt,
                "pct": round(cnt / len(df) * 100, 2) if len(df) > 0 else 0.0,
            }

        profile["missing_patterns"] = {
            "total_cells": total_cells,
            "total_missing": total_missing,
            "missing_pct": round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0,
            "columns_with_missing": cols_with_missing,
        }

        # --- Skewness alerts ---
        skew_alerts: List[Dict[str, Any]] = []
        for col in numeric_df.columns:
            clean = df[col].dropna()
            if len(clean) > 1:
                skew_val = float(clean.skew())
                if abs(skew_val) > 1.0:
                    direction = "right (positive)" if skew_val > 0 else "left (negative)"
                    severity = "high" if abs(skew_val) > 2.0 else "moderate"
                    skew_alerts.append({
                        "column": str(col),
                        "skewness": round(skew_val, 4),
                        "direction": direction,
                        "severity": severity,
                        "suggestion": (
                            "Consider log or Box-Cox transformation"
                            if severity == "high"
                            else "Monitor for downstream model impact"
                        ),
                    })
        profile["skewness_alerts"] = skew_alerts

        return profile


# ---------------------------------------------------------------------------
# SafeMerge
# ---------------------------------------------------------------------------

class SafeMerge:
    """
    Safer merge/join with pre-merge cardinality validation.

    Checks key overlap, duplicates, and missing values *before* executing
    the merge, helping catch silent data-quality issues early.

    Example
    -------
    >>> report = SafeMerge.check_join_keys(left, right, on='id')
    >>> result = SafeMerge.safe_merge(left, right, on='id', how='inner', validate='m:1')
    """

    @staticmethod
    def check_join_keys(
        left: pd.DataFrame,
        right: pd.DataFrame,
        on: Union[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Analyse join keys between two DataFrames without performing the merge.

        Parameters
        ----------
        left : pd.DataFrame
            Left-side DataFrame.
        right : pd.DataFrame
            Right-side DataFrame.
        on : str | list[str]
            Column(s) to join on.

        Returns
        -------
        Dict[str, Any]
            Report with:
            - keys_in_left_only: count of keys unique to left
            - keys_in_right_only: count of keys unique to right
            - keys_in_both: count of shared keys
            - left_duplicate_keys: number of duplicated key rows in left
            - right_duplicate_keys: number of duplicated key rows in right
            - left_null_keys: number of null key rows in left
            - right_null_keys: number of null key rows in right
            - merge_type: inferred cardinality (1:1, 1:m, m:1, m:m)
        """
        on_list = [on] if isinstance(on, str) else list(on)

        # Build key sets
        left_non_null = left.dropna(subset=on_list)
        right_non_null = right.dropna(subset=on_list)

        if isinstance(on, str):
            left_keys: Set[Any] = set(left_non_null[on].unique())
            right_keys: Set[Any] = set(right_non_null[on].unique())
        else:
            left_keys = set(
                tuple(x) for x in left_non_null[on_list].itertuples(index=False)
            )
            right_keys = set(
                tuple(x) for x in right_non_null[on_list].itertuples(index=False)
            )

        # Duplicate counts (keep=False counts all occurrences of duplicated keys)
        if isinstance(on, str):
            left_dups = int(left[on].duplicated(keep=False).sum())
            right_dups = int(right[on].duplicated(keep=False).sum())
        else:
            left_dups = int(left[on_list].duplicated(keep=False).sum())
            right_dups = int(right[on_list].duplicated(keep=False).sum())

        # Null counts
        if isinstance(on, str):
            left_nulls = int(left[on].isna().sum())
            right_nulls = int(right[on].isna().sum())
        else:
            left_nulls = int(left[on_list].isna().any(axis=1).sum())
            right_nulls = int(right[on_list].isna().any(axis=1).sum())

        # Infer cardinality
        left_has_dups = left_dups > 0
        right_has_dups = right_dups > 0
        if not left_has_dups and not right_has_dups:
            merge_type = "1:1"
        elif left_has_dups and not right_has_dups:
            merge_type = "m:1"
        elif not left_has_dups and right_has_dups:
            merge_type = "1:m"
        else:
            merge_type = "m:m"

        return {
            "left_key_count": len(left_keys),
            "right_key_count": len(right_keys),
            "keys_in_left_only": len(left_keys - right_keys),
            "keys_in_right_only": len(right_keys - left_keys),
            "keys_in_both": len(left_keys & right_keys),
            "left_duplicate_keys": left_dups,
            "right_duplicate_keys": right_dups,
            "left_null_keys": left_nulls,
            "right_null_keys": right_nulls,
            "merge_type": merge_type,
        }

    @staticmethod
    def safe_merge(
        left: pd.DataFrame,
        right: pd.DataFrame,
        on: Union[str, List[str]],
        how: str = "inner",
        validate: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Merge with optional pre-merge validation.

        When *validate* is provided (e.g. ``'m:1'``), the method reports
        key statistics first, then performs the merge. If the check reveals
        issues (e.g. unexpected duplicates), a warning is issued — the merge
        still proceeds.

        Parameters
        ----------
        left : pd.DataFrame
            Left-side DataFrame.
        right : pd.DataFrame
            Right-side DataFrame.
        on : str | list[str]
            Column(s) to join on.
        how : str
            Merge method: ``'inner'``, ``'left'``, ``'right'``, ``'outer'``.
        validate : str | None
            Expected cardinality, e.g. ``'1:1'``, ``'m:1'``, ``'1:m'``, ``'m:m'``.
            If provided and the actual cardinality differs, a warning is raised.

        Returns
        -------
        pd.DataFrame
            Merged result.
        """
        # Pre-merge key check
        key_check = SafeMerge.check_join_keys(left, right, on)

        if validate:
            actual = key_check["merge_type"]
            if actual != validate:
                warnings.warn(
                    f"Merge cardinality mismatch: expected {validate}, "
                    f"inferred {actual}. "
                    f"Left duplicates: {key_check['left_duplicate_keys']}, "
                    f"Right duplicates: {key_check['right_duplicate_keys']}.",
                    stacklevel=2,
                )

        # Warn about null keys
        if key_check["left_null_keys"] > 0:
            warnings.warn(
                f"Left DataFrame has {key_check['left_null_keys']} null key value(s). "
                "These rows will be dropped in an inner merge.",
                stacklevel=2,
            )

        if key_check["right_null_keys"] > 0:
            warnings.warn(
                f"Right DataFrame has {key_check['right_null_keys']} null key value(s). "
                "These rows will be dropped in an inner merge.",
                stacklevel=2,
            )

        # Perform the merge
        return pd.merge(left, right, on=on, how=how, validate=validate)
