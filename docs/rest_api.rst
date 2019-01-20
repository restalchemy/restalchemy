.. _rest_api:

========
REST API
========

Overview
========

RESTAlchemy provides a very intuitive and simple but still very powerful
REST API.

It's designed for 95% of usages of JSON REST APIs, which is to give
the user easy access to the data storage of your application from
a browser or other apps.

See comparisons_ to see how RESTAlchemy calls look compared to other
popular frameworks.


API Endpoints
=============

RESTAlchemy uses the common REST API scheme for URLs where you can
access the collection of your resource (on Python side, this would be a
list of your SQLAlchemy models) under `/{resource}`.  You can access one
particular resource (in Python that would be a single instance of your
model) with `/{resource}/{ID}` and you can access an attribute from this
resource (which can again be a resource or a collection or resources)
with `/{resource}/{ID}/{attribute}`.

It's also convention to include the API version in the URL, so
the first path segment must always be the API version. E.g. `/v1/`.

Quick overview of URL endpoints (need to be prefixed with version number):

HTTP GET to query:
  - `/{resource}`: Return a list of resources.
  - `/{resource}/{ID}`: Return a resource
  - `/{resource}/{ID}/{attribute}`: Return attribute of a resource

HTTP POST to create:
  - `/{resource}`: Create a new resource
  - `/{resource}/{ID}/{attribute}`: Only possible if `{attribute}` is
    list of resources. Then it will append a newly created resource.

HTTP PUT to update:
  - `/{resource}/{ID}`: Update existing resource
  - `/{resource}/{ID}/{attribute}`: Update attribute of existing resource

HTTP DELETE to delete:
  - `/{resource}/{ID}`: Delete resource
  - `/{resource}/{ID}/{attribute}`: Only possible if `{attribute}` is
    a relation to another resources. Then it will delete the resource
    and reference to it.


Query parameters
================

- ``limit``:
  Limit the number of entries to return. (default: 100; default maximum limit is 1000)

- ``offset``:
  Number of entries to skip. (default: 0)

- ``sort``:
  attribute to sort by in descending order. You can optionally specify the sort order by
  appending .asc or .desc to the attribute (default: id.asc).
  You can also sort by sub-attributes, e.g. GET ``/v3/creatives?sort=category.name.asc``
  or by quickstats, e.g. GET ``/v3/campaigns?quickstats&sort=quickstats.lifetime.clicks.asc``.
  If you specify a relationship model without specifying an attribute of it you sort by count.
  E.g. GET ``/v3/publishers?sort=sites.desc&limit=5`` returns the 5 publishers that have
  the most sites.

- ``depth``:
  Specifies how attributes that are relationships to another model or a list of other models is returned.
  There are 3 options:
    * depth=0: don't return any relationship attributes at all
    * depth=1: return a list of attribute IDs  (default)
    * depth=2: return the expanded attribute objects

- ``attributes``:
  comma separated list of attributes you want to have included in your result.
  You can also exclude certain attributes bei prepending '!' to the attribute name.
  (not set as defaults and all attributes are returned)
  e.g. get sites but only return id and names without anything else: HTTP GET to ``/v3/sites?attributes=id,name``
  or get advertiser with id 3 but without campaigns and creatives attribute:
  ``/v3/advertiser/3?attributes=!creatives,!campaigns``

- ``expand``:
  comma separated list of attributes to expand (instead of only showing the ID(s)).
  Useful if you don't want to set `depth` to a higher value because you only want one or a few
  attributes expanded or you set depth to 2 already and want to expand one attribute a level
  deeper. (not set as default)
  E.g. get all sites and also expand the domains ``/v3/sites?expand=domain``

