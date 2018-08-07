from hashlib import md5
from json.decoder import JSONDecodeError

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotModified
from pyramid.request import Request
from restalchemy.response import RestResponse
from sqlalchemy import inspect
from sqlalchemy.orm.base import MANYTOMANY, MANYTOONE, ONETOMANY

from .exceptions import (
    AttributeNotFound,
    AttributeWrong,
    Forbidden,
    InvalidJson,
    ModelNotFound,
    ResourceNotFound,
    Unauthorized,
)
from .model import RestalchemyBase
from .utils import query_models


def forbidden(request: Request):
    """Return unauthorized or forbidden."""
    if request.unauthenticated_userid:
        return Forbidden()
    return Unauthorized()


def notfound(request: Request):
    """Return 404 NotFound."""
    rest_config = request.registry.restalchemy
    if not request.path.startswith("/" + rest_config.api_version):
        return ModelNotFound(
            "API calls should start with the API version (`/{}`)".format(rest_config.api_version)
        )
    return ResourceNotFound()


def options_view(request: Request):
    """Return HTTP OPTIONS requests.

    Set `Allow` and `Access-Control-Request-Method` headers.
    """
    request.response.headers["Allow"] = "GET, POST, PUT, DELETE"
    if "Access-Control-Request-Method" in request.headers:
        request.response.headers["Access-Control-Request-Method"] = "GET, POST, PUT, DELETE"
    return request.response


def root(request: Request):
    """Return API version and optionally API name."""
    rest_config = request.registry.restalchemy
    res = {"api_version": rest_config.api_version}
    if rest_config.api_name:
        res["api_name"] = rest_config.api_name
    return res


def models_GET(request: Request):
    """Return models.

    E.g Return all users on HTTP GET `/users`.
    """
    Model: RestalchemyBase = request.matchdict["Model"]

    offset = request.offset
    limit = request.limit

    result, count, last_modified = query_models(request, Model)

    if last_modified:
        request.response.headerlist.append(("Last-Modified", last_modified))
    # etag = 'W/"' + md5(str(result).encode()).hexdigest() + '"'
    # request.response.headerlist.append(('ETag', etag))

    # if request.headers.get('If-None-Match') == etag or \
    #         (last_modified and last_modified <= request.headers.get('If-Modified-Since', '')):
    #     return HTTPNotModified(headers=[('ETag', etag)])

    # Build next and previous links
    params = "&".join([p + "=" + request.params[p] for p in request.params if p != "offset"])
    if count <= offset + limit:
        next_link = None
    else:
        next_link = "{}?{}&offset={}".format(request.path_url, params, offset + limit)

    if offset <= 0:
        prev_link = None
    else:
        prev_link = "{}?{}&offset={}".format(request.path_url, params, max(0, offset - limit))

    info = {
        "sort": request.sort,
        "offset": request.offset,
        "limit": request.limit,
        "filter": request.filter,
        "count": count,
        "previous": prev_link,
        "next": next_link,
    }
    return RestResponse(Model.__list_resource_name__(request), result, info)


def model_GET(request: Request):
    """Return model.

    E.g. Return user 23 on HTTP GET `/users/23`.
    """
    Model = request.matchdict["Model"]
    id = request.matchdict["id"]

    model = request.dbsession.query(Model).get(id)
    if model is None:
        raise ModelNotFound
    model.__after_get__(request)
    return model


def model_attribute_GET(request: Request):
    """Return attribute for a resource.

    E.g. Return user name on HTTP GET `/users/23/name`.
    """
    model = model_GET(request)
    attribute = request.matchdict["attribute"]

    if not hasattr(model, attribute):
        raise AttributeNotFound

    model.__after_attribute_get__(request, attribute)
    return getattr(model, attribute)


def models_POST(request: Request):
    """Create a new resource from json body."""
    try:  # Verify json first
        req_json = request.json
    except JSONDecodeError:
        raise InvalidJson

    Model = request.matchdict["Model"]
    model = Model()
    data = model.__before_create__(request)
    data = data or req_json
    model._update_from_json(request, data=data, is_create=True)
    request.dbsession.add(model)
    # Flush so we get an ID for our resource
    request.dbsession.flush()
    model.__after_create__(request)
    return model


