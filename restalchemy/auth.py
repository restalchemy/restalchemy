import logging
from json.decoder import JSONDecodeError

import bcrypt
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import forbidden_view_config
from restalchemy.exceptions import InvalidJson, Unauthorized, WrongLogin
from restalchemy.renderer import RestResponse
from sqlalchemy import Column, SmallInteger, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import synonym

log = logging.getLogger(__name__)


@forbidden_view_config()
def forbidden(request):
    # TODO: return HTTPForbidden if authorized (or read only model)
    return Unauthorized()


def login_factory(authenticate_fn):
    def login_fn(request):
        try:
            data = request.json_body
        except JSONDecodeError:
            raise InvalidJson
        if not isinstance(data, dict):
            raise InvalidJson("JSON data is not an object")

        auth = authenticate_fn(data)
        if not auth:
            raise WrongLogin
        user_id, expiration, counter = auth
        auth_token = request.create_jwt_token(user_id, expiration=expiration, counter=counter)
        return RestResponse(name="auth_token", return_info=auth_token)

    return login_fn


def set_authenticate_function(config, authenticate_fn):
    """Sets the authenticate function for the login view."""

    authenticate_fn = config.maybe_dotted(authenticate_fn)
    config.add_view(
        login_factory(authenticate_fn),
        request_method="POST",
        permission=NO_PERMISSION_REQUIRED,
        route_name="restalchemy.login",
    )


def includeme(config: Configurator):
    rest_config = config.registry.restalchemy

    # Pyramid requires an authorization policy to be active.
    config.set_authorization_policy(ACLAuthorizationPolicy())
    # Enable JWT authentication.
    config.include("pyramid_jwt")
    config.set_jwt_authentication_policy(auth_type="Bearer")
    config.add_route("restalchemy.login", "/" + rest_config.api_version + "/login")
    config.add_directive("set_authenticate_function", set_authenticate_function, action_wrap=True)


class PasswordMixin:
    """Adds a `password` and `password_counter` column with some helper methods.

    It adds a getter and setter for `password` that stores the
    password in bcrypt and increments `password_counter` on each write.
    It also adds :meth:`password_verify` which checks the passed
    `password` argument against the user password.
    """

    _password = Column("password", String(60))
    _password_counter = Column("password_counter", SmallInteger, nullable=False, default=0)

    def _get_password(self):
        return self._password

    def _set_password(self, password: str):
        if self._password_counter >= 255:
            self._password_counter = 0
        else:
            self._password_counter += 1
        self._password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @declared_attr
    def password(cls):
        return synonym("_password", descriptor=property(cls._get_password, cls._set_password))

    def password_verify(self, password):
        """Verify if :param:`password` matched the user password."""
        return bcrypt.hashpw(password.encode(), self.password.encode()) == self.password.encode()
