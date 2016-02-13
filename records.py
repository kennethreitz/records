# -*- coding: utf-8 -*-

import os
from code import interact
from datetime import datetime
from collections import namedtuple, OrderedDict

import tablib
from docopt import docopt
from sqlalchemy import text, create_engine
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = os.environ.get('DATABASE_URL')


class Record(object):
    """A row, from a query, from a database."""
    __slots__ = ('_keys', '_values')
    def __init__(self, keys, values):
        self._keys = keys
        self._values = values

        # Esure that lengths match properly.
        assert len(self._keys) == len(self._values)

    def keys(self):
        """Returns the list of column names from the query."""
        return self._keys

    def values(self):
        """Returns the list of values from the query."""
        return self._values

    def __repr__(self):
        return '<Record {}>'.format(self.export('json')[1:-1])

    def __getitem__(self, key):
        # Support for index-based lookup.
        if isinstance(key, int):
            return self.values()[key]

        # Support for string-based lookup.
        if key in self.keys():
            i = self.keys().index(key)
            return self.values()[i]

        raise KeyError("Record contains no '{}' field.".format(key))

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __dir__(self):
        standard = [
            # Would love to do this programatically, but couldn't figure out how.
            '__class__', '__ddir__', '__delattr__', '__doc__', '__format__',
            '__getattr__', '__getattribute__', '__getitem__', '__hash__',
            '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__',
            '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__',
            '__subclasshook__', '_keys', '_values', 'as_dict', 'dataset',
            'export', 'get', 'keys', 'values'
        ]

        # Merge standard attrs with generated ones (from column names).
        return sorted(standard + [str(k) for k in self.keys()])

    def get(self, key, default=None):
        """Returns the value for a given key, or default."""
        try:
            return self[key]
        except KeyError:
            return default

    def as_dict(self, ordered=False):
        """Returns the row as a dictionary, as ordered."""
        items = zip(self.keys(), self.values())

        return OrderedDict(items) if ordered else dict(items)

    @property
    def dataset(self):
        """A Tablib Dataset containing the row."""
        data = tablib.Dataset()
        data.headers = self.keys()

        row = _reduce_datetimes(self.values())
        data.append(row)

        return data

    def export(self, format, **kwargs):
        """Exports the row to the given format."""
        return self.dataset.export(format, **kwargs)


class RecordCollection(object):
    """A set of excellent Records from a query."""
    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []
        self.pending = True

    def __repr__(self):
        r = '<RecordCollection size={} pending={}>'.format(len(self), self.pending)
        return r

    def __iter__(self):
        """Iterate over all rows, consuming the underlying generator
        only when necessary."""
        i = 0
        while True:
            # Other code may have iterated between yields,
            # so always check the cache.
            if i < len(self):
                yield self[i]
            else:
                # Throws StopIteration when done.
                yield next(self)
            i += 1


    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            nextrow = next(self._rows)
            self._all_rows.append(nextrow)
            return nextrow
        except StopIteration:
            self.pending = False
            raise StopIteration('RecordCollection contains no more rows.')

    def __getitem__(self, key):
        is_int = isinstance(key, int)

        # Convert RecordCollection[1] into slice.
        if is_int:
            key = slice(key, key + 1)

        while len(self) < key.stop or key.stop is None:
            try:
                next(self)
            except StopIteration:
                break

        rows = self._all_rows[key]
        if is_int:
            return rows[0]
        else:
            return RecordCollection(iter(rows))

    def __len__(self):
        return len(self._all_rows)

    def export(self, format, **kwargs):
        """Export the RecordCollection to a given format (courtesy of Tablib)."""
        return self.dataset.export(format, **kwargs)

    @property
    def dataset(self):
        """A Tablib Dataset representation of the RecordCollection."""
        # Create a new Tablib Dataset.
        data = tablib.Dataset()

        # Set the column names as headers on Tablib Dataset.
        first = self[0]

        data.headers = first.keys()
        for row in self.all():
            row = _reduce_datetimes(row.values())
            data.append(row)

        return data

    def all(self, as_dict=False, as_ordereddict=False):
        """Returns a list of all rows for the RecordCollection. If they haven't
        been fetched yet, consume the iterator and cache the results."""

        # By calling list it calls the __iter__ method
        rows = list(self)

        if as_dict:
            return [r.as_dict() for r in rows]
        elif as_ordereddict:
            return [r.as_dict(ordered=True) for r in rows]

        return rows

