"""
Accessor namespaces for pandasv2.

pandas exposes .str, .dt, .cat, .sparse, .plot accessors on Series.
Because pandasv2.Series is a true pandas.Series subclass, those accessors
work transparently.  This module documents them and provides lightweight
wrappers where useful.

Built by Mahesh Makvana
"""

# All accessors are inherited from pandas.Series via the subclass relationship.
# No monkey-patching needed.  This module exposes documentation helpers
# and any extra accessors we add on top.

import pandas as _pd
from typing import Any

__all__ = [
    'StringAccessorDoc',
    'DatetimeAccessorDoc',
    'CategoricalAccessorDoc',
]


class StringAccessorDoc:
    """
    Documentation for the .str accessor.

    Available on any pandasv2.Series with object or string dtype via  s.str.*

    Methods
    -------
    s.str.contains(pat, case=True, flags=0, na=None, regex=True)
    s.str.startswith(pat, na=None)
    s.str.endswith(pat, na=None)
    s.str.match(pat, case=True, flags=0, na=None)
    s.str.fullmatch(pat, case=True, flags=0, na=None)
    s.str.extract(pat, flags=0, expand=True)
    s.str.extractall(pat, flags=0)
    s.str.findall(pat, flags=0)
    s.str.replace(pat, repl, n=-1, case=None, flags=0, regex=True)
    s.str.split(pat=None, n=-1, expand=False, regex=None)
    s.str.rsplit(pat=None, n=-1, expand=False)
    s.str.get(i)
    s.str.join(sep)
    s.str.get_dummies(sep='|')
    s.str.strip(to_strip=None)
    s.str.lstrip(to_strip=None)
    s.str.rstrip(to_strip=None)
    s.str.upper()
    s.str.lower()
    s.str.title()
    s.str.capitalize()
    s.str.swapcase()
    s.str.casefold()
    s.str.center(width, fillchar=' ')
    s.str.ljust(width, fillchar=' ')
    s.str.rjust(width, fillchar=' ')
    s.str.zfill(width)
    s.str.pad(width, side='left', fillchar=' ')
    s.str.slice(start=None, stop=None, step=None)
    s.str.slice_replace(start=None, stop=None, repl=None)
    s.str.count(pat, flags=0)
    s.str.find(sub, start=0, end=None)
    s.str.rfind(sub, start=0, end=None)
    s.str.index(sub, start=0, end=None)
    s.str.rindex(sub, start=0, end=None)
    s.str.len()
    s.str.encode(encoding, errors='strict')
    s.str.decode(encoding, errors='strict')
    s.str.normalize(form)
    s.str.isalpha()
    s.str.isnumeric()
    s.str.isalnum()
    s.str.isdigit()
    s.str.isdecimal()
    s.str.isspace()
    s.str.islower()
    s.str.isupper()
    s.str.istitle()
    s.str.wrap(width, **kwargs)
    s.str.repeat(repeats)
    s.str.cat(others=None, sep=None, na_rep=None, join='left')
    s.str.translate(table)
    s.str.removeprefix(prefix)
    s.str.removesuffix(suffix)

    Example:
        >>> import pandasv2 as pd
        >>> s = pd.Series(['Hello World', 'foo bar', None])
        >>> s.str.upper()
        >>> s.str.contains('World')
        >>> s.str.split(' ', expand=True)
    """


class DatetimeAccessorDoc:
    """
    Documentation for the .dt accessor.

    Available on any pandasv2.Series with datetime64 / timedelta64 dtype
    via  s.dt.*

    Properties (datetime)
    ----------------------
    s.dt.year, s.dt.month, s.dt.day
    s.dt.hour, s.dt.minute, s.dt.second, s.dt.microsecond, s.dt.nanosecond
    s.dt.date, s.dt.time, s.dt.timetz
    s.dt.dayofweek  (Monday=0, Sunday=6)
    s.dt.day_of_week
    s.dt.dayofyear
    s.dt.day_of_year
    s.dt.days_in_month
    s.dt.quarter
    s.dt.week (deprecated → isocalendar().week)
    s.dt.weekofyear (deprecated)
    s.dt.is_month_start, s.dt.is_month_end
    s.dt.is_quarter_start, s.dt.is_quarter_end
    s.dt.is_year_start, s.dt.is_year_end
    s.dt.is_leap_year
    s.dt.tz

    Methods (datetime)
    ------------------
    s.dt.to_period(freq)
    s.dt.to_pydatetime()
    s.dt.tz_localize(tz, ambiguous='raise', nonexistent='raise')
    s.dt.tz_convert(tz)
    s.dt.normalize()
    s.dt.strftime(date_format)
    s.dt.round(freq, ambiguous='raise', nonexistent='raise')
    s.dt.floor(freq, ambiguous='raise', nonexistent='raise')
    s.dt.ceil(freq, ambiguous='raise', nonexistent='raise')
    s.dt.month_name(locale=None)
    s.dt.day_name(locale=None)
    s.dt.isocalendar()

    Properties (timedelta)
    ----------------------
    s.dt.days, s.dt.seconds, s.dt.microseconds, s.dt.nanoseconds
    s.dt.components
    s.dt.total_seconds()

    Example:
        >>> import pandasv2 as pd
        >>> s = pd.Series(pd.date_range('2024-01-01', periods=5, freq='ME'))
        >>> s.dt.year
        >>> s.dt.month_name()
        >>> s.dt.strftime('%Y-%m')
    """


class CategoricalAccessorDoc:
    """
    Documentation for the .cat accessor.

    Available on any pandasv2.Series with CategoricalDtype via  s.cat.*

    Properties
    ----------
    s.cat.categories          – Index of categories
    s.cat.ordered             – bool
    s.cat.codes               – integer codes

    Methods
    -------
    s.cat.rename_categories(new_categories)
    s.cat.reorder_categories(new_categories, ordered=None)
    s.cat.add_categories(new_categories)
    s.cat.remove_categories(removals)
    s.cat.remove_unused_categories()
    s.cat.set_categories(new_categories, ordered=None, rename=False)
    s.cat.as_ordered()
    s.cat.as_unordered()

    Example:
        >>> import pandasv2 as pd
        >>> s = pd.Series(pd.Categorical(['a','b','a','c'], ordered=True))
        >>> s.cat.categories
        >>> s.cat.codes
        >>> s.cat.add_categories(['d'])
    """
