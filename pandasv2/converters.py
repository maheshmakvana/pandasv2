"""
Type conversion utilities for pandas and NumPy data.

Provides:
- pandas_to_json(): Convert DataFrame/Series to JSON-safe format
- json_to_pandas(): Reconstruct DataFrames from JSON
- Type inference and safe casting
- Batch conversion utilities
- Metadata preservation

Built by Mahesh Makvana
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


_PANDASV2_TAG_KEY = "__pandasv2__"
_PANDASV2_FLOAT_TAG = "float"


def pandas_to_json(
    obj: Union[pd.DataFrame, pd.Series],
    orient: str = 'records',
    include_metadata: bool = False,
    handle_na: str = 'null',
) -> Union[str, Dict, List]:
    """
    Convert pandas DataFrame or Series to JSON-safe format.

    Args:
        obj: DataFrame or Series to convert
        orient: Output orientation ('records', 'split', 'index', 'columns', 'values')
        include_metadata: If True, includes dtypes and index info
        handle_na: How to handle NaN/NaT ('null', 'drop', 'forward_fill', 'back_fill')

    Returns:
        JSON-safe dictionary or string

    Raises:
        TypeError: If obj is not DataFrame or Series
        ValueError: If orient or handle_na is invalid

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, np.nan], 'b': ['x', 'y', 'z']})
        >>> json_data = pandasv2.pandas_to_json(df, orient='records')
    """
    if not isinstance(obj, (pd.DataFrame, pd.Series)):
        raise TypeError(f"Expected DataFrame or Series, got {type(obj)}")

    if handle_na == 'forward_fill':
        obj = obj.fillna(method='ffill')
    elif handle_na == 'back_fill':
        obj = obj.fillna(method='bfill')
    elif handle_na == 'drop':
        obj = obj.dropna()

    if isinstance(obj, pd.Series):
        data = _series_to_json_safe(obj)
    else:
        data = _dataframe_to_json_safe(obj, orient=orient)

    if include_metadata:
        if isinstance(obj, pd.DataFrame):
            return {
                'data': data,
                'metadata': {
                    'shape': obj.shape,
                    'columns': obj.columns.tolist(),
                    'dtypes': {col: str(dtype) for col, dtype in obj.dtypes.items()},
                    'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
                }
            }
        else:
            return {
                'data': data,
                'metadata': {
                    'dtype': str(obj.dtype),
                    'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
                    'name': obj.name,
                }
            }

    return data


def _dataframe_to_json_safe(df: pd.DataFrame, orient: str = 'records') -> Union[Dict, List]:
    """Convert DataFrame to JSON-safe format (internal)."""
    if orient == 'records':
        return [_row_to_json_safe(row) for _, row in df.iterrows()]
    elif orient == 'split':
        return {
            'columns': df.columns.tolist(),
            'index': [_to_json_safe(v) for v in df.index.tolist()],
            'data': [[_to_json_safe(v) for v in row.tolist()] for _, row in df.iterrows()],
        }
    elif orient == 'index':
        # JSON object keys must be strings; use a stable string form for the index key.
        return {str(_to_json_safe(idx)): _row_to_json_safe(row) for idx, row in df.iterrows()}
    elif orient == 'columns':
        return {col: _series_to_json_safe(df[col]) for col in df.columns}
    elif orient == 'values':
        return [[_to_json_safe(v) for v in row] for row in df.values.tolist()]
    else:
        raise ValueError(f"Invalid orient: {orient}")


def _row_to_json_safe(row: pd.Series) -> Dict:
    """Convert a pandas Series row to JSON-safe dict."""
    return {k: _to_json_safe(v) for k, v in row.items()}


def _series_to_json_safe(series: pd.Series) -> List:
    """Convert pandas Series to JSON-safe list."""
    return [_to_json_safe(v) for v in series]


def _to_json_safe(val: Any) -> Any:
    """Convert single value to JSON-safe format."""
    # Handle None
    if val is None:
        return None

    # Non-finite floats must not be emitted as NaN/Infinity (invalid JSON).
    # Encode them as tagged objects for stable round-trip.
    if isinstance(val, (float, np.floating)):
        float_val = float(val)
        if math.isnan(float_val):
            return None
        if math.isinf(float_val):
            return {_PANDASV2_TAG_KEY: _PANDASV2_FLOAT_TAG, "value": "inf" if float_val > 0 else "-inf"}
        return float_val

    # NumPy scalars
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)

    # NumPy/pandas missing values (after float handling so NaN can be losslessly tagged)
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass

    # pandas types
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    if isinstance(val, pd.Timedelta):
        return val.total_seconds()
    if isinstance(val, pd.Period):
        return str(val)
    if isinstance(val, pd.Categorical):
        return str(val)

    # Standard types
    if isinstance(val, (str, int, float, bool)):
        return val

    # Default: convert to string
    return str(val)


def _from_json_safe(val: Any) -> Any:
    """
    Decode a value produced by _to_json_safe.

    This is intentionally minimal: it restores tagged non-finite floats.
    Datetime/Timedelta restoration is handled at the column-level using dtype metadata.
    """
    if isinstance(val, dict) and val.get(_PANDASV2_TAG_KEY) == _PANDASV2_FLOAT_TAG:
        tag_value = val.get("value")
        if tag_value == "nan":
            return float("nan")
        if tag_value == "inf":
            return float("inf")
        if tag_value == "-inf":
            return float("-inf")
        return float("nan")
    return val


def _walk_decode_json_safe(obj: Any) -> Any:
    """Recursively decode tagged values in JSON-safe structures."""
    if isinstance(obj, list):
        return [_walk_decode_json_safe(v) for v in obj]
    if isinstance(obj, dict):
        decoded = _from_json_safe(obj)
        if decoded is not obj:
            return decoded
        return {k: _walk_decode_json_safe(v) for k, v in obj.items()}
    return obj


def dataframe_to_json_safe_str(
    df: pd.DataFrame,
    orient: str = "records",
    **json_kwargs: Any,
) -> str:
    """
    Serialize a DataFrame to strict JSON safe for web APIs.

    The payload includes dtype metadata for stable round-trip via
    :func:`dataframe_from_json_safe_str`.
    """
    payload = {
        "__type__": "DataFrame",
        "orient": orient,
        "data": _dataframe_to_json_safe(df, orient=orient),
        "columns": df.columns.tolist(),
        "index": [_to_json_safe(v) for v in df.index.tolist()] if not isinstance(df.index, pd.RangeIndex) else None,
        "index_dtype": str(df.index.dtype) if not isinstance(df.index, pd.RangeIndex) else None,
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
    return json.dumps(payload, allow_nan=False, **json_kwargs)


def series_to_json_safe_str(
    series: pd.Series,
    **json_kwargs: Any,
) -> str:
    """Serialize a Series to strict JSON safe for web APIs (with dtype metadata)."""
    payload = {
        "__type__": "Series",
        "data": _series_to_json_safe(series),
        "index": [_to_json_safe(v) for v in series.index.tolist()] if not isinstance(series.index, pd.RangeIndex) else None,
        "index_dtype": str(series.index.dtype) if not isinstance(series.index, pd.RangeIndex) else None,
        "dtype": str(series.dtype),
        "name": series.name,
    }
    return json.dumps(payload, allow_nan=False, **json_kwargs)


def dataframe_from_json_safe_str(json_str: str) -> pd.DataFrame:
    """Reconstruct a DataFrame from `dataframe_to_json_safe_str` output."""
    payload = json.loads(json_str)
    if isinstance(payload, dict) and payload.get("__type__") == "DataFrame":
        orient = payload.get("orient", "records")
        dtypes = payload.get("dtypes", {}) or {}
        index = _walk_decode_json_safe(payload.get("index"))
        index_dtype = payload.get("index_dtype")

        data = _walk_decode_json_safe(payload.get("data", []))
        columns = payload.get("columns", [])

        if orient == "records":
            df = pd.DataFrame(data, columns=columns)
        elif orient == "split":
            # split payload is already a dict with columns/index/data
            if isinstance(data, dict):
                split_cols = data.get("columns", columns)
                split_index = _walk_decode_json_safe(data.get("index", index))
                split_data = _walk_decode_json_safe(data.get("data", []))
                df = pd.DataFrame(split_data, columns=split_cols)
                if split_index is not None:
                    df.index = split_index
            else:
                df = pd.DataFrame(data, columns=columns)
        else:
            # Keep reconstruction predictable: only records/split are guaranteed round-trippable.
            df = pd.DataFrame(data, columns=columns)

        if index is not None:
            df.index = _restore_index_like(index, index_dtype)

        _restore_dataframe_dtypes(df, dtypes)
        return df

    # Back-compat: allow old pandasv2 JSONEncoder payloads
    if isinstance(payload, dict) and payload.get("__type__") == "DataFrame":
        df = pd.DataFrame(payload.get("data", []), columns=payload.get("columns", []))
        if payload.get("index") is not None:
            df.index = payload["index"]
        _restore_dataframe_dtypes(df, payload.get("dtypes", {}) or {})
        return df

    raise ValueError("JSON does not represent a pandasv2 DataFrame payload")


def series_from_json_safe_str(json_str: str) -> pd.Series:
    """Reconstruct a Series from `series_to_json_safe_str` output."""
    payload = json.loads(json_str)
    if not (isinstance(payload, dict) and payload.get("__type__") == "Series"):
        raise ValueError("JSON does not represent a pandasv2 Series payload")

    data = _walk_decode_json_safe(payload.get("data", []))
    index = _walk_decode_json_safe(payload.get("index"))
    index_dtype = payload.get("index_dtype")
    dtype = payload.get("dtype", "object")
    name = payload.get("name")

    index_restored = _restore_index_like(index, index_dtype) if index is not None else None
    series = pd.Series(data, index=index_restored, name=name)
    series = _restore_series_dtype(series, dtype)
    return series


def _restore_series_dtype(series: pd.Series, dtype_str: str) -> pd.Series:
    """Restore Series dtype using dtype metadata (minimal safe behavior)."""
    if "datetime64" in dtype_str:
        return pd.to_datetime(series, errors="coerce")
    if "timedelta64" in dtype_str:
        return pd.to_timedelta(series, unit="s")
    try:
        return series.astype(dtype_str)
    except (TypeError, ValueError):
        return series


def _restore_dataframe_dtypes(df: pd.DataFrame, dtypes: Dict[str, str]) -> None:
    """Restore DataFrame dtypes in-place (minimal safe behavior)."""
    for col, dtype_str in dtypes.items():
        if col not in df.columns:
            continue
        if "datetime64" in dtype_str:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            continue
        if "timedelta64" in dtype_str:
            df[col] = pd.to_timedelta(df[col], unit="s")
            continue
        try:
            df[col] = df[col].astype(dtype_str)
        except (TypeError, ValueError):
            continue


def _restore_index_like(values: Any, dtype_str: Optional[str]) -> Any:
    """Restore index-like values based on dtype metadata (best-effort)."""
    if dtype_str is None:
        return values
    if "datetime64" in dtype_str:
        return pd.to_datetime(values, errors="coerce")
    if "timedelta64" in dtype_str:
        return pd.to_timedelta(values, unit="s")
    return values


def json_to_pandas(
    data: Union[str, Dict, List],
    dtypes: Optional[Dict[str, str]] = None,
) -> Union[pd.DataFrame, pd.Series]:
    """
    Reconstruct pandas DataFrame or Series from JSON-safe format.

    Args:
        data: JSON data (string, dict, or list)
        dtypes: Optional dict mapping column names to dtype strings

    Returns:
        DataFrame or Series

    Raises:
        ValueError: If data cannot be converted

    Example:
        >>> json_data = {'data': [{'a': 1, 'b': 'x'}]}
        >>> df = pandasv2.json_to_pandas(json_data)
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Handle metadata format
    if isinstance(data, dict) and 'data' in data and 'metadata' in data:
        actual_data = data['data']
        metadata = data['metadata']
        dtypes = metadata.get('dtypes', dtypes)
    else:
        actual_data = data

    # Convert to DataFrame or Series
    if isinstance(actual_data, list):
        if not actual_data:
            return pd.DataFrame()
        if isinstance(actual_data[0], dict):
            df = pd.DataFrame(actual_data)
        else:
            df = pd.DataFrame(actual_data)
    elif isinstance(actual_data, dict):
        df = pd.DataFrame(actual_data)
    else:
        raise ValueError(f"Cannot convert data of type {type(actual_data)}")

    # Apply dtypes if provided
    if dtypes:
        for col, dtype_str in dtypes.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype_str)
                except (ValueError, TypeError):
                    pass

    return df


