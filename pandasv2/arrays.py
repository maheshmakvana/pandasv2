"""
pd.arrays namespace for pandasv2.

Mirrors and extends pandas.arrays with all extension array types plus
pandasv2-specific utilities:

Standard (re-exported from pandas.arrays):
  ArrowExtensionArray    (pandas >= 1.5 with pyarrow installed)
  BooleanArray
  Categorical
  DatetimeArray
  FloatingArray
  IntegerArray
  IntervalArray
  MaskedArray
  NumpyExtensionArray
  PeriodArray
  SparseArray
  StringArray
  TimedeltaArray

pandasv2 extras:
  to_arrow()         — Convert DataFrame/Series → PyArrow Table/ChunkedArray
  from_arrow()       — Convert PyArrow Table/Array → DataFrame/Series
  to_numpy_safe()    — Convert extension array to NumPy, coercing NA → value

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Optional, Union


# ---------------------------------------------------------------------------
# Re-export all pandas.arrays members
# ---------------------------------------------------------------------------

BooleanArray = _pd.arrays.BooleanArray
DatetimeArray = _pd.arrays.DatetimeArray
FloatingArray = _pd.arrays.FloatingArray
IntegerArray = _pd.arrays.IntegerArray
IntervalArray = _pd.arrays.IntervalArray
MaskedArray = getattr(_pd.arrays, 'MaskedArray', None)
NumpyExtensionArray = getattr(_pd.arrays, 'NumpyExtensionArray',
                               getattr(_pd.arrays, 'PandasArray', None))
PeriodArray = _pd.arrays.PeriodArray
SparseArray = _pd.arrays.SparseArray
StringArray = _pd.arrays.StringArray
TimedeltaArray = _pd.arrays.TimedeltaArray
Categorical = _pd.Categorical  # lives in pd, not pd.arrays, but logically here

# ArrowExtensionArray — requires pyarrow
try:
    ArrowExtensionArray = _pd.arrays.ArrowExtensionArray
except AttributeError:
    ArrowExtensionArray = None


# ---------------------------------------------------------------------------
# pandasv2 extras
# ---------------------------------------------------------------------------

def to_arrow(obj, preserve_index: bool = True):
    """
    Convert a pandasv2/pandas DataFrame or Series to a PyArrow Table or ChunkedArray.

    Requires pyarrow to be installed: pip install pyarrow

    Args:
        obj: DataFrame or Series to convert
        preserve_index: Include the index in the Arrow table (DataFrames only)

    Returns:
        pyarrow.Table for DataFrame, pyarrow.ChunkedArray for Series

    Example:
        >>> import pandasv2 as pd
        >>> table = pd.arrays.to_arrow(df)
        >>> chunked = pd.arrays.to_arrow(series)
    """
    try:
        import pyarrow as pa
    except ImportError:
        raise ImportError(
            "PyArrow is required for to_arrow(). "
            "Install with: pip install pyarrow"
        )

    if isinstance(obj, _pd.DataFrame):
        return pa.Table.from_pandas(obj, preserve_index=preserve_index)
    elif isinstance(obj, _pd.Series):
        return pa.chunked_array([pa.array(obj.to_numpy(dtype=object, na_value=None))])
    else:
        raise TypeError(f"Expected DataFrame or Series, got {type(obj)}")


def from_arrow(obj) -> Union[_pd.DataFrame, _pd.Series]:
    """
    Convert a PyArrow Table or Array/ChunkedArray to a pandasv2 DataFrame or Series.

    Requires pyarrow to be installed.

    Args:
        obj: pyarrow.Table, pyarrow.Array, or pyarrow.ChunkedArray

    Returns:
        pandasv2 DataFrame (from Table) or pandasv2 Series (from Array)

    Example:
        >>> df = pd.arrays.from_arrow(arrow_table)
        >>> series = pd.arrays.from_arrow(chunked_array)
    """
    try:
        import pyarrow as pa
    except ImportError:
        raise ImportError(
            "PyArrow is required for from_arrow(). "
            "Install with: pip install pyarrow"
        )

    from .dataframe import DataFrame
    from .series import Series

    if isinstance(obj, pa.Table):
        return DataFrame(obj.to_pandas())
    elif isinstance(obj, (pa.Array, pa.ChunkedArray)):
        return Series(obj.to_pandas())
    else:
        raise TypeError(
            f"Expected pyarrow.Table, Array, or ChunkedArray, got {type(obj)}"
        )


def to_numpy_safe(arr, na_value=None, dtype=None) -> _np.ndarray:
    """
    Convert an extension array (or Series backed by one) to a plain NumPy array,
    replacing any NA values with *na_value*.

    Args:
        arr: Extension array, pandas Series, or anything with a to_numpy() method
        na_value: Value to use for NA entries (default None → 0 for numeric, '' for strings)
        dtype: Target NumPy dtype (optional)

    Returns:
        numpy.ndarray with no NA/NaT values

    Example:
        >>> s = pd.array([1, pd.NA, 3], dtype='Int64')
        >>> to_numpy_safe(s, na_value=0)
        array([1, 0, 3])
    """
    if isinstance(arr, _pd.Series):
        arr = arr.to_numpy(na_value=na_value, dtype=dtype) if na_value is not None or dtype is not None else arr.array

    if hasattr(arr, 'to_numpy'):
        kw = {}
        if na_value is not None:
            kw['na_value'] = na_value
        if dtype is not None:
            kw['dtype'] = dtype
        result = arr.to_numpy(**kw)
    else:
        result = _np.asarray(arr, dtype=dtype)

    if na_value is None and result.dtype == object:
        # Replace None/NA with empty string for object arrays
        result = _np.where(result is None, '', result)

    return result


def array(data, dtype=None, copy=True):
    """
    Create a pandas ExtensionArray from sequence data.

    Wraps pandas.array() — returns the appropriate extension array type
    based on the inferred or provided dtype.

    Args:
        data: Sequence of values
        dtype: dtype or string (e.g., 'Int64', 'boolean', 'string')
        copy: Copy the data

    Returns:
        An ExtensionArray subclass

    Example:
        >>> pd.arrays.array([1, 2, None], dtype='Int64')
        <IntegerArray>
        [1, 2, <NA>]
        Length: 3, dtype: Int64
    """
    return _pd.array(data, dtype=dtype, copy=copy)


# ---------------------------------------------------------------------------
# Namespace object — exposed as pd.arrays
# ---------------------------------------------------------------------------

class _ArraysNamespace:
    """
    Full pd.arrays namespace for pandasv2.

    Usage:
        >>> import pandasv2 as pd
        >>> pd.arrays.IntegerArray
        >>> pd.arrays.to_arrow(df)
        >>> pd.arrays.from_arrow(arrow_table)
        >>> pd.arrays.array([1, None, 3], dtype='Int64')
    """
    # Standard extension array types
    BooleanArray = BooleanArray
    DatetimeArray = DatetimeArray
    FloatingArray = FloatingArray
    IntegerArray = IntegerArray
    IntervalArray = IntervalArray
    PeriodArray = PeriodArray
    SparseArray = SparseArray
    StringArray = StringArray
    TimedeltaArray = TimedeltaArray
    Categorical = Categorical

    # Version-guarded
    if MaskedArray is not None:
        MaskedArray = MaskedArray
    if NumpyExtensionArray is not None:
        NumpyExtensionArray = NumpyExtensionArray
    if ArrowExtensionArray is not None:
        ArrowExtensionArray = ArrowExtensionArray

    # pandasv2 extras
    to_arrow = staticmethod(to_arrow)
    from_arrow = staticmethod(from_arrow)
    to_numpy_safe = staticmethod(to_numpy_safe)
    array = staticmethod(array)


arrays = _ArraysNamespace()
