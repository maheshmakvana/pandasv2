"""
Plotting support for pandasv2.

Wraps the pandas PlotAccessor so DataFrame.plot and Series.plot return
fully functional plot objects, and exposes top-level plot helpers:
  - scatter_matrix()
  - lag_plot()
  - autocorrelation_plot()
  - bootstrap_plot()
  - andrews_curves()
  - parallel_coordinates()
  - radviz()
  - PlotAccessor  — the accessor class itself

Also adds pandasv2-specific helpers on the PlotAccessor:
  - .to_base64()  — encode the current figure as a base64 PNG (for web APIs)
  - .to_html()    — render figure as an inline HTML <img> tag

Built by Mahesh Makvana
"""

import pandas as _pd
import pandas.plotting as _pp
from typing import Any, Dict, List, Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Re-export all pandas.plotting top-level functions
# ---------------------------------------------------------------------------

def scatter_matrix(frame, alpha=0.5, figsize=None, ax=None, grid=False,
                   diagonal='hist', marker='.', density_kwds=None,
                   hist_kwds=None, range_padding=0.05, **kwargs):
    """
    Draw a matrix of scatter plots.

    Example:
        >>> pd.plotting.scatter_matrix(df, figsize=(10, 10))
    """
    return _pp.scatter_matrix(
        frame, alpha=alpha, figsize=figsize, ax=ax, grid=grid,
        diagonal=diagonal, marker=marker, density_kwds=density_kwds,
        hist_kwds=hist_kwds, range_padding=range_padding, **kwargs
    )


def lag_plot(series, lag=1, ax=None, **kwargs):
    """
    Lag plot for time series.

    Example:
        >>> pd.plotting.lag_plot(series)
    """
    return _pp.lag_plot(series, lag=lag, ax=ax, **kwargs)


def autocorrelation_plot(series, ax=None, **kwargs):
    """
    Autocorrelation plot for time series.

    Example:
        >>> pd.plotting.autocorrelation_plot(series)
    """
    return _pp.autocorrelation_plot(series, ax=ax, **kwargs)


def bootstrap_plot(series, fig=None, size=50, samples=500, **kwargs):
    """
    Bootstrap plot on mean, median and mid-range statistics.

    Example:
        >>> pd.plotting.bootstrap_plot(series)
    """
    return _pp.bootstrap_plot(series, fig=fig, size=size, samples=samples, **kwargs)


def andrews_curves(frame, class_column, ax=None, samples=200,
                   color=None, colormap=None, **kwargs):
    """
    Generate a matplotlib plot of Andrews curves.

    Example:
        >>> pd.plotting.andrews_curves(iris_df, 'species')
    """
    return _pp.andrews_curves(
        frame, class_column, ax=ax, samples=samples,
        color=color, colormap=colormap, **kwargs
    )


def parallel_coordinates(frame, class_column, cols=None, ax=None,
                          color=None, use_columns=False, xticks=None,
                          colormap=None, axvlines=True, axvlines_kwds=None,
                          sort_labels=False, **kwargs):
    """
    Parallel coordinates plotting.

    Example:
        >>> pd.plotting.parallel_coordinates(iris_df, 'species')
    """
    return _pp.parallel_coordinates(
        frame, class_column, cols=cols, ax=ax, color=color,
        use_columns=use_columns, xticks=xticks, colormap=colormap,
        axvlines=axvlines, axvlines_kwds=axvlines_kwds,
        sort_labels=sort_labels, **kwargs
    )


def radviz(frame, class_column, ax=None, color=None, colormap=None, **kwargs):
    """
    Plot a multidimensional dataset in 2D using RadViz.

    Example:
        >>> pd.plotting.radviz(iris_df, 'species')
    """
    return _pp.radviz(
        frame, class_column, ax=ax, color=color, colormap=colormap, **kwargs
    )


def deregister_matplotlib_converters():
    """Remove pandas formatters and converters."""
    return _pp.deregister_matplotlib_converters()


def register_matplotlib_converters():
    """Register pandas formatters and converters with matplotlib."""
    return _pp.register_matplotlib_converters()


def plot_params():
    """Return the current pandas plotting parameters."""
    return _pp.plot_params


