"""
pandasv2 — Full pandas replacement with built-in web superpowers.

Drop-in replacement for pandas:
    import pandasv2 as pd

    df = pd.DataFrame({'a': [1, 2, 3]})
    df.groupby('a').sum()
    df.to_json_safe()           # new: lossless JSON for web APIs
    df.to_web()                 # new: plain dict for HTTP responses

All standard pandas features are available:
- DataFrame / Series (full API)
- read_csv, read_excel, read_json, read_parquet, read_sql, … (all I/O)
- merge, concat, pivot_table, melt, crosstab, get_dummies, cut, qcut, …
- groupby with agg, transform, apply, filter, cumsum, rank, …
- .str, .dt, .cat accessors
- date_range, to_datetime, to_numeric, Timestamp, Timedelta, …
- All dtype objects, Index types, Categorical, NA, NaT, …
- JSONEncoder / JSONDecoder for web frameworks
- FastAPI / Flask / Django response helpers
- df.style  — full Styler with .to_web() and .to_base64() extras
- df.plot   — full PlotAccessor with .to_base64() / .to_html() / .to_bytes()
- rolling / expanding / ewm — all return pandasv2 types
- ExcelWriter — context manager with write_many / write_with_style
- pd.testing — extended assert_* suite
- pd.api.types — full type-checking + pandasv2 extras
- pd.arrays   — all extension arrays + to_arrow / from_arrow
- pd.plotting — scatter_matrix, andrews_curves, lag_plot, …
- pd.offsets  — all offset classes + business day helpers

Built by Mahesh Makvana
https://github.com/maheshmakvana/pandasv2
"""

__version__ = "2.0.0"
__author__ = "Mahesh Makvana"
__license__ = "MIT"

# ---------------------------------------------------------------------------
# Core pandas types (subclasses)
# ---------------------------------------------------------------------------
from .dataframe import DataFrame
from .series import Series

# ---------------------------------------------------------------------------
# I/O — read_*
# ---------------------------------------------------------------------------
from .io import (
    read_csv,
    read_excel,
    read_json,
    read_parquet,
    read_feather,
    read_orc,
    read_sql,
    read_sql_query,
    read_sql_table,
    read_html,
    read_xml,
    read_hdf,
    read_pickle,
    read_clipboard,
    read_fwf,
    read_table,
    read_spss,
    read_sas,
)

# ---------------------------------------------------------------------------
# Reshape / merge / concat
# ---------------------------------------------------------------------------
from .reshape import (
    merge,
    merge_asof,
    merge_ordered,
    concat,
    pivot,
    pivot_table,
    melt,
    wide_to_long,
    crosstab,
    cut,
    qcut,
    get_dummies,
    factorize,
    unique,
    value_counts,
    isna,
    isnull,
    notna,
    notnull,
)

# Try from_dummies (added in pandas 1.5)
try:
    from .reshape import from_dummies
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Analytics / type-conversion / date constructors
# ---------------------------------------------------------------------------
from .analytics import (
    date_range,
    bdate_range,
    period_range,
    timedelta_range,
    interval_range,
    to_datetime,
    to_timedelta,
    to_numeric,
    to_period,
    eval,
    json_normalize,
    # Index types
    Index,
    RangeIndex,
    MultiIndex,
    DatetimeIndex,
    TimedeltaIndex,
    PeriodIndex,
    CategoricalIndex,
    IntervalIndex,
    # Scalar types
    Timestamp,
    Timedelta,
    Period,
    Interval,
    NaT,
    NA,
    # Categorical
    Categorical,
    CategoricalDtype,
    # Dtype objects
    DatetimeTZDtype,
    IntervalDtype,
    PeriodDtype,
    SparseDtype,
    Int8Dtype,
    Int16Dtype,
    Int32Dtype,
    Int64Dtype,
    UInt8Dtype,
    UInt16Dtype,
    UInt32Dtype,
    UInt64Dtype,
    Float32Dtype,
    Float64Dtype,
    BooleanDtype,
    StringDtype,
    # Grouper helpers
    Grouper,
    NamedAgg,
    # Options
    set_option,
    get_option,
    reset_option,
    describe_option,
    option_context,
    # Offsets (basic alias — full namespace below)
    offsets,
)

# ---------------------------------------------------------------------------
# Original web serialisation helpers (kept for backwards compatibility)
# ---------------------------------------------------------------------------
from .core import (
    JSONEncoder,
    JSONDecoder,
    to_json,
    from_json,
    serialize,
    deserialize,
    DataFrameWrapper,
)

