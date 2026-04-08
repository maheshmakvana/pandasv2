"""
Core pandas2 serialization and deserialization functionality.

Handles:
- JSON encoding of pandas/NumPy types (int64, float64, NaT, NaN, Categorical, etc.)
- JSON decoding with type preservation
- Metadata storage for round-trip serialization
- DataFrame, Series, and Index support

Built by Mahesh Makvana
"""

import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, date, time, timedelta
from typing import Any, Dict, List, Optional, Union


class JSONEncoder(json.JSONEncoder):
    """
    Enhanced JSON encoder that handles pandas and NumPy types.

    Supports:
    - NumPy scalars (int64, float64, uint32, etc.)
    - pandas types (NaT, Timedelta, Period, Interval, Categorical)
    - pandas DataFrame and Series
    - datetime objects and timedeltas
    - NaN, Infinity, -Infinity

    Usage:
        >>> import json
        >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [1.1, 2.2, 3.3]})
        >>> json.dumps(df, cls=pandas2.JSONEncoder)
    """

    def default(self, obj: Any) -> Any:
        """Convert non-JSON-serializable objects to serializable format."""

        # NumPy scalar types
        if isinstance(obj, (np.integer, np.floating)):
            # Handle NaN and Infinity
            if isinstance(obj, np.floating):
                if math.isnan(obj):
                    return None
                if math.isinf(obj):
                    return float('inf') if obj > 0 else float('-inf')
            return obj.item()

        # NumPy array
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        # pandas types
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Timedelta):
            return obj.total_seconds()
        if isinstance(obj, pd.Period):
            return str(obj)
        if isinstance(obj, pd.Interval):
            return {'left': obj.left, 'right': obj.right, 'closed': obj.closed}
        if isinstance(obj, pd.Categorical):
            return obj.astype(str).tolist()
        if pd.isna(obj):
            return None

        # pandas DataFrame
        if isinstance(obj, pd.DataFrame):
            return {
                '__type__': 'DataFrame',
                'data': obj.to_dict(orient='records'),
                'columns': obj.columns.tolist(),
                'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
                'dtypes': {col: str(dtype) for col, dtype in obj.dtypes.items()},
            }

        # pandas Series
        if isinstance(obj, pd.Series):
            return {
                '__type__': 'Series',
                'data': obj.tolist(),
                'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
                'dtype': str(obj.dtype),
                'name': obj.name,
            }

        # pandas Index
        if isinstance(obj, pd.Index):
            return {
                '__type__': 'Index',
                'data': obj.tolist(),
                'name': obj.name,
            }

        # Standard datetime types
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return obj.total_seconds()

        # Fall back to parent class
        return super().default(obj)


