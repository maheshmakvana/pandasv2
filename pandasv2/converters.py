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
import numpy as np
import pandas as pd
import math
from typing import Any, Dict, List, Union, Optional, Tuple


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
            'index': df.index.tolist(),
            'data': [row.tolist() for _, row in df.iterrows()],
        }
    elif orient == 'index':
        return {idx: _row_to_json_safe(row) for idx, row in df.iterrows()}
    elif orient == 'columns':
        return {col: _series_to_json_safe(df[col]) for col in df.columns}
    elif orient == 'values':
        return df.values.tolist()
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

    # NumPy/pandas missing values
    if pd.isna(val):
        return None

    # NumPy scalars
    if isinstance(val, (np.integer, np.floating)):
        if isinstance(val, np.floating):
            if math.isnan(val):
                return None
            if math.isinf(val):
                return None
        return val.item()

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
        if numeric_data.isna().sum() == 0:
            if all(isinstance(v, (int, np.integer)) or float(v).is_integer() for v in sample):
                return 'int64'
            return 'float64'

        # Try datetime
        datetime_data = pd.to_datetime(sample, errors='coerce')
        if datetime_data.isna().sum() == 0:
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
            results.append(pandas_to_json(item, **kwargs))
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