class Database(object):
    """A Database connection."""

    def __init__(self, db_url=None):
        # If no db_url was provided, fallback to $DATABASE_URL.
        self.db_url = db_url or DATABASE_URL

        if not self.db_url:
            raise ValueError('You must provide a db_url.')

        # Connect to the database.
        self.db = create_engine(self.db_url).connect()
        self.open = True

    def close(self):
        """Closes the connection to the Database."""
        self.db.close()
        self.open = False

    def __enter__(self):
        return self

    def __exit__(self, exc, val, traceback):
        self.close()

    def __repr__(self):
        return '<Database open={}>'.format(self.open)

    def get_table_names(self, internal=False):
        """Returns a list of table names for the connected database."""

        # Setup SQLAlchemy for Database inspection.
        metadata = declarative_base().metadata
        metadata.reflect(create_engine(self.db_url))

        # Serve the table names.
        return metadata.tables.keys()

    def query(self, query, fetchall=False, **params):
        """Executes the given SQL query against the Database. Parameters
        can, optionally, be provided. Returns a RecordCollection, which can be
        iterated over to get result rows as dictionaries.
        """

        # Execute the given query.
        cursor = self.db.execute(text(query), **params) # TODO: PARAMS GO HERE

        # Row-by-row Record generator.
        row_gen = (Record(cursor.keys(), row) for row in cursor)

        # Convert psycopg2 results to RecordCollection.
        results = RecordCollection(row_gen)

        # Fetch all results if desired.
        if fetchall:
            results.all()

        return results

    def query_file(self, path, fetchall=False, **params):
        """Like Database.query, but takes a filename to load a query from."""

        # If path doesn't exists
        if not os.path.exists(path):
            raise FileNotFoundError

        # If it's a directory
        if os.path.isdir(path):
            raise IsADirectoryError

        # Read the given .sql file into memory.
        with open(path) as f:
            query = f.read()

        # Defer processing to self.query method.
        return self.query(query=query, fetchall=fetchall, **params)

def _reduce_datetimes(row):
    """Receives a row, converts datetimes to strings."""

    row = list(row)

    for i in range(len(row)):
        if hasattr(row[i], 'isoformat'):
            row[i] = row[i].isoformat()
    return tuple(row)


def cli():
    cli_docs ="""Records: SQL for Humans™
A Kenneth Reitz project.

Usage:
  records <query> <format> [<params>...] [--url=<url>]
  records (-h | --help)

Options:
  -h --help     Show this screen.
  --url=<url>   The database URL to use. Defaults to $DATABASE_URL.

Supported Formats:
   csv, tsv, json, yaml, html, xls, xlsx, dbf, latex, ods

   Note: xls, xlsx, dbf, and ods formats are binary, and should only be
         used with redirected output e.g. '$ records sql xls > sql.xls'.

Query Parameters:
    Query parameters can be specified in key=value format, and injected
    into your query in :key format e.g.:

    $ records 'select * from repos where language ~= :lang' lang=python

Notes:
  - While you may specify a database connection string with --url, records
    will automatically default to the value of $DATABASE_URL, if available.
  - Query is intended to be the path of a SQL file, however a query string
    can be provided instead. Use this feature discernfully; it's dangerous.
  - Records is intended for report-style exports of database queries, and
    has not yet been optimized for extremely large data dumps.

Cake:
   ✨ 🍰 ✨
    """
    supported_formats = 'csv tsv json yaml html xls xlsx dbf latex ods'.split()

    # Parse the command-line arguments.
    arguments = docopt(cli_docs)
    # print arguments
    # exit()

    # Create the Database.
    db = Database(arguments['--url'])

    query = arguments['<query>']
    params = arguments['<params>']

    # Can't send an empty list if params aren't expected.
    try:
        params = dict([i.split('=') for i in params])
    except ValueError:
        print('Parameters must be given in key=value format.')
        exit(64)

    # Execute the query, if it is a found file.
    if os.path.isfile(query):
        rows = db.query_file(query, **params)

    # Execute the query, if it appears to be a query string.
    elif len(query.split()) > 2:
        rows = db.query(query, **params)

    # Otherwise, say the file wasn't found.
    else:
        print('The given query could not be found.')
        exit(66)

    # Print results in desired format.
    if arguments['<format>']:
        print(rows.export(arguments['<format>']))
    else:
        print(rows.dataset)

# Run the CLI when executed directly.
if __name__ == '__main__':
    cli()




