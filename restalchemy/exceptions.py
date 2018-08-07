from pyramid.httpexceptions import HTTPClientError


class ApiError(HTTPClientError):
    errno = 1
    code = 400  # HTTPBadRequest

    def __init__(self, error, error_id=None):
        r_json = {"success": False, "errno": self.errno, "error": error}
        if error_id:
            r_json["error_id"] = error_id
        super().__init__(json=r_json)


class InternalServerError(ApiError):
    """500 Internal Server Error."""

    errno = 500
    code = 500  # HTTPInternalServerError

    def __init__(self, error_id=None):
        super().__init__(
            "Sorry, We're experience some technical issues and can't process "
            "your request right now. Please try again later.",
            error_id,
        )


# User error


class BadRequest(ApiError):
    errno = 11

    def __init__(self, error="Bad request"):
        super().__init__(error)


class InvalidJson(ApiError):
    errno = 12

    def __init__(self, error="Invalid json data"):
        super().__init__(error)


class MissingParameters(ApiError):
    errno = 13
    title = "Missing Parameters"

    def __init__(self, error="Missing parameters"):
        super().__init__(error)


class FilterInvalid(ApiError):
    errno = 14

    def __init__(self, msg=None, error="Invalid filter"):
        if msg is not None:
            error = error + ": " + msg
        super().__init__(error)


# Authentication


class Unauthorized(ApiError):
    """ 401 Unauthorized """

    errno = 21
    code = 401  # HTTPUnauthorized

    def __init__(self, error="User unauthorized"):
        super().__init__(error)


class Forbidden(ApiError):
    """ 403 Forbidden """

    errno = 21
    code = 403  # HTTPForbidden

    def __init__(self, error="User unauthorized"):
        super().__init__(error)


class WrongLogin(ApiError):
    errno = 22
    code = 401  # HTTPUnauthorized

    def __init__(self, error="Wrong login and/or password"):
        super().__init__(error)


class InvalidAuthToken(ApiError):
    errno = 23
    code = 401

    def __init__(self, error="Invalid authentication token"):
        super().__init__(error)


# Model errors


class ResourceNotFound(ApiError):
    code = 404  # HTTPNotFound
    title = "Not Found"
    errno = 31

    def __init__(self, error="Resource not found"):
        super().__init__(error)


class ModelNotFound(ApiError):
    code = 404  # HTTPNotFound
    title = "Not Found"
    errno = 32

    def __init__(self, error="Model not found"):
        super().__init__(error)


class ModelReadOnly(ApiError):
    code = 405  # HTTPMethodNotAllowed
    errno = 33

    def __init__(self, model_name):
        super().__init__("{} is read-only".format(model_name))


# Attribute errors


class AttributeNotFound(ApiError):
    code = 404  # HTTPNotFound
    title = "Not Found"
    errno = 41

    def __init__(self, attribute=None, error="Attribute not found"):
        if attribute is not None:
            error = error + ": " + attribute
        super().__init__(error)


class AttributeReadOnly(ApiError):
    code = 404  # HTTPNotFound
    errno = 42

    def __init__(self, attribute=None, error="Attribute read only"):
        if attribute is not None:
            error = error + ": " + attribute
        super().__init__(error)


class AttributeWrong(ApiError):
    errno = 42

    def __init__(self, attribute=None, message=None, error="Wrong attribute"):
        if attribute is not None:
            error = error + ": " + attribute
        if message is not None:
            error = error + " - " + message
        super().__init__(error)


# Query parameter errors


class ParamWrong(ApiError):
    errno = 51

    def __init__(self, param=None, error="Wrong query paramter"):
        if param is not None:
            error = error + ": " + param
        super().__init__(error)
