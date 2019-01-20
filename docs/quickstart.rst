Quickstart
==========

The quickest way to get started with a new project
is to use the RESTAlchemy cookiecutter_

.. code-block:: bash

   cookiecutter gh:restalchemy/cookiecutter-restalchemy

and follow the steps shown from this command.

You can then add your SQLAlchemy_ models in the `models` folder
and import them in `models/__init__.py`.

RESTAlchemy will automatically provide endpoints to query your
models (HTTP GET) with filter parameters, relationship expansion, etc
and endpoints for model creation (POST), update (PUT), deletion (DELETE).

The template has only a single `User` model by default that you can
query like:

.. code-block:: bash

   curl localhost:6543/v1/users

Which would return a list of users in your system:

.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: application/json; charset=UTF-8

   {
       "success": true,
       "timestamp": "2019-01-17T15:13:49.234368+00:00",
       "sort": null,
       "offset": 0,
       "limit": 100,
       "filter": [],
       "count": 1,
       "previous": null,
       "next": null,
       "resource": "users",
       "users": [{
           "created_at": "2019-01-16T17:12:33+00:00",
           "email": "user@example.com",
           "id": 1,
           "name": "User",
           "updated_at": null
       }]
   }


.. _SQLAlchemy: https://www.sqlalchemy.org/