# ---------------------------------------------------------------------------
# PlotAccessor wrapper — adds to_base64 / to_html to every plot result
# ---------------------------------------------------------------------------

class _EnhancedPlotResult:
    """
    Wraps a matplotlib Axes or list of Axes object with pandasv2 extras.

    Obtained from df.plot(...) or series.plot(...).
    """

    def __init__(self, axes):
        self._axes = axes

    def __getattr__(self, name):
        return getattr(self._axes, name)

    def __repr__(self):
        return repr(self._axes)

    def _repr_html_(self):
        """Auto-display in Jupyter."""
        return self.to_html()

    @property
    def axes(self):
        """Underlying matplotlib Axes."""
        return self._axes

    def to_base64(self, fmt: str = 'png', dpi: int = 100) -> str:
        """
        Encode the current figure as a base64 string.

        Useful for embedding plots in web API responses.

        Args:
            fmt: Image format ('png', 'svg', 'jpeg')
            dpi: Dots per inch for raster formats

        Returns:
            Base64-encoded string of the image

        Example:
            >>> b64 = df.plot(kind='bar').to_base64()
            >>> return {'chart': b64}
        """
        import io
        import base64
        fig = _get_figure(self._axes)
        buf = io.BytesIO()
        fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def to_html(self, fmt: str = 'png', dpi: int = 100) -> str:
        """
        Render figure as an inline HTML <img> tag (base64 data URI).

        Suitable for embedding in HTML pages or Jupyter notebooks.

        Args:
            fmt: Image format ('png', 'svg', 'jpeg')
            dpi: Dots per inch for raster formats

        Returns:
            HTML string: <img src="data:image/png;base64,...">

        Example:
            >>> html = df.plot(kind='line').to_html()
            >>> return HTMLResponse(content=html)
        """
        b64 = self.to_base64(fmt=fmt, dpi=dpi)
        mime = 'image/svg+xml' if fmt == 'svg' else f'image/{fmt}'
        return f'<img src="data:{mime};base64,{b64}" />'

    def to_bytes(self, fmt: str = 'png', dpi: int = 100) -> bytes:
        """
        Return the figure as raw bytes.

        Useful for streaming image responses from web APIs.

        Args:
            fmt: Image format ('png', 'svg', 'jpeg')
            dpi: Resolution for raster formats

        Returns:
            Raw bytes of the rendered figure

        Example:
            >>> from fastapi.responses import Response
            >>> img = df.plot.bar().to_bytes()
            >>> return Response(content=img, media_type='image/png')
        """
        import io
        fig = _get_figure(self._axes)
        buf = io.BytesIO()
        fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return buf.read()

    def save(self, path: str, dpi: int = 150, **kwargs) -> None:
        """
        Save the figure to a file.

        Args:
            path: Output file path (extension determines format)
            dpi: Resolution for raster formats
            **kwargs: Extra kwargs passed to fig.savefig()

        Example:
            >>> df.plot(kind='bar').save('chart.png')
        """
        fig = _get_figure(self._axes)
        fig.savefig(path, dpi=dpi, bbox_inches='tight', **kwargs)


def _get_figure(axes):
    """Extract the figure from an Axes or list of Axes."""
    if hasattr(axes, 'figure'):
        return axes.figure
    elif isinstance(axes, (list, tuple)) and len(axes) > 0:
        return axes[0].figure
    import matplotlib.pyplot as plt
    return plt.gcf()


# ---------------------------------------------------------------------------
# PlotAccessor — wraps pandas PlotAccessor and returns _EnhancedPlotResult
# ---------------------------------------------------------------------------

