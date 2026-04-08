"""
pd.api.types helpers for pandasv2.

Mirrors the full pandas.api.types namespace plus pandasv2 extras:

Standard (re-exported from pandas.api.types):
  is_bool_dtype, is_categorical_dtype, is_complex_dtype,
  is_datetime64_any_dtype, is_datetime64_dtype, is_datetime64_ns_dtype,
  is_datetime64tz_dtype, is_extension_array_dtype, is_float_dtype,
  is_float, is_hashable, is_integer_dtype, is_integer,
  is_interval_dtype, is_iterator, is_list_like, is_named_tuple,
  is_number, is_numeric_dtype, is_object_dtype, is_period_dtype,
  is_re, is_re_compilable, is_scalar, is_signed_integer_dtype,
  is_sparse, is_string_dtype, is_timedelta64_dtype, is_timedelta64_ns_dtype,
  is_unsigned_integer_dtype, pandas_dtype, union_categoricals,
  infer_dtype, is_dict_like, is_file_like, is_sequence

pandasv2 extras:
  is_json_serializable   — True if value can be json.dumps'd without error
  is_web_safe            — True if value is a plain Python type (no NumPy)
  coerce_to_json_type    — Convert a single value to its JSON-safe equivalent
  get_dtype_kind         — Return single-char dtype kind ('i','f','U','M', ...)
  describe_dtype         — Human-readable dtype description string

Built by Mahesh Makvana
"""

import json as _json
import pandas as _pd
import pandas.api.types as _pat
import numpy as _np
from typing import Any


# ---------------------------------------------------------------------------
# Re-export everything from pandas.api.types
# ---------------------------------------------------------------------------

is_bool_dtype = _pat.is_bool_dtype
is_categorical_dtype = getattr(_pat, 'is_categorical_dtype', None)
is_complex_dtype = _pat.is_complex_dtype
is_datetime64_any_dtype = _pat.is_datetime64_any_dtype
is_datetime64_dtype = _pat.is_datetime64_dtype
is_datetime64_ns_dtype = _pat.is_datetime64_ns_dtype
is_datetime64tz_dtype = _pat.is_datetime64tz_dtype
is_extension_array_dtype = _pat.is_extension_array_dtype
is_float_dtype = _pat.is_float_dtype
is_float = _pat.is_float
is_hashable = _pat.is_hashable
is_integer_dtype = _pat.is_integer_dtype
is_integer = _pat.is_integer
is_interval_dtype = getattr(_pat, 'is_interval_dtype', None)
is_iterator = _pat.is_iterator
is_list_like = _pat.is_list_like
is_named_tuple = _pat.is_named_tuple
is_number = _pat.is_number
is_numeric_dtype = _pat.is_numeric_dtype
is_object_dtype = _pat.is_object_dtype
is_period_dtype = getattr(_pat, 'is_period_dtype', None)
is_re = _pat.is_re
is_re_compilable = _pat.is_re_compilable
is_scalar = _pat.is_scalar
is_signed_integer_dtype = _pat.is_signed_integer_dtype
is_sparse = getattr(_pat, 'is_sparse', None)
is_string_dtype = _pat.is_string_dtype
is_timedelta64_dtype = _pat.is_timedelta64_dtype
is_timedelta64_ns_dtype = _pat.is_timedelta64_ns_dtype
is_unsigned_integer_dtype = _pat.is_unsigned_integer_dtype
pandas_dtype = _pat.pandas_dtype
union_categoricals = _pd.api.types.union_categoricals
infer_dtype = _pat.infer_dtype
is_dict_like = _pat.is_dict_like
is_file_like = getattr(_pat, 'is_file_like', None)
is_sequence = getattr(_pat, 'is_sequence', None)


# ---------------------------------------------------------------------------
# pandasv2 extras
# ---------------------------------------------------------------------------

def is_json_serializable(value: Any) -> bool:
    """
    Return True if *value* can be serialized to JSON with the standard library.

    Note: pandasv2.JSONEncoder handles NumPy/pandas types — this function
    checks whether a value is *already* a plain Python JSON type (int, float,
    str, bool, None, list, dict).

    Example:
        >>> is_json_serializable(42)          # True
        >>> is_json_serializable(np.int64(1)) # False  (needs JSONEncoder)
        >>> is_json_serializable({'a': 1})    # True
    """
    try:
        _json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def is_web_safe(value: Any) -> bool:
    """
    Return True if *value* is a plain Python type safe for web serialization
    without any encoder (int, float, str, bool, None, list, dict).

    Unlike is_json_serializable, this does NOT attempt serialization —
    it checks the type directly, making it fast for hot paths.

    Example:
        >>> is_web_safe(1)              # True
        >>> is_web_safe(np.int64(1))    # False
        >>> is_web_safe([1, 2, 3])      # True
    """
    return isinstance(value, (int, float, str, bool, type(None), list, dict))