class JSONDecoder(json.JSONDecoder):
    """
    Enhanced JSON decoder that reconstructs pandas and NumPy types.

    Supports reconstructing:
    - pandas DataFrame with correct dtypes
    - pandas Series with correct dtype
    - pandas Index
    - datetime objects
    - Original NumPy dtypes

    Usage:
        >>> import json
        >>> json_str = '{"__type__": "DataFrame", ...}'
        >>> json.loads(json_str, cls=pandas2.JSONDecoder)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj: Dict) -> Any:
        """Reconstruct pandas objects from their serialized form."""

        if not isinstance(obj, dict):
            return obj

        # Reconstruct DataFrame
        if obj.get('__type__') == 'DataFrame':
            data = obj.get('data', [])
            columns = obj.get('columns', [])
            dtypes = obj.get('dtypes', {})
            index = obj.get('index')

            df = pd.DataFrame(data, columns=columns)

            # Restore dtypes
            for col, dtype_str in dtypes.items():
                try:
                    df[col] = df[col].astype(dtype_str)
                except (ValueError, TypeError):
                    pass  # Keep as is if conversion fails

            # Restore index if provided
            if index:
                df.index = index

            return df

        # Reconstruct Series
        if obj.get('__type__') == 'Series':
            data = obj.get('data', [])
            index = obj.get('index')
            dtype = obj.get('dtype', 'object')
            name = obj.get('name')

            series = pd.Series(data, index=index, dtype=dtype, name=name)
            return series

        # Reconstruct Index
        if obj.get('__type__') == 'Index':
            data = obj.get('data', [])
            name = obj.get('name')
            return pd.Index(data, name=name)

        return obj


def to_json(obj: Any, **kwargs) -> str:
    """
    Serialize pandas/NumPy objects to JSON string.

    Args:
        obj: DataFrame, Series, or any JSON-serializable object
        **kwargs: Passed to json.dumps()

    Returns:
        JSON string

    Raises:
        TypeError: If object cannot be JSON serialized

    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> json_str = pandas2.to_json(df)
        >>> df_restored = pandas2.from_json(json_str)
    """
    return json.dumps(obj, cls=JSONEncoder, **kwargs)


def from_json(json_str: str, **kwargs) -> Any:
    """
    Deserialize JSON string to pandas/Python objects.

    Reconstructs original types (DataFrames, Series, etc.) from JSON.

    Args:
        json_str: JSON string to deserialize
        **kwargs: Passed to json.loads()

    Returns:
        Deserialized object (DataFrame, Series, dict, list, etc.)

    Example:
        >>> json_str = '{"__type__": "DataFrame", "data": [...]}'
        >>> df = pandas2.from_json(json_str)
    """
    return json.loads(json_str, cls=JSONDecoder, **kwargs)


def serialize(obj: Any, include_metadata: bool = True) -> Dict:
    """
    Serialize object with optional metadata for reconstruction.

    Args:
        obj: Object to serialize (DataFrame, Series, etc.)
        include_metadata: If True, includes type info and metadata

    Returns:
        Dictionary with serialized data and metadata

    Example:
        >>> df = pd.DataFrame({'a': pd.date_range('2024-01-01', periods=3)})
        >>> serialized = pandas2.serialize(df)
        >>> reconstructed = pandas2.deserialize(serialized)
    """
    if isinstance(obj, pd.DataFrame):
        return {
            '__type__': 'DataFrame',
            'data': json.loads(to_json(obj.to_dict(orient='records'))),
            'columns': obj.columns.tolist(),
            'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
            'dtypes': {col: str(dtype) for col, dtype in obj.dtypes.items()} if include_metadata else {},
            'metadata': {
                'shape': obj.shape,
                'memory_usage': int(obj.memory_usage(deep=True).sum()),
            } if include_metadata else {},
        }

    if isinstance(obj, pd.Series):
        return {
            '__type__': 'Series',
            'data': json.loads(to_json(obj.tolist())),
            'index': obj.index.tolist() if not isinstance(obj.index, pd.RangeIndex) else None,
            'dtype': str(obj.dtype) if include_metadata else 'object',
            'name': obj.name,
            'metadata': {
                'shape': obj.shape,
                'memory_usage': int(obj.memory_usage(deep=True)),
            } if include_metadata else {},
        }

    return json.loads(to_json(obj))


def deserialize(data: Dict, strict: bool = False) -> Any:
    """
    Reconstruct object from serialized form.

    Args:
        data: Dictionary with '__type__' key indicating object type
        strict: If True, raises error on dtype mismatch; if False, coerces

    Returns:
        Reconstructed object (DataFrame, Series, etc.)

    Raises:
        ValueError: If strict=True and dtype cannot be restored

    Example:
        >>> serialized = pandas2.serialize(df)
        >>> df_restored = pandas2.deserialize(serialized)
    """
    if not isinstance(data, dict):
        return data

    obj_type = data.get('__type__')

    if obj_type == 'DataFrame':
        df_data = data.get('data', [])
        columns = data.get('columns', [])
        index = data.get('index')
        dtypes = data.get('dtypes', {})

        df = pd.DataFrame(df_data, columns=columns)

        # Restore dtypes
        for col, dtype_str in dtypes.items():
            try:
                df[col] = df[col].astype(dtype_str)
            except (ValueError, TypeError) as e:
                if strict:
                    raise ValueError(f"Cannot convert column '{col}' to dtype '{dtype_str}': {e}")

        if index:
            df.index = index

        return df

    if obj_type == 'Series':
        series_data = data.get('data', [])
        index = data.get('index')
        dtype = data.get('dtype', 'object')
        name = data.get('name')

        try:
            return pd.Series(series_data, index=index, dtype=dtype, name=name)
        except (ValueError, TypeError) as e:
            if strict:
                raise ValueError(f"Cannot create Series with dtype '{dtype}': {e}")
            return pd.Series(series_data, index=index, name=name)

    if obj_type == 'Index':
        return pd.Index(data.get('data', []), name=data.get('name'))

    return data


class DataFrameWrapper:
    """
    Enhanced pandas DataFrame wrapper with built-in JSON serialization.

    Wraps a DataFrame and provides convenient JSON methods.

    Usage:
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> wrapped = pandas2.DataFrameWrapper(df)
        >>> json_str = wrapped.to_json()
        >>> df_restored = wrapped.from_json(json_str)
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize with a pandas DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df)}")
        self.df = df

    def to_json(self, **kwargs) -> str:
        """Convert to JSON string."""
        return to_json(self.df, **kwargs)

    def to_dict(self, **kwargs) -> Dict:
        """Convert to dictionary with metadata."""
        return serialize(self.df, **kwargs)

    @staticmethod
    def from_json(json_str: str) -> 'DataFrameWrapper':
        """Create from JSON string."""
        df = from_json(json_str)
        if not isinstance(df, pd.DataFrame):
            raise ValueError("JSON does not represent a DataFrame")
        return DataFrameWrapper(df)

    @staticmethod
    def from_dict(data: Dict) -> 'DataFrameWrapper':
        """Create from dictionary with metadata."""
        df = deserialize(data)
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Data does not represent a DataFrame")
        return DataFrameWrapper(df)

    def __repr__(self) -> str:
        return f"DataFrameWrapper({self.df.shape[0]} rows, {self.df.shape[1]} cols)"

    def __getattr__(self, name: str) -> Any:
        """Delegate to underlying DataFrame."""
        return getattr(self.df, name)
