Records: SQL for Humans™
========================

Records is a very simple, but powerful, library for making raw SQL queries
to Postgres databases.

This common task can be surprisingly difficult with the standard tools available.
This library strives to make this workflow as simple as possible,
while providing an elegant interface to work with your query results.

We know how to write SQL, so let's send some to our database:

.. code:: python

    import records

    db = records.Database('postgres://...')
    rows = db.query('select * from active_users')    # or db.query_file('sqls/active-users.sql')

☤ The Basics
------------

Rows are represented as standard Python dictionaries: ``{'column-name': 'value'}``.

Grab one row at a time:

.. code:: python

    >>> rows.next()
    {'username': 'model-t', 'name': 'Harrison Ford', 'active': True, 'timezone': datetime.datetime(2016, 2, 6, 22, 28, 23, 894202), 'user_email': 'model-t@gmail.com'}

Or iterate over them:

.. code:: python

    for row in rows:
        spam_user(name=row['name'], email=row['user_email'])

Or store them all for later reference:

.. code:: python

    >>> rows.all()
    [{'username': ...}, {'username': ...}, {'username': ...}, ...]

☤ Features
----------

- HSTORE support, if available.
- Iterated rows are cached for future reference.
- ``$DATABASE_URL`` environment variable support.
- Convenience ``Database.get_table_names`` method.
- Safe `parameterization <http://initd.org/psycopg/docs/usage.html>`_: ``Database.query('life=%s', params=('42',))``
- Queries can be passed as strings or filenames, parameters supported.
- Query results are iterators of standard Python dictionaries: ``{'column-name': 'value'}``

Records is proudly powered by `Psycopg2 <https://pypi.python.org/pypi/psycopg2>`_
and `Tablib <http://docs.python-tablib.org/en/latest/>`_.

☤ Data Export Functionality
---------------------------

Records also features full Tablib integration, and allows you to export
your results to CSV, XLS, JSON, HTML Tables, or YAML with a single line of code.
Excellent for sharing data with friends, or generating reports.

.. code:: pycon

    >>> print rows.dataset
    username|active|name         |user_email       |timezone
    --------|------|-------------|-----------------|--------------------------
    model-t |True  |Harrison Ford|model-t@gmail.com|2016-02-06 22:28:23.894202
    ...

- Comma Seperated Values (CSV)

  .. code:: pycon

      >>> print rows.dataset.csv
      username,active,name,user_email,timezone
      model-t,True,Harrison Ford,model-t@gmail.com,2016-02-06 22:28:23.894202
      ...

- YAML Ain't Markup Language (YAML)

  .. code:: python

      >>> print rows.dataset.yaml
      - {active: true, name: Harrison Ford, timezone: '2016-02-06 22:28:23.894202', user_email: model-t@gmail.com, username: model-t}
      ...

- JavaScript Object Notation (JSON)

  .. code:: python

      >>> print rows.dataset.json
      [{"username": "model-t", "active": true, "name": "Harrison Ford", "user_email": "model-t@gmail.com", "timezone": "2016-02-06 22:28:23.894202"}, ...]

- Microsoft Excel (xls, xlsx)

  .. code:: python

      with open('report.xls', 'wb') as f:
          f.write(rows.dataset.xls)

You get the point. Of course, all other features of Tablib are also
available, so you can sort results, add/remove columns/rows, remove
duplicates, transpose the table, add separators, slice data by column,
and more.

See the `Tablib Documentation <http://docs.python-tablib.org/en/latest/>`_
for more details.

☤ Installation
--------------

Of course, the recommended installation method is pip::

    $ pip install records
    ✨🍰✨

☤ Thank You
-----------

Thanks for checking this library out! I hope you find it useful.

Of course, there's always room for improvement. Feel free to `open an issue <https://github.com/kennethreitz/records/issues>`_ so we can make Records better, stronger, faster.