def coerce_to_json_type(value: Any) -> Any:
    """
    Convert a single value to its plain Python JSON-safe equivalent.

    Handles:
    - NumPy integers → int
    - NumPy floats  → float (NaN/Inf → None)
    - NumPy bool    → bool
    - NumPy ndarray → list
    - pandas Timestamp → ISO-8601 str
    - pandas Timedelta → total_seconds float
    - pandas NaT      → None
    - pandas NA       → None
    - pandas Categorical → str(value)
    - Everything else → unchanged

    Example:
        >>> coerce_to_json_type(np.int64(7))       # 7
        >>> coerce_to_json_type(pd.Timestamp(...)) # '2024-01-01T00:00:00'
        >>> coerce_to_json_type(np.nan)            # None
    """
    if value is _pd.NaT or value is _pd.NA:
        return None
    if isinstance(value, float) and (_np.isnan(value) or _np.isinf(value)):
        return None
    if isinstance(value, _np.integer):
        return int(value)
    if isinstance(value, _np.floating):
        v = float(value)
        return None if (_np.isnan(v) or _np.isinf(v)) else v
    if isinstance(value, _np.bool_):
        return bool(value)
    if isinstance(value, _np.ndarray):
        return value.tolist()
    if isinstance(value, _pd.Timestamp):
        return value.isoformat()
    if isinstance(value, _pd.Timedelta):
        return value.total_seconds()
    if isinstance(value, _pd.Period):
        return str(value)
    if isinstance(value, _pd.Interval):
        return str(value)
    if isinstance(value, _pd.Categorical):
        return list(value)
    return value


def get_dtype_kind(dtype) -> str:
    """
    Return the single-character NumPy dtype kind for *dtype*.

    Kind codes:
      'b' boolean
      'i' signed integer
      'u' unsigned integer
      'f' float
      'c' complex
      'S' byte string
      'U' unicode string
      'V' void
      'M' datetime
      'm' timedelta
      'O' object

    Example:
        >>> get_dtype_kind('int64')   # 'i'
        >>> get_dtype_kind('float32') # 'f'
        >>> get_dtype_kind('object')  # 'O'
    """
    try:
        return _np.dtype(dtype).kind
    except TypeError:
        # pandas extension types (Int64Dtype, etc.) don't convert directly
        if hasattr(dtype, 'numpy_dtype'):
            return dtype.numpy_dtype.kind
        return 'O'


def describe_dtype(dtype) -> str:
    """
    Return a human-readable description of *dtype*.

    Example:
        >>> describe_dtype('int64')                   # 'signed 64-bit integer'
        >>> describe_dtype('float32')                 # '32-bit float'
        >>> describe_dtype('datetime64[ns]')          # 'datetime (nanosecond)'
        >>> describe_dtype(pd.CategoricalDtype())     # 'categorical'
        >>> describe_dtype(pd.StringDtype())          # 'string (nullable)'
    """
    try:
        np_dtype = _np.dtype(dtype)
    except TypeError:
        # Extension types
        name = type(dtype).__name__
        mapping = {
            'CategoricalDtype': 'categorical',
            'DatetimeTZDtype': f'timezone-aware datetime ({getattr(dtype, "tz", "??")})',
            'IntervalDtype': f'interval ({getattr(dtype, "subtype", "??")})',
            'PeriodDtype': f'period ({getattr(dtype, "freq", "??")})',
            'SparseDtype': f'sparse ({getattr(dtype, "subtype", "??")})',
            'StringDtype': 'string (nullable)',
            'BooleanDtype': 'boolean (nullable)',
        }
        for prefix, desc in mapping.items():
            if prefix in name:
                return desc
        if 'Int' in name or 'UInt' in name or 'Float' in name:
            return f'nullable {name.replace("Dtype", "").lower()}'
        return name

    kind = np_dtype.kind
    bits = np_dtype.itemsize * 8
    kind_map = {
        'b': 'boolean',
        'i': f'signed {bits}-bit integer',
        'u': f'unsigned {bits}-bit integer',
        'f': f'{bits}-bit float',
        'c': f'{bits}-bit complex',
        'S': f'byte string ({bits // 8} chars)',
        'U': f'unicode string ({bits // 32} chars)',
        'M': _datetime_desc(np_dtype),
        'm': _timedelta_desc(np_dtype),
        'O': 'object (Python)',
        'V': 'void (structured)',
    }
    return kind_map.get(kind, str(np_dtype))


