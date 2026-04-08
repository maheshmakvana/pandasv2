"""
GroupBy wrappers for pandasv2.

Wraps pandas DataFrameGroupBy / SeriesGroupBy so results are always
pandasv2 DataFrame/Series objects.

Built by Mahesh Makvana
"""

import pandas as _pd
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Union


def _wrap(obj):
    from .dataframe import DataFrame
    from .series import Series
    if isinstance(obj, _pd.DataFrame):
        return DataFrame(obj)
    if isinstance(obj, _pd.Series):
        return Series(obj)
    return obj


class DataFrameGroupBy:
    """
    pandasv2 DataFrameGroupBy — wraps pandas DataFrameGroupBy.

    All standard groupby methods are available.  Results are
    automatically wrapped as pandasv2 DataFrame/Series.

    Example:
        >>> import pandasv2 as pd
        >>> df = pd.DataFrame({'key': ['a','b','a'], 'val': [1,2,3]})
        >>> df.groupby('key').sum()
        >>> df.groupby('key').agg({'val': ['mean', 'sum']})
    """

    def __init__(self, pandas_groupby):
        self._gb = pandas_groupby

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------

    def sum(self, numeric_only=_pd.api.extensions.no_default, min_count=0, **kwargs):
        kw = dict(min_count=min_count, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.sum(**kw))

    def mean(self, numeric_only=_pd.api.extensions.no_default, **kwargs):
        kw = dict(**kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.mean(**kw))

    def median(self, numeric_only=_pd.api.extensions.no_default, **kwargs):
        kw = dict(**kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.median(**kw))

    def min(self, numeric_only=_pd.api.extensions.no_default, min_count=-1, **kwargs):
        kw = dict(min_count=min_count, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.min(**kw))

    def max(self, numeric_only=_pd.api.extensions.no_default, min_count=-1, **kwargs):
        kw = dict(min_count=min_count, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.max(**kw))

    def count(self):
        return _wrap(self._gb.count())

    def std(self, ddof=1, numeric_only=_pd.api.extensions.no_default, **kwargs):
        kw = dict(ddof=ddof, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.std(**kw))

    def var(self, ddof=1, numeric_only=_pd.api.extensions.no_default, **kwargs):
        kw = dict(ddof=ddof, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.var(**kw))

    def sem(self, ddof=1, numeric_only=_pd.api.extensions.no_default, **kwargs):
        kw = dict(ddof=ddof, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.sem(**kw))

    def prod(self, numeric_only=_pd.api.extensions.no_default, min_count=0, **kwargs):
        kw = dict(min_count=min_count, **kwargs)
        if numeric_only is not _pd.api.extensions.no_default:
            kw['numeric_only'] = numeric_only
        return _wrap(self._gb.prod(**kw))

    def first(self, numeric_only=False, min_count=-1, skipna=True, **kwargs):
        return _wrap(self._gb.first(**kwargs))

    def last(self, numeric_only=False, min_count=-1, skipna=True, **kwargs):
        return _wrap(self._gb.last(**kwargs))

    def nth(self, n, dropna=None):
        return _wrap(self._gb.nth(n, dropna=dropna))

    def nunique(self, dropna=True):
        return _wrap(self._gb.nunique(dropna=dropna))

    def size(self):
        return _wrap(self._gb.size())

    def describe(self, percentiles=None, include=None, exclude=None):
        return _wrap(self._gb.describe(percentiles=percentiles,
                                        include=include, exclude=exclude))

    def agg(self, func=None, *args, **kwargs):
        """
        Aggregate using one or more operations.

        Example:
            >>> df.groupby('key').agg('sum')
            >>> df.groupby('key').agg({'val': ['mean', 'std']})
            >>> df.groupby('key').agg(total=('val', 'sum'))
        """
        return _wrap(self._gb.agg(func, *args, **kwargs))

    aggregate = agg

    def transform(self, func, *args, engine=None, engine_kwargs=None, **kwargs):
        """
        Call func producing a like-indexed result for each group.

        Example:
            >>> df.groupby('key')['val'].transform('mean')
        """
        return _wrap(self._gb.transform(func, *args, engine=engine,
                                         engine_kwargs=engine_kwargs, **kwargs))

    def apply(self, func, *args, **kwargs):
        """
        Apply function group-wise and combine results.

        Example:
            >>> df.groupby('key').apply(lambda x: x.nlargest(2, 'val'))
        """
        return _wrap(self._gb.apply(func, *args, **kwargs))

    def filter(self, func, dropna=True, *args, **kwargs):
        """
        Return a copy of a DataFrame excluding elements from groups that
        do not satisfy the boolean criterion specified by func.

        Example:
            >>> df.groupby('key').filter(lambda x: x['val'].mean() > 1)
        """
        return _wrap(self._gb.filter(func, dropna=dropna, *args, **kwargs))

    def cumsum(self, axis=0, *args, **kwargs):
        return _wrap(self._gb.cumsum(axis=axis, *args, **kwargs))

    def cumprod(self, axis=0, *args, **kwargs):
        return _wrap(self._gb.cumprod(axis=axis, *args, **kwargs))

    def cummax(self, axis=0, **kwargs):
        return _wrap(self._gb.cummax(axis=axis, **kwargs))

    def cummin(self, axis=0, **kwargs):
        return _wrap(self._gb.cummin(axis=axis, **kwargs))

    def cumcount(self, ascending=True):
        return _wrap(self._gb.cumcount(ascending=ascending))

    def rank(self, method='average', ascending=True, na_option='keep',
             pct=False, axis=0):
        return _wrap(self._gb.rank(method=method, ascending=ascending,
                                    na_option=na_option, pct=pct, axis=axis))

    def shift(self, periods=1, freq=None, axis=0, fill_value=_pd.api.extensions.no_default):
        kw = dict(periods=periods, freq=freq, axis=axis)
        if fill_value is not _pd.api.extensions.no_default:
            kw['fill_value'] = fill_value
        return _wrap(self._gb.shift(**kw))

    def diff(self, periods=1, axis=0):
        return _wrap(self._gb.diff(periods=periods, axis=axis))

    def pct_change(self, periods=1, fill_method='ffill', limit=None, freq=None, axis=0):
        return _wrap(self._gb.pct_change(periods=periods, fill_method=fill_method,
                                          limit=limit, freq=freq, axis=axis))

    def fillna(self, value=None, method=None, axis=None, inplace=False,
               limit=None, downcast=None):
        return _wrap(self._gb.fillna(value=value, method=method, axis=axis,
                                      inplace=inplace, limit=limit,
                                      downcast=downcast))

    def ffill(self, limit=None):
        return _wrap(self._gb.ffill(limit=limit))

    def bfill(self, limit=None):
        return _wrap(self._gb.bfill(limit=limit))

    def head(self, n=5):
        return _wrap(self._gb.head(n=n))

    def tail(self, n=5):
        return _wrap(self._gb.tail(n=n))

    def sample(self, n=None, frac=None, replace=False, weights=None,
               random_state=None):
        return _wrap(self._gb.sample(n=n, frac=frac, replace=replace,
                                      weights=weights, random_state=random_state))

    def resample(self, rule, *args, **kwargs):
        return self._gb.resample(rule, *args, **kwargs)

    def rolling(self, window, *args, **kwargs):
        return self._gb.rolling(window, *args, **kwargs)

    def expanding(self, min_periods=1, *args, **kwargs):
        return self._gb.expanding(min_periods=min_periods, *args, **kwargs)

    def ewm(self, *args, **kwargs):
        return self._gb.ewm(*args, **kwargs)

    def pipe(self, func, *args, **kwargs):
        return _wrap(self._gb.pipe(func, *args, **kwargs))

    def get_group(self, name, obj=None):
        return _wrap(self._gb.get_group(name, obj=obj))

    def __iter__(self):
        for name, group in self._gb:
            yield name, _wrap(group)

    def __len__(self):
        return len(self._gb)

    def __getitem__(self, key):
        sub = self._gb[key]
        if isinstance(sub, (_pd.core.groupby.DataFrameGroupBy,
                             _pd.core.groupby.SeriesGroupBy)):
            return SeriesGroupBy(sub) if isinstance(sub, _pd.core.groupby.SeriesGroupBy) \
                else DataFrameGroupBy(sub)
        return sub

    @property
    def groups(self):
        return self._gb.groups

    @property
    def indices(self):
        return self._gb.indices

    @property
    def ngroups(self):
        return self._gb.ngroups

    def __repr__(self):
        return f"[pandasv2.DataFrameGroupBy]\n{repr(self._gb)}"


