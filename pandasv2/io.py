"""
I/O functions for pandasv2.

Wraps all pandas read_* and DataFrame.to_* functions, returning
pandasv2 DataFrame/Series objects instead of plain pandas ones.

Supported I/O:
  read_csv, read_excel, read_json, read_parquet, read_feather,
  read_orc, read_sql, read_sql_query, read_sql_table, read_html,
  read_xml, read_hdf, read_pickle, read_clipboard, read_fwf,
  read_table, read_spss, read_sas

  to_csv, to_excel, to_json, to_parquet, to_feather, to_orc,
  to_sql, to_html, to_xml, to_hdf, to_pickle, to_clipboard,
  to_latex, to_markdown, to_string

Built by Mahesh Makvana
"""

import pandas as _pd
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Union


def _wrap(obj):
    """Wrap a pandas object in the corresponding pandasv2 type."""
    from .dataframe import DataFrame
    from .series import Series
    if isinstance(obj, _pd.DataFrame):
        return DataFrame(obj)
    if isinstance(obj, _pd.Series):
        return Series(obj)
    return obj


# ---------------------------------------------------------------------------
# Read functions
# ---------------------------------------------------------------------------

def read_csv(
    filepath_or_buffer,
    sep=',',
    delimiter=None,
    header='infer',
    names=None,
    index_col=None,
    usecols=None,
    dtype=None,
    engine=None,
    converters=None,
    true_values=None,
    false_values=None,
    skipinitialspace=False,
    skiprows=None,
    skipfooter=0,
    nrows=None,
    na_values=None,
    keep_default_na=True,
    na_filter=True,
    skip_blank_lines=True,
    parse_dates=False,
    date_format=None,
    dayfirst=False,
    cache_dates=True,
    iterator=False,
    chunksize=None,
    compression='infer',
    thousands=None,
    decimal='.',
    lineterminator=None,
    quotechar='"',
    quoting=0,
    doublequote=True,
    escapechar=None,
    comment=None,
    encoding=None,
    encoding_errors='strict',
    dialect=None,
    on_bad_lines='error',
    low_memory=True,
    memory_map=False,
    float_precision=None,
    storage_options=None,
    dtype_backend=_pd.api.extensions.no_default,
):
    """
    Read a comma-separated values (CSV) file into a pandasv2 DataFrame.

    All parameters identical to pandas.read_csv().

    Example:
        >>> import pandasv2 as pd
        >>> df = pd.read_csv('data.csv')
        >>> df.head()
    """
    kwargs = dict(
        sep=sep, delimiter=delimiter, header=header, names=names,
        index_col=index_col, usecols=usecols, dtype=dtype, engine=engine,
        converters=converters, true_values=true_values, false_values=false_values,
        skipinitialspace=skipinitialspace, skiprows=skiprows, skipfooter=skipfooter,
        nrows=nrows, na_values=na_values, keep_default_na=keep_default_na,
        na_filter=na_filter, skip_blank_lines=skip_blank_lines,
        parse_dates=parse_dates, date_format=date_format,
        dayfirst=dayfirst, cache_dates=cache_dates, iterator=iterator,
        chunksize=chunksize, compression=compression, thousands=thousands,
        decimal=decimal, lineterminator=lineterminator, quotechar=quotechar,
        quoting=quoting, doublequote=doublequote, escapechar=escapechar,
        comment=comment, encoding=encoding, encoding_errors=encoding_errors,
        dialect=dialect, on_bad_lines=on_bad_lines, low_memory=low_memory,
        memory_map=memory_map, float_precision=float_precision,
        storage_options=storage_options,
    )
    if dtype_backend is not _pd.api.extensions.no_default:
        kwargs['dtype_backend'] = dtype_backend

    # Fix pandas #52493: literal string "None" was silently coerced to NaN.
    # Preserve it by removing it from the default NA values list.
    if na_values is None and keep_default_na:
        import pandas.io.parsers as _parsers
        default_na = set(getattr(_parsers, 'STR_NA_VALUES',
                                 {'', '#N/A', '#N/A N/A', '#NA', '-1.#IND',
                                  '-1.#QNAN', '-NaN', '-nan', '1.#IND',
                                  '1.#QNAN', '<NA>', 'N/A', 'NA', 'NULL',
                                  'NaN', 'None', 'n/a', 'nan', 'null'}))
        default_na.discard('None')
        kwargs['na_values'] = list(default_na)
        kwargs['keep_default_na'] = False

    result = _pd.read_csv(filepath_or_buffer, **kwargs)
    return _wrap(result)


