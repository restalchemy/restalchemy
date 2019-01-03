import logging
from functools import partial
from json.decoder import JSONDecodeError
from typing import Optional, Set

from pyramid.config import Configurator
from pyramid.request import Request

from .exceptions import AttributeNotFound, AttributeReadOnly, InvalidJson


log = logging.getLogger("restalchemy")


class RestalchemyBase:
    """Base class for RESTAlchemy models.

    There are some special methods that will be called
    when they're defined to check access rights,
    or before and after modifications of the models:

    __before_get__(self, request, data) -> data
    __after_get__(self, request) -> None

    __before_create__(cls, request, data) -> data
    __after_create__(self, request) -> None
    __create_json__(cls, request, json) -> json

    __before_update__(self, request, data) -> data
    __after_update__(self, request) -> None
    __modify_json__(self, request, json) -> json

    __before_delete__(self, request, data) -> None
    __after_delete__(self, request) -> None

    -----

    For write update:

    __writeable_attributes__ = []  # List of attributes that the user is allowed to set
    __read_only_attributes__ = []  # List of attributes that are read only and not allowed to be set by the user

    __get_writable_attributes__(cls, request) -> List of writable attributes
    __get_read_only_attributes__(cls, request) -> List of read only attributes

    # special definition just for creation and not update

    __create_writeable_attributes__ = []  # List of attributes that the user is allowed to set
    __create_read_only_attributes__ = []  # List of attributes that are read only and not allowed to be set by the user
    __create_get_writable_attributes__(cls, request) -> List of writable attributes
    __create_get_read_only_attributes__(cls, request) -> List of read only attributes

    # special definition just for update and not create

    __update_writeable_attributes__ = []  # List of attributes that the user is allowed to set
    __update_read_only_attributes__ = []  # List of attributes that are read only and not allowed to be set by the user
    __update_get_writable_attributes__(cls, request) -> List of writable attributes
    __update_get_read_only_attributes__(cls, request) -> List of read only attributes

    Helper function
    _update_from_json(request, data, is_create, is_update)

    -----

    Return sqlalchemy model as json based on function arguments or attributes on
    the model. Available model attributes are:

    __json_include__ = []  # list of attributes to return  (default: all)
    __json_exclude__ = []  # list of attributes to NOT return (applied *after* json_include (default: empty))
    __json_private__ = []  # list of attributes that are private and can NEVER be viewed by any user
    __json_expand__ = []  # list of attributes to expand by default
    __json_depth__ = 1  # default depth for this model
    __json_show_attribute__  # function to determine if attribute should be shown or not
    __json_return_{attribute}__  # function who's return value is used for the json instead of the real value
    """

    def __single_resource_name__(self, request: Request) -> str:
        """Method that returns the same when a single resource is returned."""
        from .utils import camel_case_to_snake_case

        return camel_case_to_snake_case(self.__class__.__name__)

    @classmethod
    def __list_resource_name__(cls, request: Request) -> str:
        """Method that returns the same when a list of this resource is returned."""
        return cls.__tablename__  # type: ignore

    # Get life cycles
    def __after_get__(self, request: Request) -> None:
        """Method that is called after the model got fetched."""

    def __after_attribute_get__(self, request: Request, attribute: "RestalchemyBase") -> None:
        """Method that is called (on the model) after an attribute got fetched."""

    # Create life cycles
    def __before_create__(self, request: Request) -> Optional[dict]:
        """Get and update json data before creating the model.
        If this method returns data, it is used instead of the original json data.
        """

    def __after_create__(self, request: Request) -> None:
        """Method that is called after the model got created."""

    def __after_attribute_create__(self, request: Request, attribute: "RestalchemyBase") -> None:
        """Method that is called (on the model) after an attribute got created."""

    # Update life cycles
    def __before_update__(self, request: Request) -> Optional[dict]:
        """Get and update json data before updating the model.
        If this method returns data, it is used instead of the original json data.
        """

    def __after_update__(self, request: Request) -> None:
        """Method that is called after the model got updated."""

    def __after_attribute_update__(self, request: Request, attribute: "RestalchemyBase") -> None:
        """Method that is called (on the model) after an attribute got updated."""

    # Delete life cycles
    def __before_delete__(self, request: Request) -> None:
        """Method that is called before the model is deleted."""

    def __after_attribute_delete__(self, request: Request, attribute: "RestalchemyBase") -> None:
        """Method that is called (on the model) after an attribute got deleted."""

    @classmethod
    def __get_read_only_attributes__(
        cls, request: Request = None, is_create: bool = False, is_update: bool = False
    ) -> Set[str]:
        return set(request.registry.restalchemy.read_only_attributes)  # type: ignore

    # Helper methods
    @classmethod
    def _get_read_only_attributes(
        cls, request: Request = None, is_create: bool = False, is_update: bool = False
    ) -> Set[str]:
        """Return read only attributes.

        It will return a list of read only attributes that it gets from: (if they're defined)
        - `read_only_attributes` defined in the restalchemy config (if `request` is passed)
        - `cls.__get_read_only_attributes__(request, is_create, is_update)` (`request` is passed)
        - `cls.__read_only_attributes__`
        - `cls.__create_read_only_attributes__` if :param:`is_create` is ``True``
        - `cls.__update_read_only_attributes__` if :param:`is_update` is ``True``
        - Add SQLAlchemy's `metadata` property
        - Add all properties starting with `_`

        :param Request request: Pyramid :class:`Request` request object
        :param bool is_create: Add attributes from `__create_read_only_attributes__` method
        :param bool is_update: Add attributes from `__update_read_only_attributes__` method
        :returns: List of read only attributes
        """
        if request:
            attrs = cls.__get_read_only_attributes__(request, is_create, is_update)
        else:
            attrs = set()

        attrs.update(getattr(cls, "__read_only_attributes__", []))
        if is_create:
            attrs.update(getattr(cls, "__create_read_only_attributes__", []))
        if is_update:
            attrs.update(getattr(cls, "__update_read_only_attributes__", []))

        # Add sqlalchemy metadata property
        attrs.add("metadata")

        # Only return properties that are actually defined
        # and add private properties that start with underscore
        return set(a for a in dir(cls) if (a.startswith("_") or a in attrs))

    @classmethod
    def __get_writable_attributes__(
        cls, request: Request = None, is_create: bool = False, is_update: bool = False
    ) -> Set[str]:
        return set(request.registry.restalchemy.writable_attributes)  # type: ignore

    @classmethod
    def _get_writable_attributes(
        cls, request: Request = None, is_create: bool = False, is_update: bool = False
    ) -> Set[str]:
        """Return writable attributes.

        It will return a list of writable attributes that it gets from: (if they're defined)
        - `writable_attributes` defined in the restalchemy config (if `request` is passed)
        - `cls.__get_writable_attributes__(request, is_create, is_update)` (`request` is passed)
        - `cls.__writable_attributes__`
        - `cls.__create_writable_attributes__` if :param:`is_create` is ``True``
        - `cls.__update_writable_attributes__` if :param:`is_update` is ``True``
        - If all of those lists return nothing, assume all attributes count as writable
        - Then remove all read only attributes from this list

        :param Request request: Pyramid :class:`Request` request object
        :param bool is_create: Add attributes from `__create_writable_attributes__` method
        :param bool is_update: Add attributes from `__update_writable_attributes__` method
        :returns: List of writable attributes
        """
        if request:
            attrs = cls.__get_writable_attributes__(request, is_create, is_update)
        else:
            attrs = set()

        attrs.update(getattr(cls, "__writable_attributes__", []))
        if is_create:
            attrs.update(getattr(cls, "__create_writable_attributes__", []))
        if is_update:
            attrs.update(getattr(cls, "__update_writable_attributes__", []))

        if not attrs:
            attrs = set(dir(cls))
        else:
            attrs.intersection_update(dir(cls))  # Only return properties that are actually defined

        read_only_attrs = cls._get_read_only_attributes(request, is_create, is_update)
        attrs.difference_update(read_only_attrs)

        return attrs

    def _update_from_json(
        self,
        request: Request = None,
        data: dict = None,
        is_create: bool = False,
        is_update: bool = False,
    ):
        """Update model from from json.

        Update `self` with (json) data from :param:`data` or
        :param:`request` respecting the writable or read only attributes
        defined on the model.
        When :param:`is_create` is ``True`` also respect the special
        writable and read only attributes for the 'create' case
        and when :param:`is_update` is ``True`` same for 'update'.
        """
        from .validators import validate

        if data is None:
            assert request is not None, "You have to pass either `data` or `request`"
            try:
                data = request.json
            except JSONDecodeError:
                raise InvalidJson
        if not isinstance(data, dict):
            raise InvalidJson("JSON data is not an object")

        writeable_attrs = self._get_writable_attributes(request, is_create, is_update)
        for k, v in data.items():
            if not hasattr(self, k):
                raise AttributeNotFound(k)
            if k not in writeable_attrs:
                raise AttributeReadOnly(k)
            v = validate(v, getattr(type(self), k))
            setattr(self, k, v)

    def _reset(
        self,
        request: Request = None,
        data: dict = None,
        is_create: bool = False,
        is_update: bool = False,
    ):
        """Set all writable attributes back to it's database default value."""
        for attr in self._get_writable_attributes(request, is_create, is_update):
            try:
                a = getattr(self.__class__, attr).default
            except AttributeError:
                # FIXME: relationships
                log.warning(f"No 'default' attribute for attr: {self.__class__.__name__}.{attr}")
                continue
            if a is None:
                a = getattr(self.__class__, attr).server_default
            if a is not None:
                a = a.arg
            setattr(self, attr, a)


def set_get_model_function(config, get_model_fn):
    """Sets the get model function.

    :param:`get_model_fn` is a function (can be dotted) that takes a string
    and return the model class for it.

    It should have this signature:
    `get_model(name: str) -> Optional[RestalchemyBase]`
    """
    get_model_fn = config.maybe_dotted(get_model_fn)

    config.add_request_method(
        lambda r: partial(get_model_fn, r), "restalchemy_get_model", reify=True
    )


def includeme(config: Configurator):
    config.add_directive("set_get_model_function", set_get_model_function, action_wrap=True)
