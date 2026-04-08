"""
Full pandas.tseries.offsets namespace for pandasv2.

Re-exports every offset class and alias from pandas.tseries.offsets
so users can do:
    import pandasv2 as pd
    pd.offsets.MonthEnd()
    pd.offsets.BusinessDay(2)
    pd.offsets.DateOffset(months=3)

Also provides helpers:
    to_offset(freq)   — convert string/timedelta to DateOffset
    offset_range(start, end, freq)  — generate list of offset-spaced dates

Built by Mahesh Makvana
"""

import pandas as _pd
import pandas.tseries.offsets as _offsets
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Re-export every offset class from pandas.tseries.offsets
# ---------------------------------------------------------------------------

# Base / generic
DateOffset = _offsets.DateOffset
BaseOffset = getattr(_offsets, 'BaseOffset', _offsets.DateOffset)

# Business day family
BusinessDay = _offsets.BusinessDay
BDay = _offsets.BDay
BusinessHour = _offsets.BusinessHour
BHour = getattr(_offsets, 'BHour', _offsets.BusinessHour)

# Custom business day
CustomBusinessDay = _offsets.CustomBusinessDay
CDay = _offsets.CDay
CustomBusinessHour = _offsets.CustomBusinessHour
CustomBusinessMonthBegin = getattr(_offsets, 'CustomBusinessMonthBegin', None)
CustomBusinessMonthEnd = getattr(_offsets, 'CustomBusinessMonthEnd', None)

# Month family
MonthEnd = _offsets.MonthEnd
MonthBegin = _offsets.MonthBegin
BusinessMonthEnd = _offsets.BusinessMonthEnd
BMonthEnd = _offsets.BMonthEnd
BusinessMonthBegin = _offsets.BusinessMonthBegin
BMonthBegin = _offsets.BMonthBegin
SemiMonthEnd = getattr(_offsets, 'SemiMonthEnd', None)
SemiMonthBegin = getattr(_offsets, 'SemiMonthBegin', None)

# Quarter family
QuarterEnd = _offsets.QuarterEnd
QuarterBegin = _offsets.QuarterBegin
BusinessQuarterEnd = getattr(_offsets, 'BusinessQuarterEnd',
                               getattr(_offsets, 'BQuarterEnd', None))
BusinessQuarterBegin = getattr(_offsets, 'BusinessQuarterBegin',
                                 getattr(_offsets, 'BQuarterBegin', None))
BQuarterEnd = getattr(_offsets, 'BQuarterEnd', None)
BQuarterBegin = getattr(_offsets, 'BQuarterBegin', None)

# Year family
YearEnd = _offsets.YearEnd
YearBegin = _offsets.YearBegin
BusinessYearEnd = getattr(_offsets, 'BusinessYearEnd',
                           getattr(_offsets, 'BYearEnd', None))
BusinessYearBegin = getattr(_offsets, 'BusinessYearBegin',
                              getattr(_offsets, 'BYearBegin', None))
BYearEnd = getattr(_offsets, 'BYearEnd', None)
BYearBegin = getattr(_offsets, 'BYearBegin', None)
FY5253 = getattr(_offsets, 'FY5253', None)
FY5253Quarter = getattr(_offsets, 'FY5253Quarter', None)

# Week family
Week = _offsets.Week
WeekOfMonth = getattr(_offsets, 'WeekOfMonth', None)
LastWeekOfMonth = getattr(_offsets, 'LastWeekOfMonth', None)

# Day / sub-day
Day = _offsets.Day
Hour = _offsets.Hour
Minute = _offsets.Minute
Second = _offsets.Second
Milli = _offsets.Milli
Micro = _offsets.Micro
Nano = _offsets.Nano
Millisecond = getattr(_offsets, 'Millisecond', _offsets.Milli)
Microsecond = getattr(_offsets, 'Microsecond', _offsets.Micro)
Nanosecond = getattr(_offsets, 'Nanosecond', _offsets.Nano)

# Easter
Easter = getattr(_offsets, 'Easter', None)

