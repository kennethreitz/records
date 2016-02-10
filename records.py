# -*- coding: utf-8 -*-

import os
from datetime import datetime

import tablib
import psycopg2
from psycopg2.extras import register_hstore, NamedTupleCursor
from psycopg2.extensions import cursor as _cursor


DATABASE_URL = os.environ.get('DATABASE_URL')

PG_TABLES_QUERY = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'"
PG_INTERNAL_TABLES_QUERY = "SELECT * FROM pg_catalog.pg_tables"





class BetterNamedTupleCursor(NamedTupleCursor):
    """A cursor that generates results as `~collections.namedtuple`.

    `!fetch*()` methods will return named tuples instead of regular tuples, so
    their elements can be accessed both as regular numeric items as well as
    attributes.

        >>> nt_cur = conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        >>> rec = nt_cur.fetchone()
        >>> rec
        Record(id=1, num=100, data="abc'def")
        >>> rec[1]
        100
        >>> rec.data
        "abc'def"
    """
    try:
        from collections import namedtuple
    except ImportError, _exc:
        def _make_nt(self):
            raise self._exc
    else:
        def _make_nt(self, namedtuple=namedtuple):
            RecordBase = namedtuple("Record", [d[0] for d in self.description or ()])

            class Record(RecordBase):
                __slots__ = ()
                def keys(self):
                    return self._fields

                def __getitem__(self, key):
                    if isinstance(key, int):
                        return super(RecordBase, self).__getitem__(key)

                    if key in self.keys():
                        return getattr(self, key)

                    raise KeyError("Record contains no '{}' field.".format(key))

                @property
                def dataset(self):
                    data = tablib.Dataset()

                    data.headers = self._fields
                    row = _reduce_datetimes(self)
                    data.append(row)

                    return data

                def export(self, format, **kwargs):
                    return self.dataset.export(format, **kwargs)


                def get(self, key, default=None):
                    try:
                        return self[key]
                    except KeyError:
                        return default

            return Record








class ResultSet(object):
    """A set of results from a query."""
    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []
        self.pending = True

    def __repr__(self):
        r = '<ResultSet size={} pending={}>'.format(len(self), self.pending)

        if not self._all_rows:
            return r

        for i in range(5):
            try:
                r += '\n - {}'.format(self._all_rows[i])
            except IndexError:
                break
        more = len(self._all_rows) - i
        if more:
            r += '\n   ({} more)'.format(more)
        r += '\n</ResultSet>'

        return r

    def __iter__(self):
        """Starts by returning the cached items and then consumes the
        generator in case it is not fully consumed.
        """
        if self._all_rows:
            for row in self._all_rows:
                yield row
        try:
            while True:
                yield self.__next__()
        except StopIteration:
            pass

    def next(self):
        return self.__next__()

    def __next__(self):
        try:
            nextrow = next(self._rows)
            self._all_rows.append(nextrow)
            return nextrow
        except StopIteration:
            self.pending = False
            raise StopIteration('ResultSet contains no more rows.')

    def __getitem__(self, key):

        is_int = False

        # Convert ResultSet[1] into slice.
        if isinstance(key, int):
            is_int = True
            key = slice(key, key + 1, None)

        while len(self._all_rows) < key.stop or key.stop is None:
            try:
                next(self)
            except StopIteration:
                break

        item = self._all_rows[key]
        if not is_int:
            r = ResultSet(self._rows)
            r._all_rows = item
            item = r
        else:
            item = item[0]

        return item

    def __len__(self):
        return len(self._all_rows)

    def export(self, format, **kwargs):
        """Export the ResultSet to a given format (courtesy of Tablib)."""
        return self.dataset.export(format, **kwargs)

    @property
    def dataset(self):
        """A Tablib Dataset representation of the ResultSet."""
        # Create a new Tablib Dataset.
        data = tablib.Dataset()

        # Set the column names as headers on Tablib Dataset.
        first = self[0]

        data.headers = first._fields
        for row in self.all():
            row = _reduce_datetimes(row)
            data.append(row)

        return data


    def all(self):
        """Returns a list of all rows for the ResultSet. If they haven't
        been fetched yet, consume the iterator and cache the results."""

        # By calling list it calls the __iter__ method
        return list(self)

class Database(object):
    """A Database connection."""

    def __init__(self, db_url=None):

        # If no db_url was provided, fallback to $DATABASE_URL.
        self.db_url = db_url or DATABASE_URL

        if not self.db_url:
            raise ValueError('You must provide a db_url.')

        # Connect to the database.
        self.db = psycopg2.connect(self.db_url, cursor_factory=BetterNamedTupleCursor)

        # Enable hstore if it's available.
        self._enable_hstore()

    def _enable_hstore(self):
        try:
            register_hstore(self.db)
        except psycopg2.ProgrammingError:
            pass

    def get_table_names(self, internal=False):
        """Returns a list of table names for the connected database."""

        # Support listing internal table names as well.
        query = PG_INTERNAL_TABLES_QUERY if internal else PG_TABLES_QUERY

        # Return a list of tablenames.
        return [r['tablename'] for r in self.query(query)]

    def query(self, query, params=None, fetchall=False):
        """Executes the given SQL query against the Database. Parameters
        can, optionally, be provided. Returns a ResultSet, which can be
        iterated over to get result rows as dictionaries.
        """
        # Execute the given query.
        c = self.db.cursor()
        c.execute(query, params)

        # Row-by-row result generator.
        row_gen = (r for r in c)

        # Convert psycopg2 results to ResultSet
        results = ResultSet(row_gen)

        # Fetch all results if desired.
        if fetchall:
            results.all()

        return results

    def query_file(self, path, params=None, fetchall=False):
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
        return self.query(query=query, params=params, fetchall=fetchall)

def _reduce_datetimes(row):
    """Receives a row, converts datetimes to strings."""
    for i in range(len(row)):
        if hasattr(row[i], 'isoformat'):
            row = row._replace(**{row._fields[0]: row[i].isoformat()})
    return row
