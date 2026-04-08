"""
Unit tests for pandas2 core functionality.

Tests JSON serialization, deserialization, and DataFrame handling.

Built by Mahesh Makvana
"""

import pytest
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import pandas2
from pandas2 import (
    JSONEncoder, JSONDecoder,
    to_json, from_json,
    serialize, deserialize,
    DataFrameWrapper,
)
from pandas2.converters import (
    pandas_to_json, json_to_pandas,
    dataframe_to_records, series_to_list,
    infer_dtype, safe_cast, batch_convert,
)


class TestJSONEncoder:
    """Test JSONEncoder with various pandas/NumPy types."""

    def test_numpy_int64(self):
        data = {'value': np.int64(42)}
        result = json.dumps(data, cls=JSONEncoder)
        assert '42' in result

    def test_numpy_float64(self):
        data = {'value': np.float64(3.14)}
        result = json.dumps(data, cls=JSONEncoder)
        assert '3.14' in result

    def test_numpy_nan(self):
        data = {'value': np.nan}
        result = json.dumps(data, cls=JSONEncoder)
        assert 'null' in result or 'NaN' in result.lower()

    def test_pandas_nat(self):
        data = {'value': pd.NaT}
        result = json.dumps(data, cls=JSONEncoder)
        assert 'null' in result or result is not None

    def test_pandas_timestamp(self):
        ts = pd.Timestamp('2024-01-15')
        data = {'value': ts}
        result = json.dumps(data, cls=JSONEncoder)
        assert '2024-01-15' in result

    def test_pandas_timedelta(self):
        td = pd.Timedelta(days=5)
        data = {'value': td}
        result = json.dumps(data, cls=JSONEncoder)
        assert result is not None

    def test_dataframe(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        result = json.dumps(df, cls=JSONEncoder)
        data = json.loads(result)
        assert data['__type__'] == 'DataFrame'
        assert len(data['data']) == 3

    def test_series(self):
        s = pd.Series([1, 2, 3], name='test')
        result = json.dumps(s, cls=JSONEncoder)
        data = json.loads(result)
        assert data['__type__'] == 'Series'
        assert data['name'] == 'test'

    def test_dataframe_with_nan(self):
        df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [4.0, 5.0, 6.0]})
        result = json.dumps(df, cls=JSONEncoder)
        data = json.loads(result)
        assert data['data'][1]['a'] is None


class TestJSONDecoder:
    """Test JSONDecoder for reconstructing pandas objects."""

    def test_decode_dataframe(self):
        original_df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        json_str = json.dumps(original_df, cls=JSONEncoder)
        restored_df = json.loads(json_str, cls=JSONDecoder)

        assert isinstance(restored_df, pd.DataFrame)
        assert list(restored_df.columns) == ['a', 'b']
        assert len(restored_df) == 3

    def test_decode_series(self):
        original_series = pd.Series([1, 2, 3], name='test')
        json_str = json.dumps(original_series, cls=JSONEncoder)
        restored_series = json.loads(json_str, cls=JSONDecoder)

        assert isinstance(restored_series, pd.Series)
        assert restored_series.name == 'test'
        assert len(restored_series) == 3

    def test_round_trip_dataframe(self):
        original_df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.1, 2.2, 3.3],
            'str_col': ['a', 'b', 'c'],
        })
        json_str = json.dumps(original_df, cls=JSONEncoder)
        restored_df = json.loads(json_str, cls=JSONDecoder)

        pd.testing.assert_frame_equal(original_df, restored_df)


class TestToJsonFromJson:
    """Test to_json and from_json convenience functions."""

    def test_to_json_dataframe(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        json_str = to_json(df)
        assert isinstance(json_str, str)
        assert '__type__' in json_str
        assert 'DataFrame' in json_str

    def test_from_json_dataframe(self):
        json_str = '{"__type__": "DataFrame", "data": [{"a": 1}, {"a": 2}], "columns": ["a"]}'
        df = from_json(json_str)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['a']

    def test_round_trip_to_from_json(self):
        original_df = pd.DataFrame({'x': [10, 20, 30], 'y': [100, 200, 300]})
        json_str = to_json(original_df)
        restored_df = from_json(json_str)

        pd.testing.assert_frame_equal(original_df, restored_df)


class TestSerializeDeserialize:
    """Test serialize and deserialize with metadata."""

    def test_serialize_dataframe(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [1.1, 2.2, 3.3]})
        serialized = serialize(df)

        assert serialized['__type__'] == 'DataFrame'
        assert 'metadata' in serialized
        assert serialized['metadata']['shape'] == (3, 2)

    def test_deserialize_dataframe(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [1.1, 2.2, 3.3]})
        serialized = serialize(df)
        deserialized = deserialize(serialized)

        pd.testing.assert_frame_equal(df, deserialized)

    def test_round_trip_with_metadata(self):
        original_df = pd.DataFrame({
            'int_col': np.array([1, 2, 3], dtype=np.int64),
            'float_col': np.array([1.1, 2.2, 3.3], dtype=np.float32),
        })
        serialized = serialize(original_df, include_metadata=True)
        deserialized = deserialize(serialized)

        assert deserialized.shape == original_df.shape
        assert list(deserialized.columns) == list(original_df.columns)