class PlotAccessor:
    """
    pandasv2 PlotAccessor — wraps pandas plotting with extra web helpers.

    Obtained automatically via df.plot or series.plot.

    All standard plot types work:
        df.plot(kind='line'), df.plot.bar(), df.plot.hist(), ...

    Extra methods:
        result.to_base64()  — base64 PNG for API responses
        result.to_html()    — inline <img> tag
        result.to_bytes()   — raw PNG bytes
        result.save(path)   — save to file
    """

    def __init__(self, data):
        self._data = data
        self._pandas_accessor = _pd.plotting.PlotAccessor(data)

    def __call__(self, *args, **kwargs) -> _EnhancedPlotResult:
        result = self._pandas_accessor(*args, **kwargs)
        return _EnhancedPlotResult(result)

    def __getattr__(self, name):
        attr = getattr(self._pandas_accessor, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                if hasattr(result, 'figure') or isinstance(result, (list, tuple)):
                    return _EnhancedPlotResult(result)
                return result
            return wrapper
        return attr

    # Explicit plot type methods
    def line(self, x=None, y=None, **kwargs) -> _EnhancedPlotResult:
        """Line plot."""
        return _EnhancedPlotResult(self._pandas_accessor.line(x=x, y=y, **kwargs))

    def bar(self, x=None, y=None, **kwargs) -> _EnhancedPlotResult:
        """Vertical bar plot."""
        return _EnhancedPlotResult(self._pandas_accessor.bar(x=x, y=y, **kwargs))

    def barh(self, x=None, y=None, **kwargs) -> _EnhancedPlotResult:
        """Horizontal bar plot."""
        return _EnhancedPlotResult(self._pandas_accessor.barh(x=x, y=y, **kwargs))

    def hist(self, by=None, bins=10, **kwargs) -> _EnhancedPlotResult:
        """Histogram."""
        return _EnhancedPlotResult(self._pandas_accessor.hist(by=by, bins=bins, **kwargs))

    def box(self, by=None, **kwargs) -> _EnhancedPlotResult:
        """Box plot."""
        return _EnhancedPlotResult(self._pandas_accessor.box(by=by, **kwargs))

    def kde(self, bw_method=None, ind=None, **kwargs) -> _EnhancedPlotResult:
        """Kernel density estimate plot."""
        return _EnhancedPlotResult(self._pandas_accessor.kde(
            bw_method=bw_method, ind=ind, **kwargs))

    density = kde

    def area(self, x=None, y=None, stacked=True, **kwargs) -> _EnhancedPlotResult:
        """Area plot."""
        return _EnhancedPlotResult(self._pandas_accessor.area(
            x=x, y=y, stacked=stacked, **kwargs))

    def pie(self, y=None, **kwargs) -> _EnhancedPlotResult:
        """Pie chart."""
        return _EnhancedPlotResult(self._pandas_accessor.pie(y=y, **kwargs))

    def scatter(self, x, y, s=None, c=None, **kwargs) -> _EnhancedPlotResult:
        """Scatter plot (DataFrame only)."""
        return _EnhancedPlotResult(self._pandas_accessor.scatter(
            x=x, y=y, s=s, c=c, **kwargs))

    def hexbin(self, x, y, C=None, reduce_C_function=None,
               gridsize=None, **kwargs) -> _EnhancedPlotResult:
        """Hexagonal binning plot (DataFrame only)."""
        kw = dict(x=x, y=y, **kwargs)
        if C is not None:
            kw['C'] = C
        if reduce_C_function is not None:
            kw['reduce_C_function'] = reduce_C_function
        if gridsize is not None:
            kw['gridsize'] = gridsize
        return _EnhancedPlotResult(self._pandas_accessor.hexbin(**kw))


# ---------------------------------------------------------------------------
# Namespace object — exposed as pd.plotting
# ---------------------------------------------------------------------------

class _PlottingNamespace:
    """
    Full pd.plotting namespace for pandasv2.

    Usage:
        >>> import pandasv2 as pd
        >>> pd.plotting.scatter_matrix(df)
        >>> pd.plotting.andrews_curves(iris_df, 'species')
    """
    scatter_matrix = staticmethod(scatter_matrix)
    lag_plot = staticmethod(lag_plot)
    autocorrelation_plot = staticmethod(autocorrelation_plot)
    bootstrap_plot = staticmethod(bootstrap_plot)
    andrews_curves = staticmethod(andrews_curves)
    parallel_coordinates = staticmethod(parallel_coordinates)
    radviz = staticmethod(radviz)
    deregister_matplotlib_converters = staticmethod(deregister_matplotlib_converters)
    register_matplotlib_converters = staticmethod(register_matplotlib_converters)
    PlotAccessor = PlotAccessor


plotting = _PlottingNamespace()
