from typing import Any, List, Optional, Tuple

from pyramid.request import Request
from sqlalchemy import distinct, func
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.query import Query

from .exceptions import AttributeNotFound, AttributeWrong, FilterInvalid
from .model import RestalchemyBase
from .validators import validate


def sort_query(request: Request, Model: RestalchemyBase, query: Query, sort: str) -> Query:
    """Return a query with sorting applied.

    Take :param:`query` for model :param:`Model` and return a new query
    with :param:`sort` parameters applied.
    """
    return query


def filter_query(
    request: Request, query: Query, Model: RestalchemyBase, filter_by: str, value: str
) -> Query:
    negate = filter_by.endswith("!")  # negate filter when last char is !
    less_equal = filter_by.endswith("<")  # use less equal when last char is <
    greater_equal = filter_by.endswith(">")  # use greater equal when last char is >
    filter_by = filter_by.rstrip("!<>")

    # When a filter ends with an underscore, simply ignore it.
    # Appending '_' is allowed to avoid a conflict with a reserved word like
    # 'limit' or 'offset' etc.
    if filter_by.endswith("_"):
        filter_by = filter_by[:-1]

    # FilterModel is the model who's attribute will be used for the filter
    FilterModel: RestalchemyBase = Model
    if "." in filter_by:
        # when filtered by a full name assume a join
        model2_name, filter_by = filter_by.split(".", 1)

        Model2 = request.restalchemy_get_model(model2_name)
        if not Model2:
            raise AttributeNotFound(model2_name)

        if Model != Model2:
            try:
                FilterModel = Model2 = aliased(Model2)  # type: ignore
                # LEFT JOIN so you can query `Model2.attr='null'`
                query = query.outerjoin(Model2)
                # FIXME: specify join argument like
                # ``query = query.outerjoin(Model2, Model.model2_name)``
                # otherwise sqla can't find the join with some multiple filters like:
                # `/v3/creatives?bans.reason=null&advertiser.network_id!=9&sort=quickstats.today.clicks.desc`

                # Allow 1 more join to filter stuff like /campaigns?profile.segments_filter.segments_id=14
                if "." in filter_by:
                    model3_name, filter_by = filter_by.split(".", 1)
                    Model3 = request.restalchemy_get_model(model3_name)
                    if not Model3:
                        raise AttributeNotFound(model3_name)

                    # Join Model 3 with Model2 (SQLAlchemy knows how)
                    # and filter attribute on Model3
                    if Model3 not in [Model, Model2]:
                        FilterModel = aliased(Model3)  # type: ignore
                        query = query.outerjoin(FilterModel)
            except InvalidRequestError:
                raise AttributeWrong(model2_name)

    # FIXME: ???? validate list (otherwise DBAPIError is raised)!
    try:
        filter_attr = getattr(FilterModel, filter_by)
    except AttributeError:
        raise AttributeNotFound(filter_by)

    # If filter_attr is n to m relationship, the value is always `IN` and
    # we have to join the secondary table.
    if isinstance(filter_attr, InstrumentedAttribute) and hasattr(
        filter_attr.property, "secondary"
    ):
        target: Any = request.restalchey_get_model(filter_attr.property.target.name)
        # Without `DISTINCT` models matching multiple filter values will return multiple
        # rows which sqlalchemy combines to one, resulting in less rows total then
        # the specified `limit` rows
        query = query.outerjoin(filter_attr)
        if isinstance(value, str) and value.lower() == "null":
            if negate:
                return query.filter(target.id != None)
            else:
                return query.filter(target.id == None)
        elif negate:
            return query.filter(target.id.notin_(value.split(","))).distinct()
        else:
            return query.filter(target.id.in_(value.split(","))).distinct()

    # else

    if isinstance(value, str) and "," in value:
        if less_equal or greater_equal:
            raise FilterInvalid(msg="Less or greater equal only allowed with single values.")
        if negate:
            return query.filter(filter_attr.notin_(value.split(",")))
        return query.filter(filter_attr.in_(value.split(",")))

    if isinstance(value, str) and "*" in value:
        if less_equal or greater_equal:
            raise FilterInvalid(msg="Less or greater equal is not allowed for wildcards (`*`).")
        validate(value, filter_attr)
        value = value.replace("*", "%")

        if negate:
            return query.filter(~getattr(FilterModel, filter_by).like(value))
        else:
            return query.filter(getattr(FilterModel, filter_by).like(value))

    if isinstance(value, str) and value.lower() == "null":
        value = None  # type: ignore
    validate(value, filter_attr)
    if negate:
        return query.filter(filter_attr != value)
    if less_equal:
        return query.filter(filter_attr <= value)
    if greater_equal:
        return query.filter(filter_attr >= value)

    return query.filter(filter_attr == value)


def query_models(
    request: Request,
    model: RestalchemyBase,
    offset: int = None,
    limit: int = None,
    sort: str = None,
    filter: str = None,
) -> Tuple[List[RestalchemyBase], int, Optional[str]]:
    """Return list of models."""
    Model = request.matchdict["Model"]
    model_name = request.matchdict["model_name"]

    offset = offset or request.offset
    limit = limit or request.limit
    sort = sort or request.sort
    filter = filter or request.filter

    query = request.dbsession.query(Model)  # type: Query

    if hasattr(Model, "__read_filter__"):
        query = Model.__read_filter__(query, request)
    query = sort_query(request, Model, query, request.sort)

    # Always order by ID to get a stable sort
    # https://docs.sqlalchemy.org/en/latest/faq/ormconfiguration.html#faq-subqueryload-limit-sort
    if hasattr(Model, "id"):
        query = query.order_by(Model.id)

    for filter_by, value in filter:
        query = filter_query(request, query, Model, filter_by, value)

    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    result = query.all()

    # FIXME: sqlite? and count(*)
    # if there's a GROUP BY we count the slow way:
    # SELECT count(*) FROM (SELECT ... FROM Model ... )
    if True or query.statement._group_by_clause.clauses or not hasattr(Model, "id"):
        count = query.limit(None).offset(None).order_by(None).count()
    else:
        # Remove limit, offset and order by from query and
        # SELECT count(DISTINCT Model.id) FROM Model ...
        count_query = query.statement.with_only_columns([func.count(distinct(Model.id))])
        count = count_query.limit(None).offset(None).order_by(None).scalar()

    # FIXME: `Last-Modified` not working!
    # query too slow and it should work with expand and depth==1 etc as well
    # otherwise pretty useless.
    # FIXME: `max` function takes forever in big tables.
    last_modified = None

    return result, count, last_modified


def camel_case_to_snake_case(string: str) -> str:
    """Return snake case version of :param:`string`.

    E.g.::

        >>> model_name_to_schema('BlogEntry')
        'blog_entry'
        >>> model_name_to_schema('UserLanguage')
        'user_language'
        >>> model_name_to_schema('Country')
        'country'

    :param str string: Camel case string to convert
    :return: :class:`str` :param:`string` in snake case
    """
    snake = string[0]
    for i in range(1, len(string)):
        if string[i].isupper():
            snake += "_"
        snake += string[i]

    return snake.lower()
