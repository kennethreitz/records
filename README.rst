Relational: Just Write SQL
==========================

Relational is a very simple, but powerful, library for making raw SQL queries
to Postgres Databases. 

This common task can be surprisingly difficult with the standard tools available. 
This library strives to make this workflow as easy and seamless as possible, 
while providing an elegant interface to work with your query results.

We know how to write SQL, so let's send some to our database:

.. code:: python

    import relational
    
    db = relational.Database('postgres://...')
    rows = db.query('select * from active_users')    # or db.query_file('sqls/active-users.sql')

Rows are represented as standard Python dictionaries (``{'column-name': 'value'}``). Grab one row at a time:

.. code:: python

    >>> rows.next()
    {'username': 'hansolo', 'name': 'Henry Ford', 'active': True, 'timezone': datetime.datetime(2016, 2, 6, 22, 28, 23, 894202), 'user_email': 'hansolo@gmail.com'}

Or iterate over them:

.. code:: python

    for row in rows:
        spam_user(name=row['name'], email=row['user_email'])

Or store them all for later reference:

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

Relational also features full Tablib integration, and allows you to export
your results to CSV, XLS, JSON, or YAML with a single line of code. Excellent
for sharing data with friends, or generating reports.

.. code:: python2

    >>> print rows.dataset
    username|active|name      |user_email       |timezone
    --------|------|----------|-----------------|--------------------------
    hansolo |True  |Henry Ford|hansolo@gmail.com|2016-02-06 22:28:23.894202
    ...

Export your query to CSV:

.. code:: python2

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

You get the point. Of course, all other features of Tablib are also 
available, so you can add/remove columns/rows, include seperators, 
select data by column, and more.

See the `Tablib Documentation <http://docs.python-tablib.org/en/latest/>`_ 
for more details. 

Installation
------------

Of course, the recommended installation method is pip::

    $ pip install records


Thank You
---------

Thanks for checking this library out! I hope you find it useful. 

Of course, there's always room for improvement too. Feel free to `open an issue <https://github.com/kennethreitz/records/issues>`_ so we can make it even better.
