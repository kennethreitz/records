Relational: Just Write SQL
==========================

Relational is a very simple, but powerful, library for making raw SQL queries
to Postgres Databases. This common task can be surprisingly difficult with the
standard tools available. This library strives to make this simple workflow
as easy and seamless as possible, while providing an elegant interface to work
with your results.

.. code:: python

    import relational
    db = relational.Database('postgres://...')

    # rows = db.query('select * from active_users')
    rows = db.query_file('sqls/active-users.sql')

You can grab rows one at a time:

.. code:: python

    >>> rows.next()
    {'username': 'hansolo', 'name': 'Henry Ford', 'active': True, 'timezone': datetime.datetime(2016, 2, 6, 22, 28, 23, 894202), 'user_email': 'hansolo@gmail.com'}

Iterate over them:

.. code:: python

    for row in rows:
        spam_user(name=row['name'], email=row['user_email'])

Or fetch all results for later reference:

.. code:: python

    >>> rows.all()
    [{'username': ...}, {'username': ...}, {'username': ...}, ...]

Features
--------

- HSTORE support, if available.
- Iterated rows are cached for future reference.
- ``$DATABASE_URL`` environment variable support.
- Convenience ``Database.get_table_names`` method.
- Queries can be passed as strings or filenames, parameters supported.
- Query results are iterators of standard Python dictionaries (``{'column-name': 'value'}``)

Relational is powered by `psycopg2 <https://pypi.python.org/pypi/psycopg2>`_
and `Tablib <http://docs.python-tablib.org/en/latest/>`_.

Data Export Functionality
-------------------------

Relational also feature full Tablib integration, which allows you to export
your results to CSV, XLS, JSON, or YAML with a single line of code. Excellent
for sharing data with friends, or generating reports.

.. code:: python2

    >>> print rows.dataset
    username|active|name      |user_email       |timezone
    --------|------|----------|-----------------|--------------------------
    hansolo |True  |Henry Ford|hansolo@gmail.com|2016-02-06 22:28:23.894202
    ...

Export your query to CSV:

.. code:: python

    >>> rows.dataset.csv
    username,active,name,user_email,timezone
    hansolo,True,Henry Ford,hansolo@gmail.com,2016-02-06 22:28:23.894202
    ...

YAML:

.. code:: python

    >>> rows.dataset.yaml
    - {active: true, name: Henry Ford, timezone: '2016-02-06 22:28:23.894202', user_email: hansolo@gmail.com, username: hansolo}
    ...

JSON:

.. code:: python

    >>> rows.dataset.json
    [{"username": "hansolo", "active": true, "name": "Henry Ford", "user_email": "hansolo@gmail.com", "timezone": "2016-02-06 22:28:23.894202"}, ...]


Excel:

.. code:: python

    with open('report.xls', 'wb') as f:
        f.write(rows.dataset.xls)

You get the point. Plus all the other features of Tablib are there, so you
can add/remove columns, include seperators, query columns, and more.