def read_excel(
    io,
    sheet_name=0,
    header=0,
    names=None,
    index_col=None,
    usecols=None,
    dtype=None,
    engine=None,
    converters=None,
    true_values=None,
    false_values=None,
    skiprows=None,
    nrows=None,
    na_values=None,
    keep_default_na=True,
    na_filter=True,
    parse_dates=False,
    date_format=None,
    thousands=None,
    decimal='.',
    comment=None,
    skipfooter=0,
    storage_options=None,
    dtype_backend=_pd.api.extensions.no_default,
):
    """
    Read an Excel file into a pandasv2 DataFrame.

    All parameters identical to pandas.read_excel().

    Example:
        >>> df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
    """
    kwargs = dict(
        sheet_name=sheet_name, header=header, names=names, index_col=index_col,
        usecols=usecols, dtype=dtype, engine=engine, converters=converters,
        true_values=true_values, false_values=false_values, skiprows=skiprows,
        nrows=nrows, na_values=na_values, keep_default_na=keep_default_na,
        na_filter=na_filter, parse_dates=parse_dates, date_format=date_format,
        thousands=thousands, decimal=decimal, comment=comment,
        skipfooter=skipfooter, storage_options=storage_options,
    )
    if dtype_backend is not _pd.api.extensions.no_default:
        kwargs['dtype_backend'] = dtype_backend

    result = _pd.read_excel(io, **kwargs)
    if isinstance(result, dict):
        from .dataframe import DataFrame
        return {k: DataFrame(v) for k, v in result.items()}
    return _wrap(result)


def read_json(
    path_or_buf=None,
    orient=None,
    typ='frame',
    dtype=None,
    convert_axes=None,
    convert_dates=True,
    keep_default_dates=True,
    precise_float=False,
    date_unit=None,
    encoding=None,
    encoding_errors='strict',
    lines=False,
    chunksize=None,
    compression='infer',
    nrows=None,
    storage_options=None,
    dtype_backend=_pd.api.extensions.no_default,
    engine=None,
):
    """
    Read a JSON file/string into a pandasv2 DataFrame or Series.

    All parameters identical to pandas.read_json().

    Example:
        >>> df = pd.read_json('data.json', orient='records')
    """
    kwargs = dict(
        orient=orient, typ=typ, dtype=dtype, convert_axes=convert_axes,
        convert_dates=convert_dates, keep_default_dates=keep_default_dates,
        precise_float=precise_float, date_unit=date_unit,
        encoding=encoding, encoding_errors=encoding_errors, lines=lines,
        chunksize=chunksize, compression=compression, nrows=nrows,
        storage_options=storage_options,
    )
    if dtype_backend is not _pd.api.extensions.no_default:
        kwargs['dtype_backend'] = dtype_backend
    if engine is not None:
        kwargs['engine'] = engine

    # Fix pandas #52595: orient='table' with tz-aware datetimes raises
    # "Cannot use .astype to convert from timezone-aware dtype to timezone-naive".
    try:
        result = _pd.read_json(path_or_buf, **kwargs)
    except TypeError as e:
        if orient == 'table' and 'timezone' in str(e).lower():
            # Re-read without convert_dates and fix tz manually
            kwargs2 = dict(kwargs)
            kwargs2['convert_dates'] = False
            result = _pd.read_json(path_or_buf, **kwargs2)
            for col in result.select_dtypes(include='object').columns:
                try:
                    result[col] = _pd.to_datetime(result[col], utc=True)
                except Exception:
                    pass
        else:
            raise
    return _wrap(result)


def read_parquet(
    path,
    engine='auto',
    columns=None,
    storage_options=None,
    use_nullable_dtypes=_pd.api.extensions.no_default,
    dtype_backend=_pd.api.extensions.no_default,
    filesystem=None,
    filters=None,
    **kwargs,
):
    """
    Load a Parquet object from the file path, returning a pandasv2 DataFrame.

    Example:
        >>> df = pd.read_parquet('data.parquet')
    """
    kw = dict(engine=engine, columns=columns, storage_options=storage_options,
              filters=filters)
    for param, val in [
        ('use_nullable_dtypes', use_nullable_dtypes),
        ('dtype_backend', dtype_backend),
        ('filesystem', filesystem),
    ]:
        if val is not _pd.api.extensions.no_default:
            kw[param] = val
    kw.update(kwargs)
    return _wrap(_pd.read_parquet(path, **kw))


def read_feather(path, columns=None, use_threads=True, storage_options=None,
                 dtype_backend=_pd.api.extensions.no_default):
    """Read a Feather-format object from the file path."""
    kw = dict(columns=columns, use_threads=use_threads, storage_options=storage_options)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_feather(path, **kw))


