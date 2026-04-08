"""
Testing utilities for pandasv2.

Mirrors and extends pandas.testing with all assert_* helpers plus
additional pandasv2-specific assertions:
  - assert_frame_equal
  - assert_series_equal
  - assert_index_equal
  - assert_extension_array_equal
  - assert_numpy_array_equal
  - assert_attr_equal
  - assert_interval_array_equal
  - assert_period_array_equal
  - assert_datetime_array_equal
  - assert_timedelta_array_equal
  - assert_categorical_equal
  - assert_sp_array_equal
  - assert_dict_equal          (pandasv2 extra)
  - assert_frame_schema_equal  (pandasv2 extra — checks dtypes/shape only)
  - assert_frame_values_close  (pandasv2 extra — numeric closeness shorthand)

Built by Mahesh Makvana
"""

import pandas as _pd
import pandas.testing as _pt
import numpy as _np
from typing import Any, Dict, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Re-export all standard pandas.testing functions
# ---------------------------------------------------------------------------

assert_frame_equal = _pt.assert_frame_equal
assert_series_equal = _pt.assert_series_equal
assert_index_equal = _pt.assert_index_equal
assert_extension_array_equal = _pt.assert_extension_array_equal
assert_numpy_array_equal = getattr(_pt, 'assert_numpy_array_equal', None)
assert_attr_equal = getattr(_pt, 'assert_attr_equal', None)
assert_interval_array_equal = getattr(_pt, 'assert_interval_array_equal', None)
assert_period_array_equal = getattr(_pt, 'assert_period_array_equal', None)
assert_datetime_array_equal = getattr(_pt, 'assert_datetime_array_equal', None)
assert_timedelta_array_equal = getattr(_pt, 'assert_timedelta_array_equal', None)


# ---------------------------------------------------------------------------
# pandas.testing helpers that exist only in some versions — guard them
# ---------------------------------------------------------------------------

def assert_categorical_equal(left, right, check_dtype=True,
                              check_category_order=True, obj='Categorical'):
    """Assert that two Categoricals are equal."""
    _pt.assert_extension_array_equal(
        left, right,
        check_dtype=check_dtype,
        obj=obj,
    )


# ---------------------------------------------------------------------------
# pandasv2-specific assertion helpers
# ---------------------------------------------------------------------------

def assert_dict_equal(left: Dict, right: Dict, check_like: bool = False) -> None:
    """
    Assert two dicts are equal.

    If check_like=True, key order does not matter (default dict equality
    already does this in Python 3.7+, but check_like also handles nested
    DataFrames/Series values).

    Example:
        >>> assert_dict_equal({'a': 1}, {'a': 1})
    """
    assert isinstance(left, dict), f"left is not a dict: {type(left)}"
    assert isinstance(right, dict), f"right is not a dict: {type(right)}"
    assert set(left.keys()) == set(right.keys()), (
        f"Dict keys differ.\nleft:  {sorted(left.keys())}\nright: {sorted(right.keys())}"
    )
    for k in left:
        lv, rv = left[k], right[k]
        if isinstance(lv, _pd.DataFrame) and isinstance(rv, _pd.DataFrame):
            _pt.assert_frame_equal(lv, rv, check_like=check_like)
        elif isinstance(lv, _pd.Series) and isinstance(rv, _pd.Series):
            _pt.assert_series_equal(lv, rv, check_like=check_like)
        elif isinstance(lv, _np.ndarray) and isinstance(rv, _np.ndarray):
            _np.testing.assert_array_equal(lv, rv)
        else:
            assert lv == rv, f"Dict value mismatch for key {k!r}: {lv!r} != {rv!r}"


def assert_frame_schema_equal(
    left: _pd.DataFrame,
    right: _pd.DataFrame,
    check_dtype: bool = True,
    check_column_order: bool = True,
) -> None:
    """
    Assert two DataFrames have the same schema (columns + dtypes), ignoring data.

    Args:
        left: First DataFrame
        right: Second DataFrame
        check_dtype: If True, also check that dtypes match column-by-column
        check_column_order: If True, column order must match

    Example:
        >>> assert_frame_schema_equal(df1, df2)   # same structure, don't care about values
    """
    left_cols = list(left.columns)
    right_cols = list(right.columns)

    if check_column_order:
        assert left_cols == right_cols, (
            f"Column order differs.\nleft:  {left_cols}\nright: {right_cols}"
        )
    else:
        assert set(left_cols) == set(right_cols), (
            f"Column sets differ.\nleft:  {sorted(left_cols)}\nright: {sorted(right_cols)}"
        )

    if check_dtype:
        for col in left_cols:
            ld, rd = left[col].dtype, right[col].dtype
            assert ld == rd, (
                f"Dtype mismatch for column {col!r}: {ld} != {rd}"
            )

    assert left.shape[1] == right.shape[1], (
        f"Column count differs: {left.shape[1]} != {right.shape[1]}"
    )


