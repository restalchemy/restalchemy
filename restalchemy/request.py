from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.request import Request

from . import RestalchemyConfig
from .exceptions import BadRequest, ParamWrong


def check_params(event: NewRequest):
    """Checks that the request parameters are the right type for the
    model query (i.g. type(request.params['limit']) == int)
    and sets the params directly as request attribute (i.g. request.limit)
    """
    request: Request = event.request
    rest_conf: RestalchemyConfig = request.registry.restalchemy
    params: dict = request.params

    try:
        request.sort = params.get("sort")
    except (TypeError, UnicodeDecodeError):
        # WebOb / pyramid has problems with non standard confirm (i.i. non utf-8 encoded)
        # query params or wrong missing Content-Type headers
        # see: https://github.com/Pylons/webob/issues/161
        raise BadRequest()

    try:
        request.offset = int(params.get("offset", 0))
        if request.offset < 0:
            raise ValueError
    except ValueError:
        raise ParamWrong("`offset` must be a number >= 0")
    try:
        request.limit = min(
            int(params.get("limit", rest_conf.default_limit)), int(rest_conf.max_limit)
        )
        if request.limit <= 0:
            raise ValueError
    except ValueError:
        raise ParamWrong("`limit` must be a number > 0")
    # request.depth = int(request.registry.settings.get('default_result_depth'))
    # if 'depth' in params:
    #     try:
    #         request.depth = int(params.get('depth'))
    #     except ValueError:
    #         raise ParamWrong('`depth` must be an integer value')

    # FIXME: do fields[user]=name,!email
    # request.include = []
    # request.exclude = []
    # if params.get('attributes'):
    #     request.attributes = []
    #     for attr in params.get('attributes').split(','):
    #         attr = attr.strip()
    #         if attr.startswith('!'):
    #             request.exclude.append(attr.lstrip('!'))
    #         else:
    #             request.attributes.append(attr)
    # request.attributes = request.attributes

    request.search = params.get("search")

    request.filter = [
        (k, v) for k, v in params.items() if k not in ["limit", "offset", "include", "sort"]
    ]

    # Get relationships to include
    # FIXME: add model?
    request.include = []
    if "include" in params:
        request.include = [i.strip() for i in params.get("include").split(",") if i.strip()]


def includeme(config: Configurator):
    config.add_subscriber(check_params, NewRequest)