# Tick (abstract base)
Tick = getattr(_offsets, 'Tick', None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_offset(freq) -> _offsets.DateOffset:
    """
    Convert a frequency string, timedelta, or DateOffset to a DateOffset.

    Args:
        freq: Frequency string ('D', 'ME', 'QS', '2W-MON', etc.),
              datetime.timedelta, or existing DateOffset

    Returns:
        pandas DateOffset

    Example:
        >>> pd.offsets.to_offset('ME')          # <MonthEnd>
        >>> pd.offsets.to_offset('2W-MON')      # <2 * Weeks: weekday=0>
        >>> pd.offsets.to_offset(pd.Timedelta('1D'))
    """
    return _pd.tseries.frequencies.to_offset(freq)


def offset_range(
    start,
    end=None,
    periods: Optional[int] = None,
    freq=None,
) -> List[_pd.Timestamp]:
    """
    Generate a list of Timestamps spaced by *freq* between *start* and *end*.

    Thin wrapper around pd.date_range that returns a plain Python list.

    Args:
        start: Start date (string, datetime, or Timestamp)
        end: End date (optional if periods given)
        periods: Number of periods (optional if end given)
        freq: Frequency string or DateOffset (default 'D')

    Returns:
        List of pd.Timestamp objects

    Example:
        >>> pd.offsets.offset_range('2024-01-01', periods=5, freq='ME')
        [Timestamp('2024-01-31'), ...]
    """
    idx = _pd.date_range(start=start, end=end, periods=periods, freq=freq)
    return list(idx)


def business_days_between(start, end) -> int:
    """
    Count business days between two dates (inclusive of start, exclusive of end).

    Args:
        start: Start date
        end: End date

    Returns:
        Number of business days

    Example:
        >>> pd.offsets.business_days_between('2024-01-01', '2024-01-08')
        5
    """
    import numpy as _np
    return int(_np.busday_count(
        _pd.Timestamp(start).date(),
        _pd.Timestamp(end).date(),
    ))


def next_business_day(date=None) -> _pd.Timestamp:
    """
    Return the next business day after *date* (or today).

    Example:
        >>> pd.offsets.next_business_day('2024-01-05')   # Friday → Monday
    """
    ts = _pd.Timestamp(date) if date is not None else _pd.Timestamp.now()
    return ts + BusinessDay(1)


def prev_business_day(date=None) -> _pd.Timestamp:
    """
    Return the previous business day before *date* (or today).

    Example:
        >>> pd.offsets.prev_business_day('2024-01-08')   # Monday → Friday
    """
    ts = _pd.Timestamp(date) if date is not None else _pd.Timestamp.now()
    return ts - BusinessDay(1)


def month_end(date=None) -> _pd.Timestamp:
    """
    Return the last day of the month for *date*.

    Example:
        >>> pd.offsets.month_end('2024-01-15')
        Timestamp('2024-01-31 00:00:00')
    """
    ts = _pd.Timestamp(date) if date is not None else _pd.Timestamp.now()
    return ts + MonthEnd(0) if ts.is_month_end else ts + MonthEnd(1) - MonthEnd(1) + MonthEnd(0)


def quarter_end(date=None) -> _pd.Timestamp:
    """
    Return the last day of the quarter for *date*.

    Example:
        >>> pd.offsets.quarter_end('2024-02-10')
        Timestamp('2024-03-31 00:00:00')
    """
    ts = _pd.Timestamp(date) if date is not None else _pd.Timestamp.now()
    return ts + QuarterEnd(0) if ts == ts + QuarterEnd(0) else ts + QuarterEnd(1) - QuarterEnd(1) + QuarterEnd(0)


# ---------------------------------------------------------------------------
# Namespace class — exposed as pd.offsets
# ---------------------------------------------------------------------------

class _OffsetsNamespace:
    """
    Full pd.offsets namespace for pandasv2.

    Usage:
        >>> import pandasv2 as pd
        >>> pd.offsets.MonthEnd()
        >>> pd.offsets.BusinessDay(2)
        >>> pd.offsets.to_offset('ME')
        >>> pd.offsets.business_days_between('2024-01-01', '2024-01-31')
    """

    # Base
    DateOffset = DateOffset
    BaseOffset = BaseOffset

    # Business day
    BusinessDay = BusinessDay
    BDay = BDay
    BusinessHour = BusinessHour

    # Custom business day
    CustomBusinessDay = CustomBusinessDay
    CDay = CDay
    CustomBusinessHour = CustomBusinessHour

    # Month
    MonthEnd = MonthEnd
    MonthBegin = MonthBegin
    BusinessMonthEnd = BusinessMonthEnd
    BMonthEnd = BMonthEnd
    BusinessMonthBegin = BusinessMonthBegin
    BMonthBegin = BMonthBegin

    # Quarter
    QuarterEnd = QuarterEnd
    QuarterBegin = QuarterBegin

    # Year
    YearEnd = YearEnd
    YearBegin = YearBegin

    # Week
    Week = Week

    # Sub-day ticks
    Day = Day
    Hour = Hour
    Minute = Minute
    Second = Second
    Milli = Milli
    Micro = Micro
    Nano = Nano
    Millisecond = Millisecond
    Microsecond = Microsecond
    Nanosecond = Nanosecond

    # Version-guarded
    if BQuarterEnd is not None:
        BQuarterEnd = BQuarterEnd
    if BQuarterBegin is not None:
        BQuarterBegin = BQuarterBegin
    if BYearEnd is not None:
        BYearEnd = BYearEnd
    if BYearBegin is not None:
        BYearBegin = BYearBegin
    if WeekOfMonth is not None:
        WeekOfMonth = WeekOfMonth
    if LastWeekOfMonth is not None:
        LastWeekOfMonth = LastWeekOfMonth
    if SemiMonthEnd is not None:
        SemiMonthEnd = SemiMonthEnd
    if SemiMonthBegin is not None:
        SemiMonthBegin = SemiMonthBegin
    if FY5253 is not None:
        FY5253 = FY5253
    if FY5253Quarter is not None:
        FY5253Quarter = FY5253Quarter
    if Easter is not None:
        Easter = Easter
    if Tick is not None:
        Tick = Tick
    if CustomBusinessMonthBegin is not None:
        CustomBusinessMonthBegin = CustomBusinessMonthBegin
    if CustomBusinessMonthEnd is not None:
        CustomBusinessMonthEnd = CustomBusinessMonthEnd
    if BusinessQuarterEnd is not None:
        BusinessQuarterEnd = BusinessQuarterEnd
    if BusinessQuarterBegin is not None:
        BusinessQuarterBegin = BusinessQuarterBegin
    if BusinessYearEnd is not None:
        BusinessYearEnd = BusinessYearEnd
    if BusinessYearBegin is not None:
        BusinessYearBegin = BusinessYearBegin

    # Helpers
    to_offset = staticmethod(to_offset)
    offset_range = staticmethod(offset_range)
    business_days_between = staticmethod(business_days_between)
    next_business_day = staticmethod(next_business_day)
    prev_business_day = staticmethod(prev_business_day)
    month_end = staticmethod(month_end)
    quarter_end = staticmethod(quarter_end)


offsets = _OffsetsNamespace()