def dataframe_to_records(
    df: pd.DataFrame,
    index: bool = False,
    na_value: Any = None,
) -> List[Dict]:
    """
    Convert DataFrame to list of records (dicts) with JSON-safe values.

    Args:
        df: Input DataFrame
        index: If True, include index as '__index__' column
        na_value: Value to use for missing values

    Returns:
        List of dictionaries

    Example:
        >>> df = pd.DataFrame({'a': [1, 2], 'b': [np.nan, 4.0]})
        >>> records = pandasv2.dataframe_to_records(df)
    """
    records = []
    for idx, row in df.iterrows():
        record = {col: _to_json_safe(val) for col, val in row.items()}
        if index:
            record['__index__'] = idx
        records.append(record)
    return records


def series_to_list(
    series: pd.Series,
    na_value: Any = None,
) -> List:
    """
    Convert Series to JSON-safe list.

    Args:
        series: Input Series
        na_value: Value to use for missing values

    Returns:
        List of values

    Example:
        >>> s = pd.Series([1, np.nan, 3])
        >>> lst = pandasv2.series_to_list(s)
    """
    return [_to_json_safe(v) for v in series]


def infer_dtype(
    data: Union[List, pd.Series, np.ndarray],
    sample_size: int = 100,
) -> str:
    """
    Infer pandas dtype for data.

    Args:
        data: Data to analyze
        sample_size: Number of rows to sample (for large datasets)

    Returns:
        dtype string ('int64', 'float64', 'object', 'datetime64[ns]', etc.)

    Example:
        >>> dtype = pandasv2.infer_dtype([1, 2, 3])
        'int64'
    """
    if isinstance(data, pd.Series):
        return str(data.dtype)

    if isinstance(data, np.ndarray):
        return str(data.dtype)

    if not isinstance(data, list):
        return 'object'

    if not data:
        return 'object'

    # Sample the data
    sample = data[:sample_size] if len(data) > sample_size else data

    # Try to infer dtype
    try:
        # Try numeric
        numeric_data = pd.to_numeric(sample, errors='coerce')
        if int(np.sum(pd.isna(numeric_data))) == 0:
            if all(isinstance(v, (int, np.integer)) or float(v).is_integer() for v in sample):
                return 'int64'
            return 'float64'

        # Try datetime
        datetime_data = pd.to_datetime(sample, errors='coerce')
        if int(np.sum(pd.isna(datetime_data))) == 0:
            return 'datetime64[ns]'

        # Default to object
        return 'object'
    except Exception:
        return 'object'


