from typing import List, Tuple

from pyramid.config import Configurator
from pyramid.settings import asbool, aslist


class RestalchemyConfig:
    """Restalchemy config.

    self.api_version   = api_version
    self.api_name      = api_name
    self.default_limit = int(default_limit)
    self.max_limit     = int(max_limit)
    """

    def __init__(
        self,
        api_version: str = "v1",
        api_name: str = None,
        default_limit: int = 100,
        max_limit: int = 1000,
        writable_attributes: List[str] = None,
        read_only_attributes: List[str] = None,
        allowed_origins: Tuple[str] = None,
        disable_cors: bool = False,
        authenticate_fn: str = None,
    ) -> None:

        self.api_version = api_version
        self.api_name = api_name
        self.authenticate_fn = authenticate_fn
        self.default_limit = int(default_limit)
        self.max_limit = int(max_limit)

        if writable_attributes is None:
            self.writable_attributes: List[str] = []
        else:
            self.writable_attributes = aslist(writable_attributes)

        if read_only_attributes is None:
            self.read_only_attributes: List[str] = []
        else:
            self.read_only_attributes = aslist(read_only_attributes)

        self.disable_cors = asbool(disable_cors)
        self.allowed_origins = allowed_origins and aslist(allowed_origins)


def includeme(config: Configurator):
    settings = config.registry.settings

    # XXX: Make prefix dynamic but don't require the user to add 2 lines
    #      like `config.include` *and* `restalchemy_from_config`
    prefix = "restalchemy."
    options = dict(
        (key[len(prefix) :], settings[key]) for key in settings if key.startswith(prefix)
    )
    rest_config = RestalchemyConfig(**options)
    config.registry.restalchemy = rest_config

    config.include(".sanity")  # Add sanity tween
    config.include(".model")
    config.include(".renderer")
    config.include(".request")
    config.include(".predicates")
    config.include(".validators")
    if not rest_config.disable_cors:
        config.include(".cors")
    config.include(".routes", route_prefix="/" + rest_config.api_version)
    config.include(".views")