def _datetime_desc(np_dtype) -> str:
    s = str(np_dtype)
    unit_map = {'ns': 'nanosecond', 'us': 'microsecond', 'ms': 'millisecond',
                's': 'second', 'm': 'minute', 'h': 'hour', 'D': 'day'}
    for unit, label in unit_map.items():
        if f'[{unit}]' in s:
            return f'datetime ({label})'
    return 'datetime'


def _timedelta_desc(np_dtype) -> str:
    s = str(np_dtype)
    unit_map = {'ns': 'nanosecond', 'us': 'microsecond', 'ms': 'millisecond',
                's': 'second', 'm': 'minute', 'h': 'hour', 'D': 'day'}
    for unit, label in unit_map.items():
        if f'[{unit}]' in s:
            return f'timedelta ({label})'
    return 'timedelta'


# ---------------------------------------------------------------------------
# Namespace object — exposed as pd.api.types
# ---------------------------------------------------------------------------

class _ApiTypesNamespace:
    """
    Full pd.api.types namespace for pandasv2.

    Usage:
        >>> import pandasv2 as pd
        >>> pd.api.types.is_numeric_dtype(df['price'])
        >>> pd.api.types.is_json_serializable({'a': 1})
        >>> pd.api.types.describe_dtype('datetime64[ns]')
    """
    # Standard pandas
    is_bool_dtype = staticmethod(is_bool_dtype)
    is_complex_dtype = staticmethod(is_complex_dtype)
    is_datetime64_any_dtype = staticmethod(is_datetime64_any_dtype)
    is_datetime64_dtype = staticmethod(is_datetime64_dtype)
    is_datetime64_ns_dtype = staticmethod(is_datetime64_ns_dtype)
    is_datetime64tz_dtype = staticmethod(is_datetime64tz_dtype)
    is_extension_array_dtype = staticmethod(is_extension_array_dtype)
    is_float_dtype = staticmethod(is_float_dtype)
    is_float = staticmethod(is_float)
    is_hashable = staticmethod(is_hashable)
    is_integer_dtype = staticmethod(is_integer_dtype)
    is_integer = staticmethod(is_integer)
    is_iterator = staticmethod(is_iterator)
    is_list_like = staticmethod(is_list_like)
    is_named_tuple = staticmethod(is_named_tuple)
    is_number = staticmethod(is_number)
    is_numeric_dtype = staticmethod(is_numeric_dtype)
    is_object_dtype = staticmethod(is_object_dtype)
    is_re = staticmethod(is_re)
    is_re_compilable = staticmethod(is_re_compilable)
    is_scalar = staticmethod(is_scalar)
    is_signed_integer_dtype = staticmethod(is_signed_integer_dtype)
    is_string_dtype = staticmethod(is_string_dtype)
    is_timedelta64_dtype = staticmethod(is_timedelta64_dtype)
    is_timedelta64_ns_dtype = staticmethod(is_timedelta64_ns_dtype)
    is_unsigned_integer_dtype = staticmethod(is_unsigned_integer_dtype)
    pandas_dtype = staticmethod(pandas_dtype)
    union_categoricals = staticmethod(union_categoricals)
    infer_dtype = staticmethod(infer_dtype)
    is_dict_like = staticmethod(is_dict_like)
    if is_file_like is not None:
        is_file_like = staticmethod(is_file_like)
    if is_sequence is not None:
        is_sequence = staticmethod(is_sequence)

    # pandasv2 extras
    is_json_serializable = staticmethod(is_json_serializable)
    is_web_safe = staticmethod(is_web_safe)
    coerce_to_json_type = staticmethod(coerce_to_json_type)
    get_dtype_kind = staticmethod(get_dtype_kind)
    describe_dtype = staticmethod(describe_dtype)

    # Deprecated / version-guarded — attach only if present
    if is_categorical_dtype is not None:
        is_categorical_dtype = staticmethod(is_categorical_dtype)
    if is_interval_dtype is not None:
        is_interval_dtype = staticmethod(is_interval_dtype)
    if is_period_dtype is not None:
        is_period_dtype = staticmethod(is_period_dtype)
    if is_sparse is not None:
        is_sparse = staticmethod(is_sparse)


class _ApiNamespace:
    """
    pd.api namespace — mirrors pandas.api.

    Usage:
        >>> import pandasv2 as pd
        >>> pd.api.types.is_numeric_dtype(...)
        >>> pd.api.extensions.register_dataframe_accessor(...)
    """
    types = _ApiTypesNamespace()
    extensions = _pd.api.extensions
    indexing = getattr(_pd.api, 'indexing', None)


api = _ApiNamespace()
