"""
Reshape / merge / concat utilities for pandasv2.

Wraps pandas top-level reshaping functions so results are always
pandasv2 DataFrame/Series objects.

Functions:
  merge, merge_asof, merge_ordered
  concat
  pivot, pivot_table
  melt, wide_to_long
  crosstab
  cut, qcut
  get_dummies
  factorize
  unique
  value_counts (top-level)
  lreshape
  notna, isna, isnull, notnull

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Sequence, Union


def _wrap(obj):
    from .dataframe import DataFrame
    from .series import Series
    if isinstance(obj, _pd.DataFrame):
        return DataFrame(obj)
    if isinstance(obj, _pd.Series):
        return Series(obj)
    return obj


# ---------------------------------------------------------------------------
# Merge / Join
# ---------------------------------------------------------------------------

def merge(
    left,
    right,
    how: str = 'inner',
    on=None,
    left_on=None,
    right_on=None,
    left_index: bool = False,
    right_index: bool = False,
    sort: bool = False,
    suffixes=('_x', '_y'),
    copy: bool = True,
    indicator: bool = False,
    validate=None,
):
    """
    Merge DataFrame or named Series objects with a database-style join.

    All parameters identical to pandas.merge().

    Example:
        >>> import pandasv2 as pd
        >>> df1 = pd.DataFrame({'key': ['a','b'], 'val1': [1, 2]})
        >>> df2 = pd.DataFrame({'key': ['a','b'], 'val2': [3, 4]})
        >>> pd.merge(df1, df2, on='key')
    """
    return _wrap(_pd.merge(
        left, right, how=how, on=on, left_on=left_on, right_on=right_on,
        left_index=left_index, right_index=right_index, sort=sort,
        suffixes=suffixes, copy=copy, indicator=indicator, validate=validate,
    ))


def merge_asof(
    left,
    right,
    on=None,
    left_on=None,
    right_on=None,
    left_index=False,
    right_index=False,
    by=None,
    left_by=None,
    right_by=None,
    suffixes=('_x', '_y'),
    tolerance=None,
    allow_exact_matches=True,
    direction='backward',
):
    """
    Perform an asof merge.  Similar to merge but joins on nearest key rather
    than equal keys.

    Example:
        >>> pd.merge_asof(trades, quotes, on='time', by='ticker')
    """
    return _wrap(_pd.merge_asof(
        left, right, on=on, left_on=left_on, right_on=right_on,
        left_index=left_index, right_index=right_index,
        by=by, left_by=left_by, right_by=right_by,
        suffixes=suffixes, tolerance=tolerance,
        allow_exact_matches=allow_exact_matches, direction=direction,
    ))


def merge_ordered(
    left,
    right,
    on=None,
    left_on=None,
    right_on=None,
    left_by=None,
    right_by=None,
    fill_method=None,
    suffixes=('_x', '_y'),
    how='outer',
):
    """
    Perform merge with optional filling/interpolation.

    Example:
        >>> pd.merge_ordered(df1, df2, on='date', fill_method='ffill')
    """
    return _wrap(_pd.merge_ordered(
        left, right, on=on, left_on=left_on, right_on=right_on,
        left_by=left_by, right_by=right_by, fill_method=fill_method,
        suffixes=suffixes, how=how,
    ))


# ---------------------------------------------------------------------------
# Concat / Append
# ---------------------------------------------------------------------------

def concat(
    objs,
    axis=0,
    join='outer',
    ignore_index=False,
    keys=None,
    levels=None,
    names=None,
    verify_integrity=False,
    sort=False,
    copy=True,
):
    """
    Concatenate pandas objects along a particular axis.

    All parameters identical to pandas.concat().

    Example:
        >>> pd.concat([df1, df2], ignore_index=True)
        >>> pd.concat([df1, df2], axis=1)
    """
    return _wrap(_pd.concat(
        objs, axis=axis, join=join, ignore_index=ignore_index,
        keys=keys, levels=levels, names=names,
        verify_integrity=verify_integrity, sort=sort, copy=copy,
    ))


# ---------------------------------------------------------------------------
# Pivot
# ---------------------------------------------------------------------------

def pivot(data, index=None, columns=None, values=None):
    """
    Return reshaped DataFrame organized by given index / column values.

    Example:
        >>> pd.pivot(df, index='date', columns='variable', values='value')
    """
    return _wrap(_pd.pivot(data, index=index, columns=columns, values=values))


def pivot_table(
    data,
    values=None,
    index=None,
    columns=None,
    aggfunc='mean',
    fill_value=None,
    margins=False,
    dropna=True,
    margins_name='All',
    observed=False,
    sort=True,
):
    """
    Create a spreadsheet-style pivot table as a pandasv2 DataFrame.

    Example:
        >>> pd.pivot_table(df, values='sales', index='region',
        ...                columns='product', aggfunc='sum', margins=True)
    """
    return _wrap(_pd.pivot_table(
        data, values=values, index=index, columns=columns, aggfunc=aggfunc,
        fill_value=fill_value, margins=margins, dropna=dropna,
        margins_name=margins_name, observed=observed, sort=sort,
    ))


# ---------------------------------------------------------------------------
# Melt / Wide-to-long
# ---------------------------------------------------------------------------

def melt(
    frame,
    id_vars=None,
    value_vars=None,
    var_name=None,
    value_name='value',
    col_level=None,
    ignore_index=True,
):
    """
    Unpivot a DataFrame from wide to long format.

    Example:
        >>> pd.melt(df, id_vars=['id'], value_vars=['jan','feb','mar'])
    """
    return _wrap(_pd.melt(
        frame, id_vars=id_vars, value_vars=value_vars, var_name=var_name,
        value_name=value_name, col_level=col_level, ignore_index=ignore_index,
    ))


def wide_to_long(df, stubnames, i, j, sep='', suffix=r'\d+'):
    """
    Wide panel to long format.

    Example:
        >>> pd.wide_to_long(df, stubnames=['A', 'B'], i='id', j='year')
    """
    return _wrap(_pd.wide_to_long(df, stubnames=stubnames, i=i, j=j,
                                   sep=sep, suffix=suffix))


# ---------------------------------------------------------------------------
# Cross-tabulation
# ---------------------------------------------------------------------------

def crosstab(
    index,
    columns,
    values=None,
    rownames=None,
    colnames=None,
    aggfunc=None,
    margins=False,
    margins_name='All',
    dropna=True,
    normalize=False,
):
    """
    Compute a simple cross tabulation of two (or more) factors.

    Example:
        >>> pd.crosstab(df['gender'], df['age_group'], margins=True)
    """
    return _wrap(_pd.crosstab(
        index, columns, values=values, rownames=rownames, colnames=colnames,
        aggfunc=aggfunc, margins=margins, margins_name=margins_name,
        dropna=dropna, normalize=normalize,
    ))


# ---------------------------------------------------------------------------
# Encoding / binning
# ---------------------------------------------------------------------------

def cut(
    x,
    bins,
    right=True,
    labels=None,
    retbins=False,
    precision=3,
    include_lowest=False,
    duplicates='raise',
    ordered=True,
):
    """
    Bin values into discrete intervals.

    Example:
        >>> pd.cut(df['age'], bins=[0, 18, 35, 60, 100],
        ...        labels=['child','young','adult','senior'])
    """
    result = _pd.cut(x, bins, right=right, labels=labels, retbins=retbins,
                      precision=precision, include_lowest=include_lowest,
                      duplicates=duplicates, ordered=ordered)
    if retbins:
        val, bins_out = result
        return _wrap(val) if isinstance(val, (_pd.Series, _pd.DataFrame)) else val, bins_out
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


def qcut(x, q, labels=None, retbins=False, precision=3, duplicates='raise'):
    """
    Quantile-based discretization function.

    Example:
        >>> pd.qcut(df['score'], q=4, labels=['Q1','Q2','Q3','Q4'])
    """
    result = _pd.qcut(x, q, labels=labels, retbins=retbins, precision=precision,
                       duplicates=duplicates)
    if retbins:
        val, bins_out = result
        return _wrap(val) if isinstance(val, (_pd.Series, _pd.DataFrame)) else val, bins_out
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


def get_dummies(
    data,
    prefix=None,
    prefix_sep='_',
    dummy_na=False,
    columns=None,
    sparse=False,
    drop_first=False,
    dtype=None,
):
    """
    Convert categorical variable(s) into dummy/indicator variables.

    Example:
        >>> pd.get_dummies(df, columns=['color', 'size'])
        >>> pd.get_dummies(df['color'])
    """
    return _wrap(_pd.get_dummies(
        data, prefix=prefix, prefix_sep=prefix_sep, dummy_na=dummy_na,
        columns=columns, sparse=sparse, drop_first=drop_first, dtype=dtype,
    ))


def from_dummies(data, sep=None, default_category=None):
    """
    Create a categorical DataFrame from a DataFrame of dummy variables.

    Example:
        >>> pd.from_dummies(dummies_df, sep='_')
    """
    return _wrap(_pd.from_dummies(data, sep=sep, default_category=default_category))


# ---------------------------------------------------------------------------
# Factorize / unique / value_counts
# ---------------------------------------------------------------------------

def factorize(values, sort=False, na_sentinel=_pd.api.extensions.no_default,
              use_na_sentinel=_pd.api.extensions.no_default, size_hint=None):
    """
    Encode the object as an enumerated type or categorical variable.

    Returns:
        codes (ndarray), uniques (Index)

    Example:
        >>> codes, uniques = pd.factorize(df['category'])
    """
    kw = dict(sort=sort, size_hint=size_hint)
    if na_sentinel is not _pd.api.extensions.no_default:
        kw['na_sentinel'] = na_sentinel
    if use_na_sentinel is not _pd.api.extensions.no_default:
        kw['use_na_sentinel'] = use_na_sentinel
    return _pd.factorize(values, **kw)


def unique(values):
    """Return unique values based on a hash table (faster than numpy.unique)."""
    return _pd.unique(values)


def value_counts(values, sort=True, ascending=False, normalize=False,
                 bins=None, dropna=True):
    """
    Compute a histogram of the counts of non-null values.

    Example:
        >>> pd.value_counts(df['category'])
    """
    from .series import Series
    s = _pd.Series(values) if not isinstance(values, _pd.Series) else values
    return Series(s.value_counts(sort=sort, ascending=ascending,
                                  normalize=normalize, bins=bins, dropna=dropna))


# ---------------------------------------------------------------------------
# NA utilities
# ---------------------------------------------------------------------------

def isna(obj):
    """Detect missing values. Returns boolean array/scalar."""
    result = _pd.isna(obj)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


isnull = isna


def notna(obj):
    """Detect existing (non-missing) values."""
    result = _pd.notna(obj)
    return _wrap(result) if isinstance(result, (_pd.Series, _pd.DataFrame)) else result


notnull = notna
