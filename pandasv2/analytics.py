"""
Analytics helpers for pandasv2.

Top-level statistical and time-series functions that mirror pandas:
  describe, corr, cov
  date_range, bdate_range, period_range, timedelta_range, interval_range
  to_datetime, to_timedelta, to_numeric, to_period (type conversion)
  Categorical, CategoricalDtype, CategoricalIndex
  DatetimeTZDtype, IntervalDtype, PeriodDtype, SparseDtype
  Grouper, NamedAgg
  option_context, set_option, get_option, reset_option, describe_option

Window helpers (rolling, expanding, ewm) live on the DataFrame/Series
objects directly, so no wrapping needed here.

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Dict, Hashable, Iterable, List, Optional, Sequence, Union


def _wrap(obj):
    from .dataframe import DataFrame
    from .series import Series
    if isinstance(obj, _pd.DataFrame):
        return DataFrame(obj)
    if isinstance(obj, _pd.Series):
        return Series(obj)
    return obj


# ---------------------------------------------------------------------------
# Datetime / timedelta constructors
# ---------------------------------------------------------------------------

def date_range(
    start=None,
    end=None,
    periods=None,
    freq=None,
    tz=None,
    normalize=False,
    name=None,
    inclusive='both',
    **kwargs,
):
    """
    Return a fixed frequency DatetimeIndex.

    Example:
        >>> pd.date_range('2024-01-01', periods=12, freq='ME')
    """
    return _pd.date_range(start=start, end=end, periods=periods, freq=freq,
                           tz=tz, normalize=normalize, name=name,
                           inclusive=inclusive, **kwargs)


def bdate_range(start=None, end=None, periods=None, freq='B', tz=None,
                normalize=True, name=None, weekmask=None, holidays=None,
                closed=_pd.api.extensions.no_default, inclusive='both', **kwargs):
    """Return a fixed frequency DatetimeIndex with business day frequency."""
    kw = dict(start=start, end=end, periods=periods, freq=freq, tz=tz,
              normalize=normalize, name=name, weekmask=weekmask,
              holidays=holidays, inclusive=inclusive, **kwargs)
    if closed is not _pd.api.extensions.no_default:
        kw['closed'] = closed
    return _pd.bdate_range(**kw)


def period_range(start=None, end=None, periods=None, freq=None, name=None):
    """Return a fixed frequency PeriodIndex."""
    return _pd.period_range(start=start, end=end, periods=periods,
                             freq=freq, name=name)


def timedelta_range(start=None, end=None, periods=None, freq=None, name=None,
                    closed=None):
    """Return a fixed frequency TimedeltaIndex."""
    return _pd.timedelta_range(start=start, end=end, periods=periods,
                                freq=freq, name=name, closed=closed)


def interval_range(start=None, end=None, periods=None, freq=None, name=None,
                   closed='right'):
    """Return a fixed frequency IntervalIndex."""
    return _pd.interval_range(start=start, end=end, periods=periods,
                               freq=freq, name=name, closed=closed)


# ---------------------------------------------------------------------------
# Type-conversion functions
# ---------------------------------------------------------------------------

def to_datetime(
    arg,
    errors='raise',
    dayfirst=False,
    yearfirst=False,
    utc=False,
    format=None,
    exact=_pd.api.extensions.no_default,
    unit=None,
    infer_datetime_format=_pd.api.extensions.no_default,
    origin='unix',
    cache=True,
):
    """
    Convert argument to datetime.

    Example:
        >>> pd.to_datetime(['2024-01-01', '2024-06-15'])
        >>> pd.to_datetime(df['date_str'], format='%Y-%m-%d')
    """
    kw = dict(errors=errors, dayfirst=dayfirst, yearfirst=yearfirst, utc=utc,
              format=format, unit=unit, origin=origin, cache=cache)
    if exact is not _pd.api.extensions.no_default:
        kw['exact'] = exact
    if infer_datetime_format is not _pd.api.extensions.no_default:
        kw['infer_datetime_format'] = infer_datetime_format
    result = _pd.to_datetime(arg, **kw)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


def to_timedelta(arg, unit=None, errors='raise'):
    """
    Convert argument to timedelta.

    Example:
        >>> pd.to_timedelta(['1 days', '2 hours', '30 min'])
    """
    result = _pd.to_timedelta(arg, unit=unit, errors=errors)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


def to_numeric(arg, errors='raise', downcast=None,
               dtype_backend=_pd.api.extensions.no_default):
    """
    Convert argument to a numeric type.

    Example:
        >>> pd.to_numeric(df['price_str'], errors='coerce')
    """
    kw = dict(errors=errors, downcast=downcast)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    result = _pd.to_numeric(arg, **kw)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


def to_period(arg, freq=None):
    """Convert DatetimeIndex to PeriodIndex."""
    if hasattr(arg, 'to_period'):
        return arg.to_period(freq=freq)
    return _pd.PeriodIndex(arg, freq=freq)


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def eval(expr: str, **kwargs):
    """
    Evaluate a Python expression as a string using various backends.

    Example:
        >>> pd.eval('df1 + df2')
    """
    result = _pd.eval(expr, **kwargs)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


# ---------------------------------------------------------------------------
# Index constructors
# ---------------------------------------------------------------------------

# Expose all pandas Index types directly
Index = _pd.Index
RangeIndex = _pd.RangeIndex
MultiIndex = _pd.MultiIndex
DatetimeIndex = _pd.DatetimeIndex
TimedeltaIndex = _pd.TimedeltaIndex
PeriodIndex = _pd.PeriodIndex
CategoricalIndex = _pd.CategoricalIndex
IntervalIndex = _pd.IntervalIndex
Int64Index = getattr(_pd, 'Int64Index', _pd.Index)
UInt64Index = getattr(_pd, 'UInt64Index', _pd.Index)
Float64Index = getattr(_pd, 'Float64Index', _pd.Index)


# ---------------------------------------------------------------------------
# Categorical
# ---------------------------------------------------------------------------

Categorical = _pd.Categorical
CategoricalDtype = _pd.CategoricalDtype


# ---------------------------------------------------------------------------
# Dtype objects
# ---------------------------------------------------------------------------

DatetimeTZDtype = _pd.DatetimeTZDtype
IntervalDtype = _pd.IntervalDtype
PeriodDtype = _pd.PeriodDtype
SparseDtype = _pd.SparseDtype
Int8Dtype = _pd.Int8Dtype
Int16Dtype = _pd.Int16Dtype
Int32Dtype = _pd.Int32Dtype
Int64Dtype = _pd.Int64Dtype
UInt8Dtype = _pd.UInt8Dtype
UInt16Dtype = _pd.UInt16Dtype
UInt32Dtype = _pd.UInt32Dtype
UInt64Dtype = _pd.UInt64Dtype
Float32Dtype = _pd.Float32Dtype
Float64Dtype = _pd.Float64Dtype
BooleanDtype = _pd.BooleanDtype
StringDtype = _pd.StringDtype


# ---------------------------------------------------------------------------
# Timestamp / Timedelta / Period / Interval scalars
# ---------------------------------------------------------------------------

Timestamp = _pd.Timestamp
Timedelta = _pd.Timedelta
Period = _pd.Period
Interval = _pd.Interval
NaT = _pd.NaT
NA = _pd.NA


# ---------------------------------------------------------------------------
# Grouper / NamedAgg
# ---------------------------------------------------------------------------

Grouper = _pd.Grouper
NamedAgg = _pd.NamedAgg


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

def set_option(*args, **kwargs):
    """Set the value of the specified option."""
    return _pd.set_option(*args, **kwargs)


def get_option(pat):
    """Retrieves the value of the specified option."""
    return _pd.get_option(pat)


def reset_option(pat):
    """Reset one or more options to their default value."""
    return _pd.reset_option(pat)


def describe_option(pat='', _print_desc=True):
    """Print the description for one or more registered options."""
    return _pd.describe_option(pat, _print_desc=_print_desc)


def option_context(*args):
    """Context manager to temporarily set options in a with statement."""
    return _pd.option_context(*args)


# ---------------------------------------------------------------------------
# Testing utilities
# ---------------------------------------------------------------------------

def testing_assert_frame_equal(left, right, **kwargs):
    """Wrapper around pandas.testing.assert_frame_equal."""
    _pd.testing.assert_frame_equal(left, right, **kwargs)


def testing_assert_series_equal(left, right, **kwargs):
    """Wrapper around pandas.testing.assert_series_equal."""
    _pd.testing.assert_series_equal(left, right, **kwargs)


# ---------------------------------------------------------------------------
# Offsets
# ---------------------------------------------------------------------------

offsets = _pd.offsets


# ---------------------------------------------------------------------------
# json_normalize (from pandas.io.json)
# ---------------------------------------------------------------------------

def json_normalize(
    data,
    record_path=None,
    meta=None,
    meta_prefix=None,
    record_prefix=None,
    errors='raise',
    sep='.',
    max_level=None,
):
    """
    Normalize semi-structured JSON data into a flat table.

    Example:
        >>> data = [{'id': 1, 'info': {'name': 'Alice', 'age': 30}}]
        >>> pd.json_normalize(data, meta=['id'], record_path='info')
    """
    return _wrap(_pd.json_normalize(
        data, record_path=record_path, meta=meta, meta_prefix=meta_prefix,
        record_prefix=record_prefix, errors=errors, sep=sep,
        max_level=max_level,
    ))
