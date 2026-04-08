"""
Styling support for pandasv2.

Wraps pandas Styler so DataFrame.style returns a fully functional
Styler that keeps all pandas styling capabilities while adding
pandasv2-specific helpers:
  - to_json_safe()   — export styled data as JSON
  - to_web()         — export rendered HTML for web responses

Built by Mahesh Makvana
"""

import pandas as _pd
from typing import Any, Callable, Dict, List, Optional, Sequence, Union


class Styler:
    """
    pandasv2 Styler — wraps pandas.io.formats.style.Styler.

    All standard pandas Styler methods work unchanged.  Extra features:
    - to_json_safe()  — lossless JSON of the underlying data
    - to_web()        — rendered HTML string for web responses
    - export_css()    — extract generated CSS rules

    Obtain via:
        >>> df.style                   # returns this Styler
        >>> df.style.background_gradient().to_web()
    """

    def __init__(self, styler):
        self._styler = styler

    # ------------------------------------------------------------------
    # Delegate everything to the underlying pandas Styler
    # ------------------------------------------------------------------

    def __getattr__(self, name):
        attr = getattr(self._styler, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If pandas returns a Styler, re-wrap it
                if isinstance(result, _pd.io.formats.style.Styler):
                    return Styler(result)
                return result
            return wrapper
        return attr

    # ------------------------------------------------------------------
    # Styling methods — each re-wraps the result
    # ------------------------------------------------------------------

    def set_properties(self, subset=None, **kwargs) -> 'Styler':
        return Styler(self._styler.set_properties(subset=subset, **kwargs))

    def set_table_styles(self, table_styles=None, axis=0, overwrite=True,
                         css_class_names=None) -> 'Styler':
        kw = dict(axis=axis, overwrite=overwrite)
        if css_class_names is not None:
            kw['css_class_names'] = css_class_names
        return Styler(self._styler.set_table_styles(table_styles, **kw))

    def set_caption(self, caption) -> 'Styler':
        return Styler(self._styler.set_caption(caption))

    def set_sticky(self, axis=0, pixel_size=None, levels=None) -> 'Styler':
        kw = dict(axis=axis)
        if pixel_size is not None:
            kw['pixel_size'] = pixel_size
        if levels is not None:
            kw['levels'] = levels
        return Styler(self._styler.set_sticky(**kw))

    def set_na_rep(self, na_rep: str) -> 'Styler':
        return Styler(self._styler.set_na_rep(na_rep))

    def set_uuid(self, uuid: str) -> 'Styler':
        return Styler(self._styler.set_uuid(uuid))

    def set_table_attributes(self, attributes: str) -> 'Styler':
        return Styler(self._styler.set_table_attributes(attributes))

    def background_gradient(self, cmap='PuBu', low=0, high=0,
                             axis=0, subset=None, text_color_threshold=0.408,
                             vmin=None, vmax=None, gmap=None) -> 'Styler':
        return Styler(self._styler.background_gradient(
            cmap=cmap, low=low, high=high, axis=axis, subset=subset,
            text_color_threshold=text_color_threshold, vmin=vmin, vmax=vmax,
            gmap=gmap))

    def text_gradient(self, cmap='PuBu', low=0, high=0, axis=0, subset=None,
                      vmin=None, vmax=None, gmap=None) -> 'Styler':
        return Styler(self._styler.text_gradient(
            cmap=cmap, low=low, high=high, axis=axis, subset=subset,
            vmin=vmin, vmax=vmax, gmap=gmap))

    def highlight_null(self, color='red', subset=None,
                       props=None) -> 'Styler':
        kw = dict(subset=subset)
        if props is not None:
            kw['props'] = props
        else:
            kw['color'] = color
        return Styler(self._styler.highlight_null(**kw))

    def highlight_min(self, subset=None, color='yellow', axis=0,
                      props=None) -> 'Styler':
        kw = dict(subset=subset, axis=axis)
        if props is not None:
            kw['props'] = props
        else:
            kw['color'] = color
        return Styler(self._styler.highlight_min(**kw))

    def highlight_max(self, subset=None, color='yellow', axis=0,
                      props=None) -> 'Styler':
        kw = dict(subset=subset, axis=axis)
        if props is not None:
            kw['props'] = props
        else:
            kw['color'] = color
        return Styler(self._styler.highlight_max(**kw))

    def highlight_between(self, subset=None, color='yellow', axis=0,
                           left=None, right=None, inclusive='both',
                           props=None) -> 'Styler':
        kw = dict(subset=subset, axis=axis, left=left, right=right,
                  inclusive=inclusive)
        if props is not None:
            kw['props'] = props
        else:
            kw['color'] = color
        return Styler(self._styler.highlight_between(**kw))

    def highlight_quantile(self, subset=None, color='yellow', axis=0,
                            q_left=0.0, q_right=1.0, interpolation='linear',
                            inclusive='both', props=None) -> 'Styler':
        kw = dict(subset=subset, axis=axis, q_left=q_left, q_right=q_right,
                  interpolation=interpolation, inclusive=inclusive)
        if props is not None:
            kw['props'] = props
        else:
            kw['color'] = color
        return Styler(self._styler.highlight_quantile(**kw))

    def bar(self, subset=None, axis=0, color='#d65f5f', width=100,
            height=100, align='left', vmin=None, vmax=None,
            props='width: 10em;') -> 'Styler':
        return Styler(self._styler.bar(
            subset=subset, axis=axis, color=color, width=width,
            height=height, align=align, vmin=vmin, vmax=vmax, props=props))

    def apply(self, func: Callable, axis=0, subset=None,
              **kwargs) -> 'Styler':
        return Styler(self._styler.apply(func, axis=axis, subset=subset,
                                         **kwargs))

    def applymap(self, func: Callable, subset=None, **kwargs) -> 'Styler':
        return Styler(self._styler.applymap(func, subset=subset, **kwargs))

    def map(self, func: Callable, subset=None, **kwargs) -> 'Styler':
        """Alias for applymap (pandas >= 2.1 renamed it)."""
        _fn = getattr(self._styler, 'map', None) or self._styler.applymap
        return Styler(_fn(func, subset=subset, **kwargs))

    def format(self, formatter=None, subset=None, na_rep=None,
               precision=None, decimal='.', thousands=None, escape=None,
               hyperlinks=None) -> 'Styler':
        kw = {}
        if subset is not None:
            kw['subset'] = subset
        if na_rep is not None:
            kw['na_rep'] = na_rep
        if precision is not None:
            kw['precision'] = precision
        if decimal != '.':
            kw['decimal'] = decimal
        if thousands is not None:
            kw['thousands'] = thousands
        if escape is not None:
            kw['escape'] = escape
        if hyperlinks is not None:
            kw['hyperlinks'] = hyperlinks
        return Styler(self._styler.format(formatter, **kw))

    def format_index(self, formatter=None, axis=0, level=None, na_rep=None,
                     precision=None, decimal='.', thousands=None,
                     escape=None, hyperlinks=None) -> 'Styler':
        kw = dict(axis=axis)
        if level is not None:
            kw['level'] = level
        if na_rep is not None:
            kw['na_rep'] = na_rep
        if precision is not None:
            kw['precision'] = precision
        if escape is not None:
            kw['escape'] = escape
        return Styler(self._styler.format_index(formatter, **kw))

    def relabel_index(self, labels, axis=0, level=None) -> 'Styler':
        kw = dict(axis=axis)
        if level is not None:
            kw['level'] = level
        return Styler(self._styler.relabel_index(labels, **kw))

    def hide(self, subset=None, axis=0, level=None, names=False) -> 'Styler':
        kw = dict(axis=axis, names=names)
        if subset is not None:
            kw['subset'] = subset
        if level is not None:
            kw['level'] = level
        return Styler(self._styler.hide(**kw))

    def concat(self, other: 'Styler') -> 'Styler':
        other_styler = other._styler if isinstance(other, Styler) else other
        return Styler(self._styler.concat(other_styler))

    def pipe(self, func: Callable, *args, **kwargs) -> 'Styler':
        result = self._styler.pipe(func, *args, **kwargs)
        if isinstance(result, _pd.io.formats.style.Styler):
            return Styler(result)
        return result

    def clear(self) -> 'Styler':
        return Styler(self._styler.clear())

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def render(self, **kwargs) -> str:
        """Render to HTML string (alias for to_html)."""
        return self._styler.to_html(**kwargs)

    def to_html(self, **kwargs) -> str:
        """Render to full HTML table string."""
        return self._styler.to_html(**kwargs)

    def to_latex(self, buf=None, **kwargs) -> Optional[str]:
        """Render to LaTeX tabular environment."""
        return self._styler.to_latex(buf=buf, **kwargs)

    def to_excel(self, excel_writer, sheet_name='Sheet1', **kwargs) -> None:
        """Export styled DataFrame to Excel."""
        self._styler.to_excel(excel_writer, sheet_name=sheet_name, **kwargs)

    def to_string(self, buf=None, **kwargs) -> Optional[str]:
        """Render to plain-text string."""
        return self._styler.to_string(buf=buf, **kwargs)

    def export(self) -> List[Dict]:
        """Export applied styles as a list of dicts."""
        return self._styler.export()

    def use(self, styles: List[Dict]) -> 'Styler':
        """Apply exported styles from another Styler."""
        return Styler(self._styler.use(styles))

    # ------------------------------------------------------------------
    # pandasv2 extras
    # ------------------------------------------------------------------

    def to_web(self, **kwargs) -> str:
        """
        Render to HTML string for web responses.

        Returns the full HTML table with embedded CSS — ready to inject
        into any HTML page or return from a web endpoint.

        Example:
            >>> html = df.style.background_gradient().to_web()
            >>> return HTMLResponse(content=html)
        """
        return self._styler.to_html(**kwargs)

    def to_json_safe(self, orient: str = 'records') -> str:
        """
        Serialize the underlying data to JSON (styles are not exported).

        Useful when you want the data but need JSON instead of HTML.

        Example:
            >>> json_str = df.style.format('{:.2f}').to_json_safe()
        """
        from .core import to_json
        return to_json(self._styler.data)

    def export_css(self) -> str:
        """
        Extract only the CSS rules generated by this Styler.

        Returns a plain CSS string you can embed in a <style> tag.

        Example:
            >>> css = df.style.background_gradient().export_css()
        """
        html = self._styler.to_html()
        import re
        match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ''

    @property
    def data(self):
        """Access the underlying DataFrame."""
        from .dataframe import DataFrame
        return DataFrame(self._styler.data)

    def __repr__(self) -> str:
        return f"[pandasv2.Styler]\n{self._styler.__repr__()}"

    def _repr_html_(self) -> str:
        return self._styler._repr_html_()