def safe_cast(
    data: Union[List, pd.Series, np.ndarray],
    dtype: str,
    errors: str = 'coerce',
) -> Union[pd.Series, np.ndarray]:
    """
    Safely cast data to target dtype.

    Args:
        data: Data to cast
        dtype: Target dtype string
        errors: How to handle errors ('coerce', 'ignore', 'raise')

    Returns:
        Casted data (Series or ndarray)

    Raises:
        ValueError: If errors='raise' and cast fails

    Example:
        >>> result = pandasv2.safe_cast(['1', '2', '3'], 'int64')
    """
    if isinstance(data, pd.Series):
        try:
            return data.astype(dtype)
        except (ValueError, TypeError) as e:
            if errors == 'raise':
                raise ValueError(f"Cannot cast to {dtype}: {e}")
            elif errors == 'coerce':
                return pd.to_numeric(data, errors='coerce') if 'int' in dtype or 'float' in dtype else data.astype('object')
            else:
                return data

    if isinstance(data, np.ndarray):
        try:
            return data.astype(dtype)
        except (ValueError, TypeError) as e:
            if errors == 'raise':
                raise ValueError(f"Cannot cast to {dtype}: {e}")
            else:
                return data

    # Convert list to Series and cast
    series = pd.Series(data)
    return safe_cast(series, dtype, errors=errors)