class TestDataFrameWrapper:
    """Test DataFrameWrapper convenience class."""

    def test_wrapper_to_json(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        wrapper = DataFrameWrapper(df)
        json_str = wrapper.to_json()

        assert isinstance(json_str, str)
        assert '__type__' in json_str

    def test_wrapper_from_json(self):
        json_str = '{"__type__": "DataFrame", "data": [{"a": 1}], "columns": ["a"]}'
        wrapper = DataFrameWrapper.from_json(json_str)

        assert isinstance(wrapper.df, pd.DataFrame)
        assert list(wrapper.df.columns) == ['a']

    def test_wrapper_delegation(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        wrapper = DataFrameWrapper(df)

        # Test delegation to underlying DataFrame
        assert wrapper.shape == (3, 2)
        assert list(wrapper.columns) == ['a', 'b']


class TestConverters:
    """Test conversion utility functions."""

    def test_pandas_to_json_records(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        result = pandas_to_json(df, orient='records')

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]['a'] == 1

    def test_json_to_pandas(self):
        data = [{'a': 1, 'b': 'x'}, {'a': 2, 'b': 'y'}]
        df = json_to_pandas(data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['a', 'b']

    def test_dataframe_to_records(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [np.nan, 5.0, 6.0]})
        records = dataframe_to_records(df)

        assert isinstance(records, list)
        assert len(records) == 3
        assert records[1]['b'] is None  # NaN converted to None

    def test_series_to_list(self):
        s = pd.Series([1, 2, np.nan, 4])
        lst = series_to_list(s)

        assert isinstance(lst, list)
        assert len(lst) == 4
        assert lst[2] is None

    def test_infer_dtype_int(self):
        dtype = infer_dtype([1, 2, 3])
        assert 'int' in dtype

    def test_infer_dtype_float(self):
        dtype = infer_dtype([1.1, 2.2, 3.3])
        assert 'float' in dtype

    def test_infer_dtype_object(self):
        dtype = infer_dtype(['a', 'b', 'c'])
        assert dtype == 'object'

    def test_safe_cast_to_int(self):
        result = safe_cast(['1', '2', '3'], 'int64')
        assert result.dtype == np.int64 or str(result.dtype) == 'int64'

    def test_safe_cast_with_coerce(self):
        result = safe_cast(['1', '2', 'invalid'], 'int64', errors='coerce')
        assert len(result) == 3

    def test_batch_convert(self):
        dfs = [
            pd.DataFrame({'a': [1, 2, 3]}),
            pd.DataFrame({'b': [4, 5, 6]}),
        ]
        results = batch_convert(dfs, operation='to_json')

        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        json_str = to_json(df)
        restored = from_json(json_str)

        assert isinstance(restored, pd.DataFrame)
        assert len(restored) == 0

    def test_dataframe_with_multiindex(self):
        df = pd.DataFrame(
            {'value': [1, 2, 3, 4]},
            index=pd.MultiIndex.from_tuples([('a', 1), ('a', 2), ('b', 1), ('b', 2)])
        )
        # MultiIndex should still serialize
        json_str = to_json(df)
        assert json_str is not None

    def test_dataframe_with_datetime_index(self):
        df = pd.DataFrame(
            {'value': [1, 2, 3]},
            index=pd.date_range('2024-01-01', periods=3)
        )
        json_str = to_json(df)
        restored = from_json(json_str)

        assert isinstance(restored, pd.DataFrame)

    def test_series_with_nan_and_inf(self):
        s = pd.Series([1.0, np.nan, np.inf, -np.inf, 5.0])
        json_str = to_json(s)
        restored = from_json(json_str)

        assert isinstance(restored, pd.Series)
        assert len(restored) == 5

    def test_categorical_column(self):
        df = pd.DataFrame({
            'category': pd.Categorical(['a', 'b', 'a', 'c']),
            'value': [1, 2, 3, 4]
        })
        json_str = to_json(df)
        assert json_str is not None

    def test_nan_handling_drop(self):
        df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [4, 5, 6]})
        result = pandas_to_json(df, handle_na='drop')

        # Should have dropped the row with NaN
        assert len(result) < 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