from .converters import (
    pandas_to_json,
    json_to_pandas,
    dataframe_to_records,
    series_to_list,
    infer_dtype,
    safe_cast,
    batch_convert,
    preserve_metadata,
)

from .integrations import (
    FastAPIResponse,
    FlaskResponse,
    DjangoResponse,
    setup_json_encoder,
    create_response_handler,
)

# ---------------------------------------------------------------------------
# GroupBy wrappers (used internally; exposed for type-checking)
# ---------------------------------------------------------------------------
from .groupby import DataFrameGroupBy, SeriesGroupBy

# ---------------------------------------------------------------------------
# ExcelWriter — context manager
# ---------------------------------------------------------------------------
from .excel_writer import ExcelWriter

# ---------------------------------------------------------------------------
# Styler — DataFrame.style returns this
# ---------------------------------------------------------------------------
from .styling import Styler

# ---------------------------------------------------------------------------
# Window wrappers
# ---------------------------------------------------------------------------
from .window import Rolling, Expanding, ExponentialMovingWindow, EWM

# ---------------------------------------------------------------------------
# testing namespace — enhanced with pandasv2 extras
# ---------------------------------------------------------------------------
from .testing import testing

# ---------------------------------------------------------------------------
# api namespace — pd.api.types, pd.api.extensions
# ---------------------------------------------------------------------------
from .api_types import api

# ---------------------------------------------------------------------------
# arrays namespace — pd.arrays.*
# ---------------------------------------------------------------------------
from .arrays import arrays

# ---------------------------------------------------------------------------
# plotting namespace — pd.plotting.*
# ---------------------------------------------------------------------------
from .plotting import plotting

# ---------------------------------------------------------------------------
# offsets namespace — full pd.offsets.* (overrides the basic alias above)
# ---------------------------------------------------------------------------
from .offsets_ext import offsets  # noqa: F811 — intentional override

# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------
__all__ = [
    # Core
    "DataFrame", "Series",
    # I/O
    "read_csv", "read_excel", "read_json", "read_parquet", "read_feather",
    "read_orc", "read_sql", "read_sql_query", "read_sql_table", "read_html",
    "read_xml", "read_hdf", "read_pickle", "read_clipboard", "read_fwf",
    "read_table", "read_spss", "read_sas",
    # Reshape
    "merge", "merge_asof", "merge_ordered", "concat", "pivot", "pivot_table",
    "melt", "wide_to_long", "crosstab", "cut", "qcut", "get_dummies",
    "from_dummies", "factorize", "unique", "value_counts",
    "isna", "isnull", "notna", "notnull",
    # Analytics / datetime
    "date_range", "bdate_range", "period_range", "timedelta_range",
    "interval_range", "to_datetime", "to_timedelta", "to_numeric",
    "to_period", "eval", "json_normalize",
    # Index types
    "Index", "RangeIndex", "MultiIndex", "DatetimeIndex", "TimedeltaIndex",
    "PeriodIndex", "CategoricalIndex", "IntervalIndex",
    # Scalar types
    "Timestamp", "Timedelta", "Period", "Interval", "NaT", "NA",
    # Categorical
    "Categorical", "CategoricalDtype",
    # Dtype objects
    "DatetimeTZDtype", "IntervalDtype", "PeriodDtype", "SparseDtype",
    "Int8Dtype", "Int16Dtype", "Int32Dtype", "Int64Dtype",
    "UInt8Dtype", "UInt16Dtype", "UInt32Dtype", "UInt64Dtype",
    "Float32Dtype", "Float64Dtype", "BooleanDtype", "StringDtype",
    # Grouper
    "Grouper", "NamedAgg",
    # Options
    "set_option", "get_option", "reset_option", "describe_option",
    "option_context",
    # Offsets namespace
    "offsets",
    # Web serialisation
    "JSONEncoder", "JSONDecoder", "to_json", "from_json",
    "serialize", "deserialize", "DataFrameWrapper",
    "pandas_to_json", "json_to_pandas", "dataframe_to_records",
    "series_to_list", "infer_dtype", "safe_cast", "batch_convert",
    "preserve_metadata",
    # Framework integrations
    "FastAPIResponse", "FlaskResponse", "DjangoResponse",
    "setup_json_encoder", "create_response_handler",
    # GroupBy
    "DataFrameGroupBy", "SeriesGroupBy",
    # ExcelWriter
    "ExcelWriter",
    # Styling
    "Styler",
    # Window
    "Rolling", "Expanding", "ExponentialMovingWindow", "EWM",
    # Namespaces
    "testing", "api", "arrays", "plotting",
]
