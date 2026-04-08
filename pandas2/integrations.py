"""
Web framework integrations for pandas2.

Provides zero-configuration helpers for:
- FastAPI: Automatic JSONResponse handling
- Flask: JSON endpoint decorators
- Django: Response middleware

Built by Mahesh Makvana
"""

import json
from typing import Any, Callable, Optional, Dict
from .core import to_json, JSONEncoder


class FastAPIResponse:
    """
    FastAPI integration for automatic DataFrame JSON serialization.

    Usage:
        >>> from fastapi import FastAPI
        >>> from pandas2 import FastAPIResponse
        >>> app = FastAPI()
        >>>
        >>> @app.get("/data")
        >>> def get_data() -> FastAPIResponse:
        >>>     df = pd.read_csv("data.csv")
        >>>     return FastAPIResponse(df)
    """

    def __init__(self, content: Any, status_code: int = 200, headers: Optional[Dict] = None):
        """
        Initialize FastAPI response with pandas object.

        Args:
            content: DataFrame, Series, or any JSON-serializable object
            status_code: HTTP status code
            headers: Optional response headers
        """
        self.content = to_json(content)
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = 'application/json'

    def __call__(self):
        """Return response as dict for FastAPI."""
        return {
            'body': self.content,
            'status_code': self.status_code,
            'headers': self.headers,
            'media_type': self.media_type,
        }


class FlaskResponse:
    """
    Flask integration for automatic DataFrame JSON serialization.

    Usage:
        >>> from flask import Flask
        >>> from pandas2 import FlaskResponse
        >>> app = Flask(__name__)
        >>>
        >>> @app.route("/data")
        >>> def get_data():
        >>>     df = pd.read_csv("data.csv")
        >>>     return FlaskResponse(df)
    """

    def __init__(self, content: Any, status_code: int = 200):
        """
        Initialize Flask response with pandas object.

        Args:
            content: DataFrame, Series, or any JSON-serializable object
            status_code: HTTP status code
        """
        self.content = to_json(content)
        self.status_code = status_code

    def get_response(self):
        """Return Flask-compatible response tuple."""
        from flask import Response
        return Response(
            response=self.content,
            status=self.status_code,
            mimetype='application/json'
        )

    def __call__(self):
        """Make response callable."""
        return self.get_response()


class DjangoResponse:
    """
    Django integration for automatic DataFrame JSON serialization.

    Usage:
        >>> from django.http import JsonResponse
        >>> from pandas2 import DjangoResponse
        >>>
        >>> def get_data(request):
        >>>     df = pd.read_csv("data.csv")
        >>>     return DjangoResponse(df)
    """

    def __init__(self, content: Any, status: int = 200, safe: bool = False):
        """
        Initialize Django response with pandas object.

        Args:
            content: DataFrame, Series, or any JSON-serializable object
            status: HTTP status code
            safe: Whether to allow non-dict objects
        """
        self.content_json = to_json(content)
        self.status = status
        self.safe = safe

    def get_response(self):
        """Return Django-compatible JsonResponse."""
        from django.http import JsonResponse
        import json

        content_dict = json.loads(self.content_json)
        return JsonResponse(
            data=content_dict,
            status=self.status,
            safe=self.safe
        )

    def __call__(self):
        """Make response callable."""
        return self.get_response()


def setup_json_encoder(app: Any, framework: str = 'auto') -> None:
    """
    Configure app's JSON encoder globally.

    Automatically detects framework (FastAPI, Flask, Django) and
    sets up pandas2.JSONEncoder as the default.

    Args:
        app: Application instance (FastAPI, Flask, Django)
        framework: Framework name ('fastapi', 'flask', 'django', 'auto')

    Example:
        >>> from fastapi import FastAPI
        >>> import pandas2
        >>> app = FastAPI()
        >>> pandas2.setup_json_encoder(app)
    """
    if framework == 'auto':
        # Auto-detect framework
        if hasattr(app, 'add_route'):
            framework = 'fastapi'
        elif hasattr(app, 'route'):
            framework = 'flask'
        elif hasattr(app, 'get_wsgi_application'):
            framework = 'django'
        else:
            raise ValueError("Could not auto-detect framework")

    if framework == 'fastapi':
        from fastapi.encoders import JSONEncoder as FastAPIEncoder
        app.json_encoder = JSONEncoder

    elif framework == 'flask':
        app.json_encoder = JSONEncoder

    elif framework == 'django':
        import json
        from django.core.serializers.json import DjangoJSONEncoder

        class PandasDjangoEncoder(DjangoJSONEncoder):
            def default(self, o: Any) -> Any:
                encoder = JSONEncoder()
                try:
                    return encoder.default(o)
                except TypeError:
                    return super().default(o)

        import django.core.serializers.json
        django.core.serializers.json.DjangoJSONEncoder = PandasDjangoEncoder


def create_response_handler(
    encoder: type = JSONEncoder,
    error_handler: Optional[Callable] = None,
) -> Callable:
    """
    Create custom response handler for your application.

    Args:
        encoder: Custom JSONEncoder class
        error_handler: Optional function to handle errors

    Returns:
        Response handler function

    Example:
        >>> from fastapi import FastAPI
        >>> import pandas2
        >>>
        >>> handler = pandas2.create_response_handler()
        >>> app = FastAPI()
        >>> app.add_middleware(handler)
    """
    def handle_response(content: Any) -> str:
        """Convert content to JSON using custom encoder."""
        try:
            return json.dumps(content, cls=encoder)
        except Exception as e:
            if error_handler:
                return error_handler(e, content)
            else:
                raise

    return handle_response


def json_middleware(encoder: type = JSONEncoder) -> Callable:
    """
    Create ASGI middleware for automatic JSON encoding.

    Useful for frameworks without built-in pandas support.

    Args:
        encoder: Custom JSONEncoder class

    Returns:
        Middleware function

    Example:
        >>> from fastapi import FastAPI
        >>> import pandas2
        >>> app = FastAPI()
        >>> app.add_middleware(pandas2.json_middleware())
    """
    def middleware(app):
        async def asgi(scope, receive, send):
            if scope['type'] == 'http':
                async def send_with_json(message):
                    if message['type'] == 'http.response.body':
                        # Try to JSON-encode the body
                        try:
                            body = message.get('body', b'')
                            if body:
                                data = json.loads(body)
                                message['body'] = json.dumps(
                                    data, cls=encoder
                                ).encode()
                        except Exception:
                            pass  # Leave as is if not JSON
                    await send(message)
                return await app(scope, receive, send_with_json)
            else:
                return await app(scope, receive, send)

        return asgi

    return middleware