def read_orc(path, columns=None, dtype_backend=_pd.api.extensions.no_default,
             filesystem=None, **kwargs):
    """Read an ORC object from the file path."""
    kw = dict(columns=columns, **kwargs)
    for param, val in [
        ('dtype_backend', dtype_backend), ('filesystem', filesystem),
    ]:
        if val is not _pd.api.extensions.no_default:
            kw[param] = val
    return _wrap(_pd.read_orc(path, **kw))


def read_sql(
    sql,
    con,
    index_col=None,
    coerce_float=True,
    params=None,
    parse_dates=None,
    columns=None,
    chunksize=None,
    dtype_backend=_pd.api.extensions.no_default,
    dtype=None,
):
    """
    Read SQL query or database table into a pandasv2 DataFrame.

    Example:
        >>> import sqlite3
        >>> con = sqlite3.connect('data.db')
        >>> df = pd.read_sql('SELECT * FROM users', con)
    """
    kw = dict(index_col=index_col, coerce_float=coerce_float, params=params,
              parse_dates=parse_dates, columns=columns, chunksize=chunksize)
    for param, val in [
        ('dtype_backend', dtype_backend), ('dtype', dtype),
    ]:
        if val is not _pd.api.extensions.no_default:
            kw[param] = val
    result = _pd.read_sql(sql, con, **kw)
    return _wrap(result)


def read_sql_query(
    sql, con, index_col=None, coerce_float=True, params=None,
    parse_dates=None, chunksize=None, dtype=None,
    dtype_backend=_pd.api.extensions.no_default,
):
    """Read SQL query into a pandasv2 DataFrame.

    Fixes pandas #52437: dict-cursor adapters (e.g. pymssql as_dict=True)
    caused column headers to fill every cell.  We detect list-of-dicts
    results and build the DataFrame directly.
    """
    kw = dict(index_col=index_col, coerce_float=coerce_float, params=params,
              parse_dates=parse_dates, chunksize=chunksize)
    for param, val in [('dtype', dtype), ('dtype_backend', dtype_backend)]:
        if val is not _pd.api.extensions.no_default:
            kw[param] = val
    try:
        result = _pd.read_sql_query(sql, con, **kw)
        # Detect the pandas #52437 symptom: first row values equal column names
        if (isinstance(result, _pd.DataFrame) and len(result) > 0
                and list(result.iloc[0]) == list(result.columns)):
            raise ValueError("dict-cursor detected")
        return _wrap(result)
    except Exception:
        # Fallback: execute manually and build from list-of-dicts
        try:
            cursor = con.cursor()
            cursor.execute(sql, params or [])
            rows = cursor.fetchall()
            if rows and isinstance(rows[0], dict):
                from .dataframe import DataFrame
                return DataFrame(rows)
        except Exception:
            pass
        # Re-run original path if fallback also fails
        return _wrap(_pd.read_sql_query(sql, con, **kw))


def read_sql_table(
    table_name, con, schema=None, index_col=None, coerce_float=True,
    parse_dates=None, columns=None, chunksize=None,
    dtype_backend=_pd.api.extensions.no_default,
):
    """Read SQL database table into a pandasv2 DataFrame."""
    kw = dict(schema=schema, index_col=index_col, coerce_float=coerce_float,
              parse_dates=parse_dates, columns=columns, chunksize=chunksize)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_sql_table(table_name, con, **kw))


def read_html(
    io, match='.+', flavor=None, header=None, index_col=None, skiprows=None,
    attrs=None, parse_dates=False, thousands=',', encoding=None, decimal='.',
    converters=None, na_values=None, keep_default_na=True, displayed_only=True,
    extract_links=None, dtype_backend=_pd.api.extensions.no_default,
    storage_options=None,
):
    """
    Read HTML tables into a list of pandasv2 DataFrames.

    Example:
        >>> dfs = pd.read_html('https://example.com/table.html')
    """
    kw = dict(
        match=match, flavor=flavor, header=header, index_col=index_col,
        skiprows=skiprows, attrs=attrs, parse_dates=parse_dates,
        thousands=thousands, encoding=encoding, decimal=decimal,
        converters=converters, na_values=na_values, keep_default_na=keep_default_na,
        displayed_only=displayed_only, storage_options=storage_options,
    )
    for param, val in [
        ('extract_links', extract_links), ('dtype_backend', dtype_backend),
    ]:
        if val is not _pd.api.extensions.no_default:
            kw[param] = val
    results = _pd.read_html(io, **kw)
    return [_wrap(r) for r in results]


