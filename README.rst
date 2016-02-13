Records: SQL for Humans™
========================

**Records is a very simple, but powerful, library for making raw SQL queries
to most relational databases.**

This common task can be surprisingly difficult with the standard tools available.
This library strives to make this workflow as simple as possible,
while providing an elegant interface to work with your query results.

*Database support includes Postgresql, MySQL, SQLite, Oracle, and MS-SQL (drivers not included).*

-------------------------------------


☤ The Basics
------------
We know how to write SQL, so let's send some to our database:

.. code:: python

    import records

    db = records.Database('postgres://...')
    rows = db.query('select * from active_users')    # or db.query_file('sqls/active-users.sql')


Grab one row at a time:

.. code:: python

    >>> rows[0]
    <Record {"username": "model-t", "active": true, "name": "Henry Ford", "user_email": "model-t@gmail.com", "timezone": "2016-02-06 22:28:23.894202"}>

Or iterate over them:

.. code:: python

    for r in rows:
        spam_user(name=r.name, email=r.user_email)

Values can be accessed many ways: ``row.user_email``, ``row['user_email']``, or ``row[3]``. Fields with non-alphanumeric charecters (like spaces) are also fully supported. 

Or store them all for later reference:

.. code:: python

    >>> rows.all()
    [<Record {"username": ...}>, <Record {"username": ...}>, <Record {"username": ...}>, ...]

If you'd prefer to have a copy of your record collection, use ``rows.as_dict()`` or ``rows.as_dict(ordered=True)``.

☤ Features
----------

- Iterated rows are cached for future reference.
- ``$DATABASE_URL`` environment variable support.
- Convenience ``Database.get_table_names`` method.
- Command-line `records` tool for exporting queries.
- Safe `parameterization <http://initd.org/psycopg/docs/usage.html>`_: ``Database.query('life=:everything', everything=42)``
- Queries can be passed as strings or filenames, parameters supported.

Records is proudly powered by `SQLAlchemy <http://www.sqlalchemy.org>`_
and `Tablib <http://docs.python-tablib.org/en/latest/>`_.

☤ Data Export Functionality
---------------------------

Records also features full Tablib integration, and allows you to export
your results to CSV, XLS, JSON, HTML Tables, or YAML with a single line of code.
Excellent for sharing data with friends, or generating reports.

.. code:: pycon

    >>> print rows.dataset
    username|active|name      |user_email       |timezone
    --------|------|----------|-----------------|--------------------------
    model-t |True  |Henry Ford|model-t@gmail.com|2016-02-06 22:28:23.894202
    ...

- Comma Seperated Values (CSV)

  .. code:: pycon

      >>> print rows.export('csv')
      username,active,name,user_email,timezone
      model-t,True,Henry Ford,model-t@gmail.com,2016-02-06 22:28:23.894202
      ...

- YAML Ain't Markup Language (YAML)

  .. code:: python

      >>> print rows.export('yaml')
      - {active: true, name: Henry Ford, timezone: '2016-02-06 22:28:23.894202', user_email: model-t@gmail.com, username: model-t}
      ...

- JavaScript Object Notation (JSON)

  .. code:: python

      >>> print rows.export('json')
      [{"username": "model-t", "active": true, "name": "Henry Ford", "user_email": "model-t@gmail.com", "timezone": "2016-02-06 22:28:23.894202"}, ...]

- Microsoft Excel (xls, xlsx)

  .. code:: python

      with open('report.xls', 'wb') as f:
          f.write(rows.export('xls'))

You get the point. All other features of Tablib are also available,
so you can sort results, add/remove columns/rows, remove duplicates,
transpose the table, add separators, slice data by column, and more.

See the `Tablib Documentation <http://docs.python-tablib.org/en/latest/>`_
for more details.

☤ Installation
--------------

Of course, the recommended installation method is pip::

    $ pip install records
    ✨🍰✨

☤ Command-Line Tool
-------------------

As an added bonus, a ``records`` command-line tool is automatically
included. Here's a screenshot of the usage information:

.. image:: https://s3.amazonaws.com/f.cl.ly/items/1M0147110J3k0p2D3z2b/records.png?v=729fd472

☤ Thank You
-----------

Thanks for checking this library out! I hope you find it useful.

Of course, there's always room for improvement. Feel free to `open an issue <https://github.com/kennethreitz/records/issues>`_ so we can make Records better, stronger, faster.


