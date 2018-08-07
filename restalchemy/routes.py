from pyramid.config import Configurator
from pyramid.request import Request

from .exceptions import ResourceNotFound


def is_model(info: dict, request: Request):
    """Custom route predicate that checks that the model path is an actual model.
    To verify the model name, the function that was set during configuration
    with `config.set_get_model_function` is called.
    If it is a valid model, add a "Model" key to the match dictionary with the
    return value of this function.
    """
    match = info["match"]
    Model = request.restalchemy_get_model(match["model_name"])
    if not Model:
        raise ResourceNotFound("Resource {} not found".format(match["model_name"]))
    # if hasattr(Model, '__json_depth__') and 'depth' not in request.params:
    #     request.depth = Model.__json_depth__

    match["Model"] = Model
    match["model_name"] = Model.__name__
    return True


def includeme(config: Configurator):
    config.add_route("restalchemy.root", "/")
    # config.add_route('login', '/login')
    config.add_route(
        "restalchemy.attribute",
        r"/{model_name}/{id:\d+}/{attribute}",
        custom_predicates=(is_model,),
    )
    config.add_route("restalchemy.model", r"/{model_name}/{id:\d+}", custom_predicates=(is_model,))
    config.add_route("restalchemy.models", "/{model_name}", custom_predicates=(is_model,))
