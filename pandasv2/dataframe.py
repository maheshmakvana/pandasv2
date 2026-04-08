"""
DataFrame - Full-featured pandas DataFrame wrapper for pandasv2.

Wraps pandas.DataFrame and re-exposes every major API so users can
import pandasv2 as pd and use DataFrame, Series, etc. as drop-in
replacements, while gaining built-in JSON serialization and web helpers.

Built by Mahesh Makvana
"""

import pandas as _pd
import numpy as _np
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Sequence, Tuple, Union


class DataFrame(_pd.DataFrame):
    """
    pandasv2 DataFrame — a full pandas.DataFrame subclass.

    All standard pandas methods work unchanged.  Extra features:
    - to_json_safe() / from_json_safe()  – lossless JSON round-trip
    - to_web()                           – dict ready for any HTTP response
    - Enhanced repr for notebooks

    Usage (drop-in replacement):
        >>> import pandasv2 as pd
        >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4.0, 5.0, 6.0]})
        >>> df.groupby('a').sum()
        >>> df.to_json_safe()
    """

    # Preserve subclass through pandas operations
    @property
    def _constructor(self):
        return DataFrame

    @property
    def _constructor_sliced(self):
        from .series import Series
        return Series

    # ------------------------------------------------------------------
    # Extra serialisation helpers
    # ------------------------------------------------------------------

    def to_json_safe(self, orient: str = 'records', **kwargs) -> str:
        """
        Serialize DataFrame to JSON, handling all pandas/NumPy types.

        Args:
            orient: 'records' | 'split' | 'index' | 'columns' | 'values' | 'table'
            **kwargs: Passed to pandas DataFrame.to_json()

        Returns:
            JSON string safe for any web framework

        Example:
            >>> df.to_json_safe(orient='records')
        """
        from .core import to_json
        return to_json(self, **kwargs)

    @classmethod
    def from_json_safe(cls, json_str: str) -> 'DataFrame':
        """
        Reconstruct DataFrame from pandasv2 JSON string.

        Example:
            >>> df = DataFrame.from_json_safe(json_str)
        """
        from .core import from_json
        result = from_json(json_str)
        return cls(result)

    def to_web(self, orient: str = 'records', include_dtypes: bool = False) -> Dict:
        """
        Convert to a plain dict suitable for web responses.

        Args:
            orient: How to structure the data ('records', 'split', 'index')
            include_dtypes: Include dtype info for reconstruction

        Returns:
            Plain Python dict (no NumPy types)

        Example:
            >>> @app.get('/data')
            >>> def endpoint():
            >>>     return df.to_web()
        """
        from .converters import pandas_to_json
        return pandas_to_json(self, orient=orient, include_metadata=include_dtypes)

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_records(cls, data, columns=None, **kwargs) -> 'DataFrame':
        """Create from list of dicts/tuples (alias wrapping pd.DataFrame.from_records)."""
        return cls(_pd.DataFrame.from_records(data, columns=columns, **kwargs))

    @classmethod
    def from_dict(cls, data, orient='columns', dtype=None, columns=None) -> 'DataFrame':
        """Create from dict of arrays/dicts (alias wrapping pd.DataFrame.from_dict)."""
        return cls(_pd.DataFrame.from_dict(data, orient=orient, dtype=dtype, columns=columns))

    # ------------------------------------------------------------------
    # Quality-of-life extras
    # ------------------------------------------------------------------

    def head(self, n: int = 5) -> 'DataFrame':
        return DataFrame(super().head(n))

    def tail(self, n: int = 5) -> 'DataFrame':
        return DataFrame(super().tail(n))

    def sample(self, n=None, frac=None, replace=False, weights=None,
               random_state=None, axis=None, ignore_index=False) -> 'DataFrame':
        return DataFrame(super().sample(n=n, frac=frac, replace=replace,
                                        weights=weights, random_state=random_state,
                                        axis=axis, ignore_index=ignore_index))

    def copy(self, deep: bool = True) -> 'DataFrame':
        return DataFrame(super().copy(deep=deep))

    def reset_index(self, level=None, drop=False, inplace=False,
                    col_level=0, col_fill='') -> 'DataFrame':
        result = super().reset_index(level=level, drop=drop, inplace=inplace,
                                     col_level=col_level, col_fill=col_fill)
        if inplace:
            return None
        return DataFrame(result)

    def set_index(self, keys, drop=True, append=False, inplace=False,
                  verify_integrity=False) -> 'DataFrame':
        result = super().set_index(keys, drop=drop, append=append,
                                   inplace=inplace, verify_integrity=verify_integrity)
        if inplace:
            return None
        return DataFrame(result)

    def sort_values(self, by, axis=0, ascending=True, inplace=False,
                    kind='quicksort', na_position='last', ignore_index=False,
                    key=None) -> 'DataFrame':
        result = super().sort_values(by=by, axis=axis, ascending=ascending,
                                     inplace=inplace, kind=kind,
                                     na_position=na_position,
                                     ignore_index=ignore_index, key=key)
        if inplace:
            return None
        return DataFrame(result)

    def sort_index(self, axis=0, level=None, ascending=True, inplace=False,
                   kind='quicksort', na_position='last', sort_remaining=True,
                   ignore_index=False, key=None) -> 'DataFrame':
        result = super().sort_index(axis=axis, level=level, ascending=ascending,
                                    inplace=inplace, kind=kind,
                                    na_position=na_position,
                                    sort_remaining=sort_remaining,
                                    ignore_index=ignore_index, key=key)
        if inplace:
            return None
        return DataFrame(result)

    def drop(self, labels=None, axis=0, index=None, columns=None,
             level=None, inplace=False, errors='raise') -> 'DataFrame':
        result = super().drop(labels=labels, axis=axis, index=index,
                              columns=columns, level=level, inplace=inplace,
                              errors=errors)
        if inplace:
            return None
        return DataFrame(result)

    def rename(self, mapper=None, index=None, columns=None, axis=None,
               copy=True, inplace=False, level=None, errors='ignore') -> 'DataFrame':
        result = super().rename(mapper=mapper, index=index, columns=columns,
                                axis=axis, copy=copy, inplace=inplace,
                                level=level, errors=errors)
        if inplace:
            return None
        return DataFrame(result)

    def fillna(self, value=None, method=None, axis=None, inplace=False,
               limit=None, downcast=None) -> 'DataFrame':
        result = super().fillna(value=value, method=method, axis=axis,
                                inplace=inplace, limit=limit, downcast=downcast)
        if inplace:
            return None
        return DataFrame(result)

    def dropna(self, axis=0, how=_pd.api.extensions.no_default, thresh=_pd.api.extensions.no_default,
               subset=None, inplace=False) -> 'DataFrame':
        kw = dict(axis=axis, subset=subset, inplace=inplace)
        if thresh is not _pd.api.extensions.no_default:
            kw['thresh'] = thresh
        else:
            kw['how'] = 'any' if how is _pd.api.extensions.no_default else how
        result = super().dropna(**kw)
        if inplace:
            return None
        return DataFrame(result)

    def astype(self, dtype, copy=True, errors='raise') -> 'DataFrame':
        return DataFrame(super().astype(dtype, copy=copy, errors=errors))

    def apply(self, func, axis=0, raw=False, result_type=None, args=(), **kwargs):
        result = super().apply(func, axis=axis, raw=raw,
                               result_type=result_type, args=args, **kwargs)
        if isinstance(result, _pd.DataFrame):
            return DataFrame(result)
        return result

    def applymap(self, func, na_action=None, **kwargs) -> 'DataFrame':
        return DataFrame(super().applymap(func, na_action=na_action, **kwargs))

    def assign(self, **kwargs) -> 'DataFrame':
        return DataFrame(super().assign(**kwargs))

    def where(self, cond, other=_np.nan, inplace=False, axis=None, level=None,
              errors='raise', try_cast=_pd.api.extensions.no_default) -> 'DataFrame':
        result = super().where(cond, other=other, inplace=inplace, axis=axis,
                               level=level, errors=errors)
        if inplace:
            return None
        return DataFrame(result)

    def mask(self, cond, other=_np.nan, inplace=False, axis=None, level=None,
             errors='raise', try_cast=_pd.api.extensions.no_default) -> 'DataFrame':
        result = super().mask(cond, other=other, inplace=inplace, axis=axis,
                              level=level, errors=errors)
        if inplace:
            return None
        return DataFrame(result)

    def query(self, expr: str, inplace: bool = False, **kwargs) -> 'DataFrame':
        result = super().query(expr, inplace=inplace, **kwargs)
        if inplace:
            return None
        return DataFrame(result)

    def eval(self, expr: str, inplace: bool = False, **kwargs):
        result = super().eval(expr, inplace=inplace, **kwargs)
        if isinstance(result, _pd.DataFrame):
            return DataFrame(result)
        return result

    def pipe(self, func, *args, **kwargs):
        result = super().pipe(func, *args, **kwargs)
        if isinstance(result, _pd.DataFrame):
            return DataFrame(result)
        return result

    def merge(self, right, how='inner', on=None, left_on=None, right_on=None,
              left_index=False, right_index=False, sort=False, suffixes=('_x', '_y'),
              copy=True, indicator=False, validate=None) -> 'DataFrame':
        result = super().merge(right, how=how, on=on, left_on=left_on,
                               right_on=right_on, left_index=left_index,
                               right_index=right_index, sort=sort,
                               suffixes=suffixes, copy=copy,
                               indicator=indicator, validate=validate)
        return DataFrame(result)

    def join(self, other, on=None, how='left', lsuffix='', rsuffix='',
             sort=False) -> 'DataFrame':
        return DataFrame(super().join(other, on=on, how=how, lsuffix=lsuffix,
                                      rsuffix=rsuffix, sort=sort))

    def pivot(self, index=None, columns=None, values=None) -> 'DataFrame':
        return DataFrame(super().pivot(index=index, columns=columns, values=values))

    def pivot_table(self, values=None, index=None, columns=None, aggfunc='mean',
                    fill_value=None, margins=False, dropna=True,
                    margins_name='All', observed=False, sort=True) -> 'DataFrame':
        return DataFrame(super().pivot_table(
            values=values, index=index, columns=columns, aggfunc=aggfunc,
            fill_value=fill_value, margins=margins, dropna=dropna,
            margins_name=margins_name, observed=observed, sort=sort))

    def melt(self, id_vars=None, value_vars=None, var_name=None,
             value_name='value', col_level=None, ignore_index=True) -> 'DataFrame':
        return DataFrame(super().melt(
            id_vars=id_vars, value_vars=value_vars, var_name=var_name,
            value_name=value_name, col_level=col_level, ignore_index=ignore_index))

    def stack(self, level=-1, dropna=True):
        result = super().stack(level=level, dropna=dropna)
        if isinstance(result, _pd.DataFrame):
            return DataFrame(result)
        from .series import Series
        return Series(result)

    def unstack(self, level=-1, fill_value=None):
        result = super().unstack(level=level, fill_value=fill_value)
        if isinstance(result, _pd.DataFrame):
            return DataFrame(result)
        from .series import Series
        return Series(result)

    def transpose(self, *args, copy=False) -> 'DataFrame':
        return DataFrame(super().transpose(*args, copy=copy))

    @property
    def T(self) -> 'DataFrame':
        return DataFrame(super().T)

    def explode(self, column, ignore_index=False) -> 'DataFrame':
        return DataFrame(super().explode(column, ignore_index=ignore_index))

    def crosstab(self, *args, **kwargs) -> 'DataFrame':
        return DataFrame(_pd.crosstab(*args, **kwargs))

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def filter(self, items=None, like=None, regex=None, axis=None) -> 'DataFrame':
        return DataFrame(super().filter(items=items, like=like, regex=regex, axis=axis))

    def select_dtypes(self, include=None, exclude=None) -> 'DataFrame':
        return DataFrame(super().select_dtypes(include=include, exclude=exclude))

    def isin(self, values) -> 'DataFrame':
        return DataFrame(super().isin(values))

    def between_time(self, start_time, end_time, include_start=True,
                     include_end=True, axis=None) -> 'DataFrame':
        return DataFrame(super().between_time(start_time, end_time,
                                              include_start=include_start,
                                              include_end=include_end, axis=axis))

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    @property
    def style(self):
        """
        Return a pandasv2 Styler for this DataFrame.

        All pandas Styler methods work unchanged, plus extra helpers:
          .to_web()       — rendered HTML string for web responses
          .to_json_safe() — underlying data as lossless JSON
          .export_css()   — extract generated CSS rules

        Example:
            >>> df.style.background_gradient().to_web()
        """
        from .styling import Styler
        return Styler(super().style)

    # ------------------------------------------------------------------
    # Window (explicit wrappers that return pandasv2 types)
    # ------------------------------------------------------------------

    def rolling(self, window, min_periods=None, center=False, win_type=None,
                on=None, closed=None, step=None, method='single'):
        """
        Provide rolling window calculations, returning pandasv2 Rolling.

        Example:
            >>> df.rolling(7).mean()
            >>> df.rolling('30D', on='date').std()
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
            >>> df.expanding().mean()
        """
        from .window import Expanding
        return Expanding(super().expanding(min_periods=min_periods, method=method))

    def ewm(self, com=None, span=None, halflife=None, alpha=None,
            min_periods=0, adjust=True, ignore_na=False, times=None,
            method='single'):
        """
        Provide exponentially weighted calculations, returning pandasv2 EWM.

        Example:
            >>> df.ewm(span=12).mean()
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
        Return a pandasv2 PlotAccessor for this DataFrame.

        All standard plot types work (line, bar, hist, scatter, etc.).
        Extra methods on the result object:
          .to_base64()  — base64 PNG for API responses
          .to_html()    — inline <img> tag
          .to_bytes()   — raw PNG bytes
          .save(path)   — save to file

        Example:
            >>> df.plot.bar(x='date', y='value').to_web()
        """
        from .plotting import PlotAccessor
        return PlotAccessor(self)

    def __repr__(self) -> str:
        base = super().__repr__()
        return f"[pandasv2.DataFrame]\n{base}"
