import json

import numpy as np
import pandas as pd

import pandasv2 as pv


def test_dataframe_to_json_safe_is_strict_json_and_roundtrips_dtypes():
    df = pv.DataFrame(
        {
            "i64": np.array([1, 2, 3], dtype=np.int64),
            "nullable_i": pd.Series([1, None, 3], dtype="Int64"),
            "ts": pd.to_datetime(["2024-01-01", None, "2024-01-03"]),
            "td": pd.to_timedelta([0, 60, None], unit="s"),
            "f": [1.25, float("nan"), float("inf")],
            "g": [float("-inf"), 0.0, 5.0],
        }
    )

    json_str = df.to_json_safe()

    # Must be strict JSON: no NaN/Infinity tokens.
    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    payload = json.loads(json_str)
    assert payload["__type__"] == "DataFrame"

    df2 = pv.DataFrame.from_json_safe(json_str)

    assert str(df2["i64"].dtype) == str(df["i64"].dtype)
    assert str(df2["nullable_i"].dtype) == str(df["nullable_i"].dtype)
    assert str(df2["ts"].dtype) == str(df["ts"].dtype)
    assert str(df2["td"].dtype) == str(df["td"].dtype)

    pd.testing.assert_frame_equal(df, df2, check_dtype=True)


def test_series_to_json_safe_is_strict_json_and_roundtrips():
    s_num = pv.Series([1.0, float("nan"), float("-inf"), float("inf")], name="num")
    json_str = s_num.to_json_safe()

    assert "NaN" not in json_str
    assert "Infinity" not in json_str

    s2_num = pv.Series.from_json_safe(json_str)
    assert s2_num.name == s_num.name
    pd.testing.assert_series_equal(s_num, s2_num, check_dtype=True)

    s_dt = pv.Series(pd.to_datetime(["2024-01-01", None, "2024-01-03"]), name="dt")
    json_str_dt = s_dt.to_json_safe()
    s2_dt = pv.Series.from_json_safe(json_str_dt)
    assert str(s2_dt.dtype) == str(s_dt.dtype)
    pd.testing.assert_series_equal(s_dt, s2_dt, check_dtype=True)