def assert_frame_values_close(
    left: _pd.DataFrame,
    right: _pd.DataFrame,
    rtol: float = 1.0e-5,
    atol: float = 1.0e-8,
    check_like: bool = False,
) -> None:
    """
    Assert numeric columns of two DataFrames are element-wise close.

    Non-numeric columns are compared with exact equality.

    Args:
        left: First DataFrame
        right: Second DataFrame
        rtol: Relative tolerance for numeric comparison
        atol: Absolute tolerance for numeric comparison
        check_like: Ignore row/column order

    Example:
        >>> assert_frame_values_close(result_df, expected_df, atol=0.01)
    """
    _pt.assert_frame_equal(
        left, right,
        check_exact=False,
        rtol=rtol,
        atol=atol,
        check_like=check_like,
    )


def assert_series_values_close(
    left: _pd.Series,
    right: _pd.Series,
    rtol: float = 1.0e-5,
    atol: float = 1.0e-8,
    check_names: bool = True,
) -> None:
    """
    Assert two numeric Series are element-wise close.

    Example:
        >>> assert_series_values_close(result, expected, atol=1e-3)
    """
    _pt.assert_series_equal(
        left, right,
        check_exact=False,
        rtol=rtol,
        atol=atol,
        check_names=check_names,
    )


def assert_frame_not_empty(df: _pd.DataFrame, msg: str = '') -> None:
    """
    Assert DataFrame has at least one row.

    Example:
        >>> assert_frame_not_empty(df, 'Query returned no rows')
    """
    assert len(df) > 0, msg or f"DataFrame is empty (0 rows)"


def assert_series_not_empty(s: _pd.Series, msg: str = '') -> None:
    """Assert Series has at least one element."""
    assert len(s) > 0, msg or "Series is empty (0 elements)"


def assert_no_nulls(obj: Union[_pd.DataFrame, _pd.Series], subset=None) -> None:
    """
    Assert DataFrame or Series contains no null values.

    Args:
        obj: DataFrame or Series to check
        subset: For DataFrames, list of column names to check (default: all)

    Example:
        >>> assert_no_nulls(df[['price', 'qty']])
    """
    if isinstance(obj, _pd.DataFrame):
        check = obj[subset] if subset is not None else obj
        nulls = check.isnull().sum()
        cols_with_nulls = nulls[nulls > 0]
        assert cols_with_nulls.empty, (
            f"DataFrame contains nulls:\n{cols_with_nulls.to_string()}"
        )
    elif isinstance(obj, _pd.Series):
        n = obj.isnull().sum()
        assert n == 0, f"Series '{obj.name}' contains {n} null value(s)"
    else:
        raise TypeError(f"Expected DataFrame or Series, got {type(obj)}")


def assert_unique_index(df: _pd.DataFrame, msg: str = '') -> None:
    """
    Assert DataFrame index has no duplicates.

    Example:
        >>> assert_unique_index(df)
    """
    dupes = df.index.duplicated().sum()
    assert dupes == 0, msg or f"DataFrame index has {dupes} duplicate(s)"


def assert_columns_exist(df: _pd.DataFrame, columns: Sequence[str]) -> None:
    """
    Assert all specified columns exist in the DataFrame.

    Example:
        >>> assert_columns_exist(df, ['user_id', 'timestamp', 'value'])
    """
    missing = [c for c in columns if c not in df.columns]
    assert not missing, f"Missing columns: {missing}"


