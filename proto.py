import os
from datetime import datetime


import tablib
import psycopg2
from psycopg2.extras import register_hstore, RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

PG_TABLES_QUERY = "SELECT * FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'"
PG_INTERNAL_TABLES_QUERY = "SELECT * FROM pg_catalog.pg_tables"


def reduce_datetimes(row):
    """Receives a row, converts datetimes to strings."""
    for i in range(len(row)):
        if isinstance(row[i], datetime):
            row[i] = '{}'.format(row[i])
    return row

class ResultSet(object):
    """A set of results from a query."""
    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []
        self._completed = False

    def __repr__(self):
        return '<ResultSet {:o}>'.format(id(self))

    def __iter__(self):
        # Use cached results if available.
        if self._completed:
            for row in self._all_rows:
                yield row

        # Iterate over result cursor, cache rows.
        for row in self._rows:
            self._all_rows.append(row)
            yield row
        self._completed = True

    def next(self):
        try:
            return self._rows.next()
        except StopIteration:
            raise StopIteration("ResultSet contains no more rows.")

    @property
    def dataset(self):
        """A Tablib Dataset representation of the ResultSet."""
        # Create a new Tablib Dataset.
        data = tablib.Dataset()

        # Set the column names as headers on Tablib Dataset.
        data.headers = self.all()[0].keys()

        # Take each row, string-ify datetimes, insert into Tablib Dataset.
        for row in self.all():
            row = reduce_datetimes([v for k, v in row.items()])
            data.append(row)

        return data

    def all(self):
        """Returns a list of all rows for the ResultSet. If they haven't
        been fetched yet, consume the iterator and cache the results."""

        # If rows aren't cached, fetch them.
        if not self._all_rows:
            self._all_rows = list(self._rows)
        return self._all_rows

class Database(object):
    """A Database connection."""

    def __init__(self, db_url=None):

        # If no db_url was provided, fallback to $DATABASE_URL.
        self.db_url = db_url or DATABASE_URL

        if not self.db_url:
            raise ValueError('You must provide a db_url.')

        # Connect to the database.
        self.db = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

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
        # Read the given .sql file into memory.
        with open(path) as f:
            query = f.read()

        # Defer processing to self.query method.
        return self.query(query=query, params=params, fetchall=fetchall)
