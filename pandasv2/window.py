"""
Window operation wrappers for pandasv2.

Provides explicit wrappers around pandas Rolling, Expanding, and ExponentialMovingWindow
objects so all results come back as pandasv2 DataFrame/Series instead of plain pandas.

Classes:
  Rolling    — wraps pandas.core.window.rolling.Rolling
  Expanding  — wraps pandas.core.window.expanding.Expanding
  ExponentialMovingWindow (EWM) — wraps pandas.core.window.ewm.ExponentialMovingWindow

Each class exposes the full pandas window API:
  agg, aggregate, apply, corr, count, cov, kurt, max, mean, median,
  min, quantile, rank, sem, skew, std, sum, var

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Callable, Dict, Optional, Union


def _wrap(obj):
    """Wrap a pandas result as a pandasv2 type."""
    from .dataframe import DataFrame
    from .series import Series
    if isinstance(obj, _pd.DataFrame):
        return DataFrame(obj)
    if isinstance(obj, _pd.Series):
        return Series(obj)
    return obj


class _BaseWindow:
    """
    Shared base for Rolling, Expanding, and EWM wrappers.

    All aggregation methods are delegated to the underlying pandas window
    and results are automatically wrapped.
    """

    def __init__(self, window_obj):
        self._w = window_obj

    def __getattr__(self, name):
        attr = getattr(self._w, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return _wrap(result) if isinstance(result, (_pd.DataFrame, _pd.Series)) else result
            return wrapper
        return attr

    # ------------------------------------------------------------------
    # Common aggregation methods (explicit for IDE completion)
    # ------------------------------------------------------------------

    def mean(self, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.mean(numeric_only=numeric_only, *args, **kwargs))

    def sum(self, numeric_only=False, min_count=0, *args, **kwargs):
        return _wrap(self._w.sum(numeric_only=numeric_only, min_count=min_count, *args, **kwargs))

    def min(self, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.min(numeric_only=numeric_only, *args, **kwargs))

    def max(self, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.max(numeric_only=numeric_only, *args, **kwargs))

    def std(self, ddof=1, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.std(ddof=ddof, numeric_only=numeric_only, *args, **kwargs))

    def var(self, ddof=1, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.var(ddof=ddof, numeric_only=numeric_only, *args, **kwargs))

    def sem(self, ddof=1, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.sem(ddof=ddof, numeric_only=numeric_only, *args, **kwargs))

    def count(self, numeric_only=False):
        return _wrap(self._w.count(numeric_only=numeric_only))

    def median(self, numeric_only=False, **kwargs):
        return _wrap(self._w.median(numeric_only=numeric_only, **kwargs))

    def kurt(self, numeric_only=False, **kwargs):
        return _wrap(self._w.kurt(numeric_only=numeric_only, **kwargs))

    def skew(self, numeric_only=False, **kwargs):
        return _wrap(self._w.skew(numeric_only=numeric_only, **kwargs))

    def corr(self, other=None, pairwise=None, ddof=1,
             numeric_only=False, **kwargs):
        return _wrap(self._w.corr(other=other, pairwise=pairwise,
                                   ddof=ddof, numeric_only=numeric_only, **kwargs))

    def cov(self, other=None, pairwise=None, ddof=1,
            numeric_only=False, **kwargs):
        return _wrap(self._w.cov(other=other, pairwise=pairwise,
                                  ddof=ddof, numeric_only=numeric_only, **kwargs))

    def apply(self, func: Callable, raw: bool = False, engine=None,
              engine_kwargs=None, args=None, kwargs=None):
        kw = dict(raw=raw)
        if engine is not None:
            kw['engine'] = engine
        if engine_kwargs is not None:
            kw['engine_kwargs'] = engine_kwargs
        if args is not None:
            kw['args'] = args
        if kwargs is not None:
            kw['kwargs'] = kwargs
        return _wrap(self._w.apply(func, **kw))

    def aggregate(self, func=None, *args, **kwargs):
        return _wrap(self._w.aggregate(func, *args, **kwargs))

    agg = aggregate

    def quantile(self, quantile: float, interpolation: str = 'linear',
                 numeric_only=False, **kwargs):
        return _wrap(self._w.quantile(quantile, interpolation=interpolation,
                                       numeric_only=numeric_only, **kwargs))

    def rank(self, method='average', ascending=True, pct=False,
             numeric_only=False, **kwargs):
        return _wrap(self._w.rank(method=method, ascending=ascending, pct=pct,
                                   numeric_only=numeric_only, **kwargs))


class Rolling(_BaseWindow):
    """
    pandasv2 Rolling window — wraps pandas Rolling with auto type-wrapping.

    Obtain via df.rolling(window) or series.rolling(window).

    Supports all pandas rolling parameters and methods, and returns
    pandasv2 DataFrame/Series from every aggregation.

    Extra:
        .to_web()  — compute rolling mean and return as plain dict for API responses

    Example:
        >>> df.rolling(7).mean()
        >>> series.rolling('30D').std()
        >>> df.rolling(3).agg({'price': 'mean', 'volume': 'sum'})
    """

    def __init__(self, window_obj):
        super().__init__(window_obj)

    # Rolling-specific extras
    def to_web(self, func: str = 'mean', **kwargs) -> Dict:
        """
        Compute a rolling aggregation and return as a plain dict for web responses.

        Args:
            func: Aggregation to apply ('mean', 'sum', 'std', etc.)
            **kwargs: Passed to the aggregation method

        Returns:
            Plain Python dict {column: [values]}

        Example:
            >>> df.rolling(7).to_web('mean')
        """
        result = getattr(self._w, func)(**kwargs)
        from .converters import pandas_to_json
        return pandas_to_json(result, orient='split')


class Expanding(_BaseWindow):
    """
    pandasv2 Expanding window — wraps pandas Expanding with auto type-wrapping.

    Obtain via df.expanding() or series.expanding().

    Example:
        >>> df.expanding().mean()
        >>> series.expanding(min_periods=5).std()
    """

    def __init__(self, window_obj):
        super().__init__(window_obj)


class ExponentialMovingWindow(_BaseWindow):
    """
    pandasv2 ExponentialMovingWindow — wraps pandas EWM with auto type-wrapping.

    Obtain via df.ewm(...) or series.ewm(...).

    Supports:
        mean, std, var, corr, cov

    Example:
        >>> df.ewm(span=12).mean()
        >>> series.ewm(alpha=0.3).std()
    """

    def __init__(self, window_obj):
        super().__init__(window_obj)

    def mean(self, numeric_only=False, ignore_na=False, *args, **kwargs):
        return _wrap(self._w.mean(numeric_only=numeric_only, *args, **kwargs))

    def std(self, bias=False, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.std(bias=bias, numeric_only=numeric_only, *args, **kwargs))

    def var(self, bias=False, numeric_only=False, *args, **kwargs):
        return _wrap(self._w.var(bias=bias, numeric_only=numeric_only, *args, **kwargs))

    def corr(self, other=None, pairwise=None, numeric_only=False, **kwargs):
        return _wrap(self._w.corr(other=other, pairwise=pairwise,
                                   numeric_only=numeric_only, **kwargs))

    def cov(self, other=None, pairwise=None, bias=False,
            numeric_only=False, **kwargs):
        return _wrap(self._w.cov(other=other, pairwise=pairwise, bias=bias,
                                  numeric_only=numeric_only, **kwargs))


# Alias for convenience
EWM = ExponentialMovingWindow


# ---------------------------------------------------------------------------
# Top-level constructors (called by DataFrame/Series in their rolling/ewm)
# ---------------------------------------------------------------------------

def rolling(obj, window, min_periods=None, center=False, win_type=None,
            on=None, axis=_pd.api.extensions.no_default, closed=None,
            step=None, method='single') -> Rolling:
    """
    Provide rolling window calculations on a DataFrame or Series.

    Args:
        obj: DataFrame or Series
        window: Size of the moving window (int or offset string)
        min_periods: Minimum number of observations required
        center: Set the window labels at the center of the window
        win_type: Window type string (e.g. 'boxcar', 'triang', 'blackman')
        on: Column to use as the datetime index (DataFrame only)
        closed: Define which observations are closed on each end
        step: Evaluate the window at every step result
        method: 'single' or 'table' (table operates on entire DataFrame)

    Example:
        >>> from pandasv2.window import rolling
        >>> rolling(df, 7).mean()
    """
    kw = dict(min_periods=min_periods, center=center, win_type=win_type,
              on=on, closed=closed, method=method)
    if step is not None:
        kw['step'] = step
    if axis is not _pd.api.extensions.no_default:
        kw['axis'] = axis
    return Rolling(obj.rolling(window, **kw))


def expanding(obj, min_periods: int = 1,
              axis=_pd.api.extensions.no_default,
              method: str = 'single') -> Expanding:
    """
    Provide expanding window calculations on a DataFrame or Series.

    Args:
        obj: DataFrame or Series
        min_periods: Minimum number of observations required
        method: 'single' or 'table'

    Example:
        >>> from pandasv2.window import expanding
        >>> expanding(df, min_periods=5).mean()
    """
    kw = dict(min_periods=min_periods, method=method)
    if axis is not _pd.api.extensions.no_default:
        kw['axis'] = axis
    return Expanding(obj.expanding(**kw))


def ewm(obj, com=None, span=None, halflife=None, alpha=None,
        min_periods: int = 0, adjust: bool = True, ignore_na: bool = False,
        axis=_pd.api.extensions.no_default,
        times=None, method: str = 'single') -> ExponentialMovingWindow:
    """
    Provide exponentially weighted calculations on a DataFrame or Series.

    Args:
        obj: DataFrame or Series
        com: Specify decay in terms of center of mass
        span: Specify decay in terms of span
        halflife: Specify decay in terms of half-life
        alpha: Specify smoothing factor directly (0 < alpha <= 1)
        min_periods: Minimum number of observations
        adjust: Divide by decaying adjustment factor
        ignore_na: Ignore missing values when calculating weights
        times: Times corresponding to observations (for halflife)
        method: 'single' or 'table'

    Example:
        >>> from pandasv2.window import ewm
        >>> ewm(df, span=12).mean()
    """
    kw = dict(min_periods=min_periods, adjust=adjust, ignore_na=ignore_na,
              method=method)
    for k, v in [('com', com), ('span', span), ('halflife', halflife),
                 ('alpha', alpha), ('times', times)]:
        if v is not None:
            kw[k] = v
    if axis is not _pd.api.extensions.no_default:
        kw['axis'] = axis
    return ExponentialMovingWindow(obj.ewm(**kw))
