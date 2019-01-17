RESTAlchemy
===========

A REST framework build on top of Pyramid_ and SQLAlchemy_.

.. warning::

   RESTAlchemy is early alpha and while working and in
   production in some of my own projects,
   it's not really ready for production.
   Before I tag a version, I will make breaking changes on
   a somewhat regular basis. Feedback welcome.


Intro
-----

If you use the SQLAlchemy_ ORM for your models,
you already specify the type of the column,
if it's nullable, a default value and other properties.

So instead of duplicating what you already specified
in your SQLAlchemy_ models and writing validation for your
REST API again either from scratch or with another utility
like `marshmallow`, RESTAlchemy inspects your models and
derives the API from this.

Of course, sometimes you want to return something else
for some attribute or restrict access to a resource etc.
For that, you have many special RESTAlchemy attributes or functions
that you can use on your model.

You don't have to jump between your view implementation, the model
and validation code. Everything is right there at your model.
(Of course, you can still split everything up if that's what you prefer).

Quick Start
-----------

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


Documentation
-------------

- Read the `tutorial <https://restalchemy.readthedocs.org/en/latest/tutorial.html>`_,
- Create a new project with `cookiecutter-restalchemy <https://github.com/restalchemy/cookiecutter-restalchemy>`_.
- Read the full `documentation online <https://restalchemy.readthedocs.org/en/latest/index.html>`_,


Support
-------

For questions and general discussion, join our
`mailing list <https://groups.google.com/forum/#!forum/restalchemy>`_.

For feature requests or bug reports open a
`GitHub issue <https://github.com/restalchemy/restalchemy/issues>`_.


Check the `website <https://www.restalchemy.org>`_ for updates.

.. _Pyramid: https://trypyramid.com
.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _cookiecutter: https://cookiecutter.readthedocs.io
