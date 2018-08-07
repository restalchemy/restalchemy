"""RESTAlchemy CORS module.

If this module is included, the API will answer to HTTP OPTIONS requests
and add CORS headers to the response when the request has the 'Origin' header set.

'Same Origin Policy'
See http://www.w3.org/wiki/CORS_Enabled

"""
from pyramid.config import Configurator
from pyramid.security import NO_PERMISSION_REQUIRED

from . import RestalchemyConfig


class CorsPreflightRoutePredicate:
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return "cors_preflight = %s" % bool(self.val)

    phash = text

    def __call__(self, context, request):
        if not self.val:
            return False
        return (
            request.method == "OPTIONS"
            and "Origin" in request.headers
            and "Access-Control-Request-Method" in request.headers
        )


def add_cors_to_response(event):
    request = event.request
    headers = event.response.headers
    headers["Access-Control-Allow-Credentials"] = "true"

    if "Origin" in request.headers:
        rest_config: RestalchemyConfig = request.registry.restalchemy
        origin = request.headers["Origin"]
        if rest_config.allowed_origins and origin not in rest_config.allowed_origins:
            origin = rest_config.allowed_origins[0]
        headers["Vary"] = "Origin"
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Expose-Headers"] = (
            "Content-Type,Content-Length,Date," "Authorization,X-Request-ID"
        )
        headers["Access-Control-Allow-Origin"] = origin


def cors_options_view(context, request):
    headers = request.response.headers
    if "Access-Control-Request-Headers" in request.headers:
        headers["Access-Control-Allow-Methods"] = "OPTIONS,HEAD,GET,POST,PUT,DELETE"

    headers["Access-Control-Allow-Headers"] = (
        "Origin,X-Requested-With,Content-Type,Accept-Language,"
        "Accept,Authorization,If-None-Match,If-Modified-Since"
    )
    return request.response


def includeme(config: Configurator):
    config.add_route_predicate("cors_preflight", CorsPreflightRoutePredicate)
    config.add_route("cors-options-preflight", "/{catch_all:.*}", cors_preflight=True)
    config.add_view(
        cors_options_view, route_name="cors-options-preflight", permission=NO_PERMISSION_REQUIRED
    )

    config.add_subscriber(add_cors_to_response, "pyramid.events.NewResponse")
