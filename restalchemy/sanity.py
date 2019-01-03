from json import JSONDecodeError

from .exceptions import BadRequest, InvalidJson


def check_junk_encoding(request):
    # We're going to test our request a bit, before we pass it into the
    # handler. This will let us return a better error than a 500 if we
    # can't decode these.

    # Ref: https://github.com/Pylons/webob/issues/161
    try:
        request.GET.get("", None)
    except UnicodeDecodeError:
        raise BadRequest("Invalid bytes in query string.")

    # Ref: https://github.com/Pylons/webob/issues/115
    # Look for invalid bytes in a path.
    try:
        request.path_info
    except UnicodeDecodeError:
        raise BadRequest("Invalid bytes in URL.")


def check_json(request):
    if request.content_length > 0:
        try:
            rjson = request.json
        except JSONDecodeError:
            raise InvalidJson
        if not isinstance(rjson, dict):
            raise InvalidJson("JSON data is not an object")


def sanity_tween_factory(handler, registry):
    def sanity_tween(request):
        check_junk_encoding(request)
        if request.method not in ["GET", "DELETE"]:
            check_json(request)

        return handler(request)

    return sanity_tween


def includeme(config):
    config.add_tween("restalchemy.sanity.sanity_tween_factory")
