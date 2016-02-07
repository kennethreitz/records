Relational: Just Write SQL
==========================

Relational is a very simple, but powerful, library for making raw SQL queries
to Postgres Databases. This common task can be surprisingly difficult with the
standard tools available. This library strives to make this simple workflow
as easy and seamless as possible, while providing an elegant interface to work
with your results.

Relational also feature full Tablib integration, which allows you to export
your results to CSV, XLS, JSON, or YAML with a single line of code. Excellent
for sharing data with friends, or generating reports.

- HSTORE support, if available.
- Iterated rows are cached for future reference.
- ``$DATABASE_URL`` environment variable support.
- Convenience `Database.get_table_names` method.
- Queries can be passed as strings or filenames, parameters supported.
- Query results are iterators of standard Python dictionaries (``{'column-name': 'value'}``)

Relational is powered by `psycopg2 <https://pypi.python.org/pypi/psycopg2>`_
and `Tablib <http://docs.python-tablib.org/en/latest/>`_.