def assert_dtypes(df: _pd.DataFrame, expected: Dict[str, Any]) -> None:
    """
    Assert column dtypes match expected mapping.

    Args:
        df: DataFrame to check
        expected: Dict of {column_name: expected_dtype}
                  Dtype can be a string ('int64'), numpy dtype, or pandas dtype.

    Example:
        >>> assert_dtypes(df, {'price': 'float64', 'qty': 'int64', 'name': 'object'})
    """
    for col, expected_dtype in expected.items():
        assert col in df.columns, f"Column {col!r} not found in DataFrame"
        actual = df[col].dtype
        expected_dtype = _np.dtype(expected_dtype) if isinstance(expected_dtype, str) else expected_dtype
        assert actual == expected_dtype, (
            f"Column {col!r} dtype mismatch: got {actual}, expected {expected_dtype}"
        )


def assert_row_count(df: _pd.DataFrame, expected_count: int,
                     msg: str = '') -> None:
    """
    Assert DataFrame has exactly the expected number of rows.

    Example:
        >>> assert_row_count(df, 100)
    """
    assert len(df) == expected_count, (
        msg or f"Row count mismatch: got {len(df)}, expected {expected_count}"
    )


def assert_sorted(obj: Union[_pd.DataFrame, _pd.Series], by=None,
                  ascending: bool = True) -> None:
    """
    Assert a DataFrame or Series is sorted.

    Args:
        obj: DataFrame or Series to check
        by: For DataFrames, column(s) to check sort order on
        ascending: Expected sort direction

    Example:
        >>> assert_sorted(df, by='timestamp')
        >>> assert_sorted(series)
    """
    if isinstance(obj, _pd.DataFrame):
        assert by is not None, "Must provide 'by' column(s) for DataFrame"
        check_col = obj[by] if isinstance(by, str) else obj[by[0]]
    else:
        check_col = obj

    values = check_col.dropna().values
    if ascending:
        is_sorted = all(values[i] <= values[i + 1] for i in range(len(values) - 1))
    else:
        is_sorted = all(values[i] >= values[i + 1] for i in range(len(values) - 1))

    direction = 'ascending' if ascending else 'descending'
    assert is_sorted, f"Data is not sorted in {direction} order"


# ---------------------------------------------------------------------------
# Namespace object for pd.testing usage
# ---------------------------------------------------------------------------

class _TestingNamespace:
    """
    Exposes all pandasv2 testing utilities as pd.testing.*.

    Example:
        >>> import pandasv2 as pd
        >>> pd.testing.assert_frame_equal(df1, df2)
        >>> pd.testing.assert_no_nulls(df)
        >>> pd.testing.assert_columns_exist(df, ['a', 'b'])
    """

    # Standard pandas.testing
    assert_frame_equal = staticmethod(assert_frame_equal)
    assert_series_equal = staticmethod(assert_series_equal)
    assert_index_equal = staticmethod(assert_index_equal)
    assert_extension_array_equal = staticmethod(assert_extension_array_equal)
    assert_categorical_equal = staticmethod(assert_categorical_equal)

    # Version-guarded — only attach if available in installed pandas
    if assert_numpy_array_equal is not None:
        assert_numpy_array_equal = staticmethod(assert_numpy_array_equal)
    if assert_attr_equal is not None:
        assert_attr_equal = staticmethod(assert_attr_equal)
    if assert_interval_array_equal is not None:
        assert_interval_array_equal = staticmethod(assert_interval_array_equal)
    if assert_period_array_equal is not None:
        assert_period_array_equal = staticmethod(assert_period_array_equal)
    if assert_datetime_array_equal is not None:
        assert_datetime_array_equal = staticmethod(assert_datetime_array_equal)
    if assert_timedelta_array_equal is not None:
        assert_timedelta_array_equal = staticmethod(assert_timedelta_array_equal)

    # pandasv2 extras
    assert_dict_equal = staticmethod(assert_dict_equal)
    assert_frame_schema_equal = staticmethod(assert_frame_schema_equal)
    assert_frame_values_close = staticmethod(assert_frame_values_close)
    assert_series_values_close = staticmethod(assert_series_values_close)
    assert_frame_not_empty = staticmethod(assert_frame_not_empty)
    assert_series_not_empty = staticmethod(assert_series_not_empty)
    assert_no_nulls = staticmethod(assert_no_nulls)
    assert_unique_index = staticmethod(assert_unique_index)
    assert_columns_exist = staticmethod(assert_columns_exist)
    assert_dtypes = staticmethod(assert_dtypes)
    assert_row_count = staticmethod(assert_row_count)
    assert_sorted = staticmethod(assert_sorted)


testing = _TestingNamespace()
