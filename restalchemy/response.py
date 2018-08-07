from pyramid.response import Response as PyramidResponse

from typing import NamedTuple


class RestResponse(NamedTuple):
    name: str
    resource: list
    return_info: dict


class Response(PyramidResponse):
    # FIXME
    def __init__(success=True, webob=None, **kwargs):
        """RESTAlchemy response object.
        :success bool: Indicates if API call was successful or not

        webob: `dict` that get's passed to the `webob.response.Response` constructor
        """
        if webob is None:
            webob = {}

        super().__init__(**webob)

        resp = {k: v for k, v in kwargs.items()}
        if "success" not in resp:
            resp["success"] = success

        return resp
