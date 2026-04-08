"""
Series - Full-featured pandas Series wrapper for pandasv2.

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Callable, Dict, Hashable, List, Optional, Union


class Series(_pd.Series):
    """
    pandasv2 Series — a full pandas.Series subclass.

    All standard pandas methods work unchanged.  Extra features:
    - to_json_safe() / from_json_safe()  – lossless JSON round-trip
    - to_web()                           – list/dict ready for HTTP responses

    Usage (drop-in replacement):
        >>> import pandasv2 as pd
        >>> s = pd.Series([1, 2, 3], name='values')
        >>> s.rolling(2).mean()
        >>> s.to_json_safe()
    """

    @property
    def _constructor(self):
        return Series

    @property
    def _constructor_expanddim(self):
        from .dataframe import DataFrame
        return DataFrame

    # ------------------------------------------------------------------
    # Extra serialisation helpers
    # ------------------------------------------------------------------

    def to_json_safe(self, **kwargs) -> str:
        """Serialize Series to JSON, handling all pandas/NumPy types."""
        from .core import to_json
        return to_json(self, **kwargs)

    @classmethod
    def from_json_safe(cls, json_str: str) -> 'Series':
        """Reconstruct Series from pandasv2 JSON string."""
        from .core import from_json
        result = from_json(json_str)
        return cls(result)

    def to_web(self) -> List:
        """Convert to a plain Python list suitable for web responses."""
        from .converters import series_to_list
        return series_to_list(self)

    # ------------------------------------------------------------------
    # Core ops — return Series subclass
    # ------------------------------------------------------------------

    def copy(self, deep: bool = True) -> 'Series':
        return Series(super().copy(deep=deep))

    def head(self, n: int = 5) -> 'Series':
        return Series(super().head(n))

    def tail(self, n: int = 5) -> 'Series':
        return Series(super().tail(n))

    def sample(self, n=None, frac=None, replace=False, weights=None,
               random_state=None, axis=None, ignore_index=False) -> 'Series':
        return Series(super().sample(n=n, frac=frac, replace=replace,
                                     weights=weights, random_state=random_state,
                                     axis=axis, ignore_index=ignore_index))

    def reset_index(self, level=None, drop=False, name=_pd.api.extensions.no_default,
                    inplace=False, allow_duplicates=False):
        result = super().reset_index(level=level, drop=drop, inplace=inplace)
        if inplace:
            return None
        if isinstance(result, _pd.DataFrame):
            from .dataframe import DataFrame
            return DataFrame(result)
        return Series(result)

    def sort_values(self, axis=0, ascending=True, inplace=False, kind='quicksort',
                    na_position='last', ignore_index=False, key=None) -> 'Series':
        result = super().sort_values(axis=axis, ascending=ascending, inplace=inplace,
                                     kind=kind, na_position=na_position,
                                     ignore_index=ignore_index, key=key)
        if inplace:
            return None
        return Series(result)

    def sort_index(self, axis=0, level=None, ascending=True, inplace=False,
                   kind='quicksort', na_position='last', sort_remaining=True,
                   ignore_index=False, key=None) -> 'Series':
        result = super().sort_index(axis=axis, level=level, ascending=ascending,
                                    inplace=inplace, kind=kind,
                                    na_position=na_position,
                                    sort_remaining=sort_remaining,
                                    ignore_index=ignore_index, key=key)
        if inplace:
            return None
        return Series(result)

    def drop(self, labels=None, axis=0, index=None, columns=None, level=None,
             inplace=False, errors='raise') -> 'Series':
        result = super().drop(labels=labels, axis=axis, index=index,
                              columns=columns, level=level, inplace=inplace,
                              errors=errors)
        if inplace:
            return None
        return Series(result)

    def rename(self, index=None, **kwargs) -> 'Series':
        result = super().rename(index=index, **kwargs)
        return Series(result)

    def fillna(self, value=None, method=None, axis=None, inplace=False,
               limit=None, downcast=None) -> 'Series':
        result = super().fillna(value=value, method=method, axis=axis,
                                inplace=inplace, limit=limit, downcast=downcast)
        if inplace:
            return None
        return Series(result)

    def dropna(self, axis=0, inplace=False, how=None) -> 'Series':
        result = super().dropna(axis=axis, inplace=inplace, how=how)
        if inplace:
            return None
        return Series(result)

    def astype(self, dtype, copy=True, errors='raise') -> 'Series':
        return Series(super().astype(dtype, copy=copy, errors=errors))

    def apply(self, func, args=(), **kwargs) -> Any:
        result = super().apply(func, args=args, **kwargs)
        if isinstance(result, _pd.Series):
            return Series(result)
        return result

    def map(self, arg, na_action=None) -> 'Series':
        return Series(super().map(arg, na_action=na_action))

    def pipe(self, func, *args, **kwargs):
        result = super().pipe(func, *args, **kwargs)
        if isinstance(result, _pd.Series):
            return Series(result)
        return result

    def where(self, cond, other=_np.nan, inplace=False, axis=None, level=None,
              errors='raise', try_cast=_pd.api.extensions.no_default) -> 'Series':
        result = super().where(cond, other=other, inplace=inplace, axis=axis,
                               level=level, errors=errors)
        if inplace:
            return None
        return Series(result)

    def mask(self, cond, other=_np.nan, inplace=False, axis=None, level=None,
             errors='raise', try_cast=_pd.api.extensions.no_default) -> 'Series':
        result = super().mask(cond, other=other, inplace=inplace, axis=axis,
                              level=level, errors=errors)
        if inplace:
            return None
        return Series(result)

    # Aggregations
    def value_counts(self, normalize=False, sort=True, ascending=False,
                     bins=None, dropna=True) -> 'Series':
        return Series(super().value_counts(normalize=normalize, sort=sort,
                                           ascending=ascending, bins=bins,
                                           dropna=dropna))

    def unique(self) -> _np.ndarray:
        return super().unique()

    def nunique(self, dropna=True) -> int:
        return super().nunique(dropna=dropna)

    def isin(self, values) -> 'Series':
        return Series(super().isin(values))

    def between(self, left, right, inclusive='both') -> 'Series':
        return Series(super().between(left, right, inclusive=inclusive))

    def clip(self, lower=None, upper=None, axis=None, inplace=False, *args, **kwargs) -> 'Series':
        result = super().clip(lower=lower, upper=upper, axis=axis,
                              inplace=inplace, *args, **kwargs)
        if inplace:
            return None
        return Series(result)

    def replace(self, to_replace=None, value=_pd.api.extensions.no_default,
                inplace=False, limit=None, regex=False, method=_pd.api.extensions.no_default) -> 'Series':
        result = super().replace(to_replace=to_replace, value=value,
                                 inplace=inplace, limit=limit, regex=regex,
                                 method=method)
        if inplace:
            return None
        return Series(result)

    def interpolate(self, method='linear', axis=0, limit=None, inplace=False,
                    limit_direction=None, limit_area=None, downcast=None, **kwargs) -> 'Series':
        result = super().interpolate(method=method, axis=axis, limit=limit,
                                     inplace=inplace, limit_direction=limit_direction,
                                     limit_area=limit_area, downcast=downcast, **kwargs)
        if inplace:
            return None
        return Series(result)

    def shift(self, periods=1, freq=None, axis=0, fill_value=_pd.api.extensions.no_default) -> 'Series':
        return Series(super().shift(periods=periods, freq=freq, axis=axis,
                                    fill_value=fill_value))

    def diff(self, periods=1) -> 'Series':
        return Series(super().diff(periods=periods))

    def pct_change(self, periods=1, fill_method='pad', limit=None, freq=None, **kwargs) -> 'Series':
        return Series(super().pct_change(periods=periods, fill_method=fill_method,
                                         limit=limit, freq=freq, **kwargs))

    def cumsum(self, axis=0, skipna=True, *args, **kwargs) -> 'Series':
        return Series(super().cumsum(axis=axis, skipna=skipna, *args, **kwargs))

    def cumprod(self, axis=0, skipna=True, *args, **kwargs) -> 'Series':
        return Series(super().cumprod(axis=axis, skipna=skipna, *args, **kwargs))

    def cummax(self, axis=0, skipna=True, *args, **kwargs) -> 'Series':
        return Series(super().cummax(axis=axis, skipna=skipna, *args, **kwargs))

    def cummin(self, axis=0, skipna=True, *args, **kwargs) -> 'Series':
        return Series(super().cummin(axis=axis, skipna=skipna, *args, **kwargs))

    def abs(self) -> 'Series':
        return Series(super().abs())

    def round(self, decimals=0, *args, **kwargs) -> 'Series':
        return Series(super().round(decimals=decimals, *args, **kwargs))

    def explode(self, ignore_index=False) -> 'Series':
        return Series(super().explode(ignore_index=ignore_index))

    def combine_first(self, other) -> 'Series':
        return Series(super().combine_first(other))

    def combine(self, other, func, fill_value=None) -> 'Series':
        return Series(super().combine(other, func, fill_value=fill_value))

    # ------------------------------------------------------------------
    # Window (explicit wrappers that return pandasv2 types)
    # ------------------------------------------------------------------

    def rolling(self, window, min_periods=None, center=False, win_type=None,
                on=None, closed=None, step=None, method='single'):
        """
        Provide rolling window calculations, returning pandasv2 Rolling.

        Example:
            >>> series.rolling(7).mean()
        """
        from .window import Rolling
        kw = dict(min_periods=min_periods, center=center,
                  win_type=win_type, on=on, closed=closed, method=method)
        if step is not None:
            kw['step'] = step
        return Rolling(super().rolling(window, **kw))

    def expanding(self, min_periods=1, method='single'):
        """
        Provide expanding window calculations, returning pandasv2 Expanding.

        Example:
            >>> series.expanding().mean()
        """
        from .window import Expanding
        return Expanding(super().expanding(min_periods=min_periods, method=method))

    def ewm(self, com=None, span=None, halflife=None, alpha=None,
            min_periods=0, adjust=True, ignore_na=False, times=None,
            method='single'):
        """
        Provide exponentially weighted calculations, returning pandasv2 EWM.

        Example:
            >>> series.ewm(span=12).mean()
        """
        from .window import ExponentialMovingWindow
        kw = dict(min_periods=min_periods, adjust=adjust,
                  ignore_na=ignore_na, method=method)
        for k, v in [('com', com), ('span', span), ('halflife', halflife),
                     ('alpha', alpha), ('times', times)]:
            if v is not None:
                kw[k] = v
        return ExponentialMovingWindow(super().ewm(**kw))

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    @property
    def plot(self):
        """
        Return a pandasv2 PlotAccessor for this Series.

        All standard plot types work (line, bar, hist, kde/density, etc.).
        Extra methods on the result:
          .to_base64()  — base64 PNG for API responses
          .to_html()    — inline <img> tag
          .to_bytes()   — raw PNG bytes
          .save(path)   — save to file

        Example:
            >>> series.plot.line().to_base64()
        """
        from .plotting import PlotAccessor
        return PlotAccessor(self)

    def __repr__(self) -> str:
        base = super().__repr__()
        return f"[pandasv2.Series]\n{base}"