class SeriesGroupBy:
    """
    pandasv2 SeriesGroupBy — wraps pandas SeriesGroupBy.

    Example:
        >>> s = pd.Series([1, 2, 3], index=['a','b','a'])
        >>> s.groupby(level=0).sum()
    """

    def __init__(self, pandas_groupby):
        self._gb = pandas_groupby

    def sum(self, **kwargs):
        return _wrap(self._gb.sum(**kwargs))

    def mean(self, **kwargs):
        return _wrap(self._gb.mean(**kwargs))

    def median(self, **kwargs):
        return _wrap(self._gb.median(**kwargs))

    def min(self, **kwargs):
        return _wrap(self._gb.min(**kwargs))

    def max(self, **kwargs):
        return _wrap(self._gb.max(**kwargs))

    def count(self):
        return _wrap(self._gb.count())

    def std(self, **kwargs):
        return _wrap(self._gb.std(**kwargs))

    def var(self, **kwargs):
        return _wrap(self._gb.var(**kwargs))

    def prod(self, **kwargs):
        return _wrap(self._gb.prod(**kwargs))

    def first(self, **kwargs):
        return _wrap(self._gb.first(**kwargs))

    def last(self, **kwargs):
        return _wrap(self._gb.last(**kwargs))

    def nunique(self, dropna=True):
        return _wrap(self._gb.nunique(dropna=dropna))

    def size(self):
        return _wrap(self._gb.size())

    def agg(self, func=None, *args, **kwargs):
        return _wrap(self._gb.agg(func, *args, **kwargs))

    aggregate = agg

    def transform(self, func, *args, **kwargs):
        return _wrap(self._gb.transform(func, *args, **kwargs))

    def apply(self, func, *args, **kwargs):
        return _wrap(self._gb.apply(func, *args, **kwargs))

    def filter(self, func, dropna=True, *args, **kwargs):
        return _wrap(self._gb.filter(func, dropna=dropna, *args, **kwargs))

    def cumsum(self, **kwargs):
        return _wrap(self._gb.cumsum(**kwargs))

    def cummax(self, **kwargs):
        return _wrap(self._gb.cummax(**kwargs))

    def cummin(self, **kwargs):
        return _wrap(self._gb.cummin(**kwargs))

    def cumcount(self, ascending=True):
        return _wrap(self._gb.cumcount(ascending=ascending))

    def value_counts(self, normalize=False, sort=True, ascending=False,
                     bins=None, dropna=True):
        return _wrap(self._gb.value_counts(normalize=normalize, sort=sort,
                                            ascending=ascending, bins=bins,
                                            dropna=dropna))

    def describe(self, **kwargs):
        return _wrap(self._gb.describe(**kwargs))

    def pipe(self, func, *args, **kwargs):
        return _wrap(self._gb.pipe(func, *args, **kwargs))

    def get_group(self, name, obj=None):
        return _wrap(self._gb.get_group(name, obj=obj))

    def __iter__(self):
        for name, group in self._gb:
            yield name, _wrap(group)

    def __len__(self):
        return len(self._gb)

    @property
    def groups(self):
        return self._gb.groups

    @property
    def ngroups(self):
        return self._gb.ngroups

    def __repr__(self):
        return f"[pandasv2.SeriesGroupBy]\n{repr(self._gb)}"
