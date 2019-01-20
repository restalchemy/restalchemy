.. _front:

============
Front Matter
============

A REST framework build on top of Pyramid_ and SQLAlchemy_.

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

Goals
=====

- DRY

  Most things you need for your REST API is already specified
  in your sql model. What type, what values are allowed,
  is it nullable or required, default values, relationships, etc.

  There is no need to write extra validation or rendering code.

- Simple to use and extend yet very powerful and flexible

  For those attributes that you want to handle differently,
  you can easily do that by adding extra methods (or variables)
  to your models without much boilerplate.

  It's really easy to only return certain attributes on some
  conditions or write your own create/change/query functions.


- Provide a simple and easy to use REST Interface

  With a very quick look at a few API calls, the user should
  be able to figure out how to query stuff without much thinking
  and the URL schema and query parameters should feel "natural".

  You can easily query a resource with some relationships expanded
  without having to do multiple calls or stitching your model
  back together like in most other REST frameworks.


Project Info
============

The python `restalchemy` package is hosted on `github <https://github.com/restalchemy/restalchemy>`_.

Releases and project status are available on `Pypi <http://pypi.python.org/pypi/restalchemy>`_.

The most recent published version of this documentation is at
`<http://restalchemy.readthedocs.org/en/latest/index.html>`_.


Support
=======

For questions and general discussion, join our
`mailing list <https://groups.google.com/forum/#!forum/restalchemy>`_.

For feature requests or bug reports open a
`GitHub issue <https://github.com/restalchemy/restalchemy/issues>`_.

Check the `website <https://www.restalchemy.org>`_ for updates.


Installation
============

Existing app
------------

If you already have a Pyramid_ app and want to extend your app
with REST functionality, simply

.. code-block:: bash

    $ pip install restalchemy

And add RESTAlchemy to your :class:`pyramid.config.Configurator` object
with `config.include("restalchemy")`.

You have to tell RESTAlchemy how to find your models, for that
you need to set a function with :func:`config.set_set_model_function`
that takes a string (which is the model name as part of the URL)
and returns your model class or `None`.
You can check `this function <https://github.com/restalchemy/cookiecutter-restalchemy/blob/master/%7B%7Bcookiecutter.repo_name%7D%7D/%7B%7Bcookiecutter.repo_name%7D%7D/utils.py>`_ from the cookiecutter template for inspiration.

So at minimum you have to add this to your config:

.. code-block:: python

    config.include("restalchemy")
    config.set_get_model_function("yourapp.utils.get_model")

See :ref:`configuration` for more infos.

New app
-------

If you want to start a fresh project, it's best to
use cookiecutter_:

.. code-block:: bash

   $ cookiecutter gh:restalchemy/cookiecutter-restalchemy

and follow the steps show from this command.


.. _Pyramid: https://trypyramid.com
.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _cookiecutter: https://cookiecutter.readthedocs.io