- ``attribute filter``:
  every attribute other then the above (limit, offset, sort, depth, attributes, expand) is used
  as a filter for the result set. The URL parameter in general looks like ``attribute_to_filter=filter_string``
  If ``attribute_to_filter`` is starting with `!` the filter is negated.
  ``filter_string`` can be a comma separated list of multiple values or contain `*` as wildcard
  for matches in strings. (no filter set as default)
  E.g. find all .mx TLDs ``/v3/domains?hostname=*.mx``


Special Endpoints
=================

If you use the authentication module from RESTAlchemy,
you get a special `/login` endpoint to receive an auth token.
What JSON you exactly have to post to this API is depending on the
implementer. See :ref:`authentiaction` for more details.


Custom endpoints or query parameters
====================================

RESTAlchemy gives you the full power of Pyramid_, so it's easy to
overwrite the default URL routes or query parameters or add your own.

See :ref:`configuration` for a way to change routes/query parameters or create
new ones.


Examples
========

Usage with curl
---------------

To login and receive the authentication token:

.. code-block:: bash

    $ curl -X POST -d '{"email": "test@example.com", "password": "test"}' -H "Content-Type: application/json" localhost:6543/v1/login

A sample response would be:

.. code-block:: http

    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8
    Date: Tue, 28 Oct 2014 11:37:25 GMT

    {
        "auth_token": "your-long-token-here",
        "message": "test (user id 1) logged in",
        "success": true,
        "user": {
            "created_at": "2014-09-09T15:34:56",
            "email": "test@example.com",
            "id": 1,
            "name": "test",
            "updated_at": "2014-10-14T19:01:11"
        }
    }


Now you can pass the auth token in the header of your next request(s) to
access more resources.
To do so add an 'Authorization' Header with 'Bearer ' + ``auth_token`` as value.

E.g. get all sites:

.. code-block:: bash

    $ curl -H 'Authorization: Bearer your-long-token-here' localhost:6543/v1/todos

Would result in a json response that lists all TODOs available for the
test@example.com user:

.. code-block:: http

    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    {
        "filter": [],
        "limit": null,
        "offset": null,
        "todos": [
            {
                "id": 5,
                "todo": 'todo five',
                "description": "todo description",
                "created_at": "2014-10-29T17:36:42",
                "updated_at": "2014-10-29T17:38:25"
            },
            {
                "id": 9,
                "todo": 'todo nine',
                "description": "todo description",
                "created_at": "2014-10-29T18:36:42",
                "updated_at": "2014-10-29T18:38:25"
            },
            /* {... more todos */ ...}
        ],
        "sort": "id.asc",
        "success": true,
        "timestamp": "2015-04-03T00:14:35.072516"
    }


To create a new entry you have to POST with the necessary data you want to set.
E.g. creating a new `todo`:

.. code-block:: bash

    $ curl -H 'Authorization: Bearer your-long-token-here' -X POST -d '{"todo": "test todo", "description": "test description"}' -H "Content-Type: application/json" localhost:6543/v1/todo

Would create a new todo and the response would look like:

.. code-block:: http

    HTTP/1.1 200 OK
    Content-Type: application/json; charset=UTF-8

    {
        "todo": {
            "id": 23,
            "todo": "test todo",
            "description": "test description"
            "created_at": "2014-10-28T21:56:44",
        },
        "status": "OK"
    }


API Client Libraries
--------------------

- Python: https://github.com/restalchemy/restalchemy-client-python
- Emacs: https://github.com/restalchemy/restalchemy-client-emacs
- TODO JavaScript: https://github.com/restalchemy/restalchemy-client-javascript
- TODO Go: https://github.com/restalchemy/restalchemy-client-go

Comparisons
===========

Let's look at some common queries and there outputs with
RESTAlchemy_, `Eve <https://docs.python-eve.org>`_,
`JSON API <https://jsonapi.org/>`_ and
`Django Rest Framework <https://www.django-rest-framework.org/>`_

TODO

.. _RESTAlchemy: https://www.restalchemy.org
.. _Pyramid: https://trypyramid.com
.. _configuration: configuration