def read_xml(
    path_or_buffer, xpath='./*', namespaces=None, elems_only=False,
    attrs_only=False, names=None, dtype=None, converters=None,
    parse_dates=None, encoding='utf-8', parser='lxml', stylesheet=None,
    iterparse=None, compression='infer', storage_options=None,
    dtype_backend=_pd.api.extensions.no_default,
):
    """Read XML document into a pandasv2 DataFrame."""
    kw = dict(
        xpath=xpath, namespaces=namespaces, elems_only=elems_only,
        attrs_only=attrs_only, names=names, dtype=dtype, converters=converters,
        parse_dates=parse_dates, encoding=encoding, parser=parser,
        stylesheet=stylesheet, iterparse=iterparse, compression=compression,
        storage_options=storage_options,
    )
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_xml(path_or_buffer, **kw))


def read_hdf(path_or_buf, key=None, mode='r', errors='strict',
             where=None, start=None, stop=None, columns=None,
             iterator=False, chunksize=None, **kwargs):
    """Read from the store, close it if we opened it."""
    result = _pd.read_hdf(path_or_buf, key=key, mode=mode, errors=errors,
                           where=where, start=start, stop=stop,
                           columns=columns, iterator=iterator,
                           chunksize=chunksize, **kwargs)
    return _wrap(result)


def read_pickle(filepath_or_buffer, compression='infer', storage_options=None):
    """Load pickled pandas object (or any object) from file."""
    return _wrap(_pd.read_pickle(filepath_or_buffer, compression=compression,
                                  storage_options=storage_options))


def read_clipboard(sep=r'\s+', dtype_backend=_pd.api.extensions.no_default, **kwargs):
    """Read text from clipboard and pass to read_csv."""
    kw = dict(sep=sep, **kwargs)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_clipboard(**kw))


def read_fwf(filepath_or_buffer, colspecs='infer', widths=None,
             infer_nrows=100, dtype_backend=_pd.api.extensions.no_default, **kwargs):
    """Read a table of fixed-width formatted lines into DataFrame."""
    kw = dict(colspecs=colspecs, widths=widths, infer_nrows=infer_nrows, **kwargs)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_fwf(filepath_or_buffer, **kw))


def read_table(
    filepath_or_buffer, sep='\t', delimiter=None, header='infer',
    names=None, index_col=None, usecols=None, dtype=None, engine=None,
    converters=None, true_values=None, false_values=None, skipinitialspace=False,
    skiprows=None, skipfooter=0, nrows=None, na_values=None,
    keep_default_na=True, na_filter=True, skip_blank_lines=True,
    parse_dates=False, date_format=None, dayfirst=False, cache_dates=True,
    iterator=False, chunksize=None, compression='infer', thousands=None,
    decimal='.', lineterminator=None, quotechar='"', quoting=0,
    doublequote=True, escapechar=None, comment=None, encoding=None,
    encoding_errors='strict', dialect=None, on_bad_lines='error',
    low_memory=True, memory_map=False, float_precision=None,
    storage_options=None, dtype_backend=_pd.api.extensions.no_default,
):
    """Read general delimited file into DataFrame."""
    kw = dict(
        sep=sep, delimiter=delimiter, header=header, names=names,
        index_col=index_col, usecols=usecols, dtype=dtype, engine=engine,
        converters=converters, true_values=true_values, false_values=false_values,
        skipinitialspace=skipinitialspace, skiprows=skiprows, skipfooter=skipfooter,
        nrows=nrows, na_values=na_values, keep_default_na=keep_default_na,
        na_filter=na_filter, skip_blank_lines=skip_blank_lines,
        parse_dates=parse_dates, date_format=date_format, dayfirst=dayfirst,
        cache_dates=cache_dates, iterator=iterator, chunksize=chunksize,
        compression=compression, thousands=thousands, decimal=decimal,
        lineterminator=lineterminator, quotechar=quotechar, quoting=quoting,
        doublequote=doublequote, escapechar=escapechar, comment=comment,
        encoding=encoding, encoding_errors=encoding_errors, dialect=dialect,
        on_bad_lines=on_bad_lines, low_memory=low_memory, memory_map=memory_map,
        float_precision=float_precision, storage_options=storage_options,
    )
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_table(filepath_or_buffer, **kw))


def read_spss(path, usecols=None, convert_categoricals=True,
              dtype_backend=_pd.api.extensions.no_default):
    """Load an SPSS file, returning a pandasv2 DataFrame."""
    kw = dict(usecols=usecols, convert_categoricals=convert_categoricals)
    if dtype_backend is not _pd.api.extensions.no_default:
        kw['dtype_backend'] = dtype_backend
    return _wrap(_pd.read_spss(path, **kw))


def read_sas(filepath_or_buffer, format=None, index=None, encoding=None,
             chunksize=None, iterator=False, compression='infer'):
    """Read SAS files stored as either XPORT or SAS7BDAT format files."""
    result = _pd.read_sas(filepath_or_buffer, format=format, index=index,
                           encoding=encoding, chunksize=chunksize,
                           iterator=iterator, compression=compression)
    return _wrap(result)
