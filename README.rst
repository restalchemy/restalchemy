RESTAlchemy
===========

A REST framework build on top of Pyramid and SQLAlchemy.

.. warning::

   RESTAlchemy is early alpha and while working and in
   production in some of my own projects,
   it's not really ready for production.
   Before I tag a version, I will make breaking changes on
   a somewhat regular basis. Feedback welcome.


Intro
-----

If you use the `SQLAlchemy` ORM for your models,
you already specify the type of the column,
if it's nullable, a default value and other properties.

So instead of duplicating what you already specified
in your `SQLAlchemy` models and writing validation for your
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

Documentation
-------------

- Read the `tutorial <https://restalchemy.readthedocs.org/en/latest/tutorial.html>`_,
- Create a new project with `cookiecutter <https://github.com/restalchemy/cookiecutter-restalchemy>`_.
- Read the full `documentation online <https://restalchemy.readthedocs.org/en/latest/index.html>`_,


Support
-------

For questions and general discussion, join our
`mailing list <https://groups.google.com/forum/#!forum/restalchemy>`_.

For feature requests or bug reports open a
`GitHub issue <https://github.com/restalchemy/restalchemy/issues>`_.


Check the `website <https://www.restalchemy.org>`_ for updates.
