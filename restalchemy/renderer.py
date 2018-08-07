import enum
from datetime import datetime
from typing import Optional

import rapidjson
from pyramid.config import Configurator
from pyramid.renderers import RendererHelper
from pyramid.request import Request
from sqlalchemy import inspect
from sqlalchemy.ext.associationproxy import _AssociationList
from sqlalchemy.orm.collections import InstrumentedList

from .model import RestalchemyBase
from .response import RestResponse


def get_expand(request: Request, model, expand=None) -> list:
    if expand is None:
        expand = []
    model_expand = []
    # make copy of expand so expand.extend with the model.__json_expand__ attributes
    # doesn't alter request.expand (passed in as argument)
    # also filter expand to only expand the root level or explicitly specified with a dot.
    for exp in expand:
        if model.__class__ == request.matchdict.get("Model"):
            if "." not in exp:
                # we're in the root level and no '.' in expand.
                model_expand.append(exp)
        else:
            # we're in a sub-level model
            if "." in exp:
                model_name, attr = exp.split(".", 1)
                if request.restalchemy_get_model(model_name) == model.__class__:
                    model_expand.append(attr)

    return model_expand + getattr(model, "__json_expand__", [])


def get_attributes(
    request: Request, model, include=None, exclude=None, private=None, expand=None
) -> list:
    if include is None:
        include = getattr(
            model,
            "__json_include__",
            # By default don't show fields starting with '_', 'validate' or `metadata`
            [
                f
                for f in dir(model)
                if not (f.startswith("_") or f.startswith("validate_") or f == "metadata")
            ],
        )

    if exclude is None:
        exclude = []
    if hasattr(model, "__json_exclude__"):
        exclude = [e for e in model.__json_exclude__ if e not in expand] + exclude
    if private is None:
        private = []
    if hasattr(model, "__json_private__"):
        exclude += model.__json_private__ + exclude + private

        exclude = getattr(model, "__json_exclude__", [])
    exclude += getattr(model, "__json_private__", [])
    # Returned attributes are included minus excluded attributes
    return [a for a in include if a not in exclude]


def serialize_model(
    request: Request, model, include=None, exclude=None, private=None, expand=None, depth=0
):
    """
    FIXME: rename expand to `include`. Instead of attributes do `fields[users]=name`
    """
    expand = get_expand(request, model, expand)
    attributes = get_attributes(request, model, include, exclude, private, expand)

    res = {}
    i = inspect(model)
    for attr in attributes:
        # If depth is 0 and it's a relationship do nothing since
        # only accessing the attribute could trigger a SQL query
        if depth == 0 and attr not in expand and attr in i.mapper.relationships:
            # Check that attr is a relationship and not a synonym.
            continue

        if request and hasattr(model, "__json_show_attribute__"):
            if not model.__json_show_attribute__(request, attr):
                continue
        if request and hasattr(model, "__json_return_{}__".format(attr)):
            val = getattr(model, "__json_return_{}__".format(attr))(request)
        else:
            val = getattr(model, attr)

        # expand objects have same depth as original model
        if attr in expand:
            expand_depth = depth
        else:
            expand_depth = depth - 1

        if callable(val):  # Ignore methods defined on models
            continue
        if (
            (
                isinstance(val, _AssociationList)
                or isinstance(val, InstrumentedList)
                or isinstance(val, list)
            )
            and len(val) > 0
            and isinstance(val[0], RestalchemyBase)
        ):
            if depth > 1 or not hasattr(val[0], "id") or attr in expand:
                val = [
                    serialize_model(request, v, include, exclude, private, expand, expand_depth)
                    for v in val
                ]
            elif depth == 1:
                val = [v.id for v in val]
            else:
                continue  # don't return relations for depth == 0
        elif isinstance(val, RestalchemyBase):
            if depth > 1 or not hasattr(val, "id") or attr in expand:
                val = serialize_model(request, val, include, exclude, private, expand, expand_depth)
            elif depth == 1:
                val = val.id  # type: ignore
            else:
                continue  # don't return relations for depth == 0

        res[attr] = val

    return res


def serialize_response(request, value):
    if hasattr(value, "__json__"):
        return value.__json__(request)
    if isinstance(value, list) or isinstance(value, set):
        return [serialize_response(request, v) for v in value]
    if isinstance(value, RestalchemyBase):
        return serialize_model(request, value)
    if isinstance(value, RestResponse):
        return serialize_response(request, value.resource)
    return value


class ApiRenderer:
    def __init__(self, info: RendererHelper) -> None:
        """Constructor: info will be an object having the
        following attributes: name (the renderer name), package
        (the package that was 'current' at the time the
        renderer was registered), type (the renderer type
        name), registry (the current application registry) and
        settings (the deployment settings dictionary)."""
        # print('name',     info.name)
        # print('package',  info.package)
        # print('type',     info.type)
        # print('registry', info.registry)
        # print('settings', info.settings)
        self.settings = info.settings

    def __call__(self, value, system: dict) -> str:
        """Call the renderer implementation with the value
        and the system value passed in as arguments and return
        the result (a string or unicode object).  The value is
        the return value of a view.  The system value is a
        dictionary containing available system values
        (e.g., view, context, and request)."""
        request: Optional[Request] = system.get("request")
        name = "json"
        if request is not None:
            name = request.matchdict.get("model_name", name)
            response = request.response
            if response.content_type == response.default_content_type:
                response.content_type = "application/json"

        # If a view returns a string, we just assume it's already
        # json encoded and simply return it.
        if isinstance(value, str):
            return value

        r = {"success": True, "timestamp": datetime.now()}
        if isinstance(value, RestalchemyBase):
            name = value.__single_resource_name__(request)
        elif isinstance(value, RestResponse):
            name = value.name
            r = {**r, **value.return_info}

        resp = serialize_response(request, value)

        r["resource"] = name
        r[name] = resp

        return dumps(r)


def _json_dumps_default(obj):
    if (
        isinstance(obj, set)
        or isinstance(obj, _AssociationList)
        or isinstance(obj, InstrumentedList)
    ):
        return list(obj)
    elif isinstance(obj, enum.Enum):
        return obj.value
    raise ValueError("%r is not JSON serializable" % obj)


def dumps(obj):
    """Json dump string that handles more common types.

    Like `json.dumps` but supports following additional types:
    - set
    - enum.Enum
    - datetime.date
    - datetime.datetime
    - datetime.time
    - decimal.Decimal
    - uuid.uuid4
    - sqlalchemy.ext.associationproxy._AssociationList
    - sqlalchemy.orm.collections.InstrumentedList
    """
    return rapidjson.dumps(
        obj,
        default=_json_dumps_default,
        number_mode=rapidjson.NM_DECIMAL,
        uuid_mode=rapidjson.UM_CANONICAL,
        datetime_mode=rapidjson.DM_ISO8601 | rapidjson.DM_NAIVE_IS_UTC,
    )


def includeme(config: Configurator):
    config.add_renderer(None, "restalchemy.renderer.ApiRenderer")
