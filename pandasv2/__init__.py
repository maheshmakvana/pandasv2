"""
pandasv2 - Advanced Pandas for Web Applications

Solves critical pain points when using pandas DataFrames in web applications:
- JSON serialization of NumPy/pandas types (int64, float64, NaT, etc.)
- Type-safe conversions with metadata preservation
- Zero-configuration integration with FastAPI, Flask, Django
- Round-trip serialization: serialize and deserialize with 100% fidelity
- Batch processing and streaming support
- Production-ready performance

Built by Mahesh Makvana
https://github.com/maheshmakvana/pandasv2
"""

__version__ = "1.0.0"
__author__ = "Mahesh Makvana"
__license__ = "MIT"

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

__all__ = [
    # Core functions
    "JSONEncoder",
    "JSONDecoder",
    "to_json",
    "from_json",
    "serialize",
    "deserialize",
    "DataFrameWrapper",
    # Converters
    "pandas_to_json",
    "json_to_pandas",
    "dataframe_to_records",
    "series_to_list",
    "infer_dtype",
    "safe_cast",
    "batch_convert",
    "preserve_metadata",
    # Integrations
    "FastAPIResponse",
    "FlaskResponse",
    "DjangoResponse",
    "setup_json_encoder",
    "create_response_handler",
]