def batch_convert(
    data: List[Union[pd.DataFrame, pd.Series]],
    operation: str = 'to_json',
    **kwargs
) -> List[Union[str, Dict]]:
    """
    Batch convert multiple DataFrames or Series.

    Args:
        data: List of DataFrames/Series to convert
        operation: Operation to perform ('to_json', 'to_dict', 'to_records')
        **kwargs: Passed to conversion function

    Returns:
        List of converted objects

    Example:
        >>> dfs = [df1, df2, df3]
        >>> json_strs = pandasv2.batch_convert(dfs, operation='to_json')
    """
    results = []
    for item in data:
        if operation == 'to_json':
            results.append(json.dumps(pandas_to_json(item, **kwargs), allow_nan=False))
        elif operation == 'to_dict':
            from .core import serialize
            results.append(serialize(item, **kwargs))
        elif operation == 'to_records':
            if isinstance(item, pd.DataFrame):
                results.append(dataframe_to_records(item, **kwargs))
            else:
                results.append(series_to_list(item, **kwargs))
        else:
            raise ValueError(f"Unknown operation: {operation}")
    return results


def preserve_metadata(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
) -> pd.DataFrame:
    """
    Attach metadata to DataFrame for round-trip serialization.

    Args:
        df: Input DataFrame
        metadata: Metadata dict to attach

    Returns:
        DataFrame with metadata attached

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> meta = {'source': 'api', 'version': 1}
        >>> df_with_meta = pandasv2.preserve_metadata(df, meta)
        >>> retrieved_meta = df_with_meta.attrs
    """
    df.attrs.update(metadata)
    return df