def model_attribute_POST(request: Request):
    """Add a new resource to a model attribute.

    The model attribute has to be a 1-n or n-m relationship.

    E.g. Add a new user blog post:

        HTTP POST /users/23/blogs
        { "title": "new entry", "text": "blog text"}
    """
    model = model_GET(request)
    Model: RestalchemyBase = request.matchdict["Model"]
    model_name = model.__single_resource_name__(request)
    attr_name = request.matchdict["attribute"]

    if not hasattr(model, attr_name):
        raise AttributeNotFound(attr_name)

    mapper = inspect(Model)
    for r in mapper.relationships:
        if r.key == attr_name and r.direction in [MANYTOMANY, ONETOMANY]:
            break
    else:
        raise AttributeWrong(f"{attr_name} is not in 1-n or n-m relation to {model_name}.")

    try:  # Verify json first
        req_json = request.json
    except JSONDecodeError:
        raise InvalidJson

    RelationModel = r.mapper.class_
    rel_attr = RelationModel()
    data = rel_attr.__before_create__(request)
    data = data or req_json
    rel_attr._update_from_json(request, data=data, is_create=True)
    rel_attr.__after_create__(request)
    attr = getattr(model, attr_name)
    attr.append(rel_attr)
    # Flush so we get an ID for our resource
    request.dbsession.flush()
    model.__after_attribute_create__(request, rel_attr)
    return model


def model_PUT(request: Request):
    """Update resource from json body."""

    model = model_GET(request)
    try:  # Verify json first
        req_json = request.json
    except JSONDecodeError:
        raise InvalidJson
    data = model.__before_update__(request)
    data = data or req_json
    model._update_from_json(request, data=data, is_update=True)
    model.__after_update__(request)
    return model


def model_attribute_PUT(request: Request):
    """Update a model attribute.

    The model attribute has to be a 1-1 or n-1 relationship.

    E.g. Update user for blog post 42

        HTTP PUT /blogs/42/user
        { "name": "foobar", "language": "de"}
    """
    model = model_GET(request)
    Model = request.matchdict["Model"]
    model_name = model.__single_resource_name__(request)
    attr_name = request.matchdict["attribute"]

    if not hasattr(model, attr_name):
        raise AttributeNotFound(attr_name)

    mapper = inspect(Model)
    for r in mapper.relationships:
        if r.key == attr_name and r.direction == MANYTOONE:
            break
    else:
        raise AttributeWrong(f"{attr_name} is not in n-1 or 1-1 relation to {model_name}.")

    try:  # Verify json first
        req_json = request.json
    except JSONDecodeError:
        raise InvalidJson
    attr = getattr(model, attr_name)
    data = attr.__before_update__(request)
    data = data or req_json
    attr._update_from_json(request, data=data, is_update=True)
    attr.__after_update__(request)
    model.__after_attribute_update__(request, attr)
    return model


def model_attribute_DELETE(request: Request):
    """Delete a model attribute.

    The model attribute has to be a 1-1 or n-1 relationship.

    E.g. Delete user for blog post 42

        HTTP DELETE /blog/42/user
    """
    model = model_GET(request)
    Model = request.matchdict["Model"]
    model_name = model.__single_resource_name__(request)
    attr_name = request.matchdict["attribute"]

    if not hasattr(model, attr_name):
        raise AttributeNotFound(attr_name)

    mapper = inspect(Model)
    for r in mapper.relationships:
        if r.key == attr_name and r.direction == MANYTOONE:
            break
    else:
        raise AttributeWrong(f"{attr_name} is not in n-1 or 1-1 relation to {model_name}.")

    attr = getattr(model, attr_name)
    attr.__before_delete__(request)
    delattr(model, attr_name)
    model.__after_attribute_delete__(request, attr)
    return model


def includeme(config: Configurator):
    config.add_forbidden_view(forbidden)
    config.add_notfound_view(notfound)
    config.add_view(root, request_method="GET", route_name="restalchemy.root")

    # GET
    config.add_view(model_GET, request_method="GET", route_name="restalchemy.model")
    config.add_view(model_attribute_GET, request_method="GET", route_name="restalchemy.attribute")
    config.add_view(models_GET, request_method="GET", route_name="restalchemy.models")

    # POST
    config.add_view(models_POST, request_method="POST", route_name="restalchemy.models")
    config.add_view(model_attribute_POST, request_method="POST", route_name="restalchemy.attribute")

    # PUT
    config.add_view(model_PUT, request_method="PUT", route_name="restalchemy.model")
    config.add_view(model_attribute_PUT, request_method="PUT", route_name="restalchemy.attribute")

    # DELETE
    # config.add_view(model_DELETE, request_method="DELETE", route_name="restalchemy.model")
    config.add_view(
        model_attribute_DELETE, request_method="DELETE", route_name="restalchemy.attribute"
    )
