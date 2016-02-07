import os
from datetime import datetime
from multiprocessing.util import register_after_fork

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import tablib
import psycopg2
from psycopg2.extras import RealDictConnection, register_hstore, RealDictCursor, NamedTupleCursor, DictCursor
from psycopg2 import ProgrammingError
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')


Base = declarative_base()


_ENGINES = {}
_SESSIONS = {}

# https://github.com/celery/celery/blob/master/celery/backends/database/session.py#L27-L46

class _after_fork(object):
    registered = False

    def __call__(self):
        self.registered = False  # child must reregister
        for engine in list(_ENGINES.values()):
            engine.dispose()
        _ENGINES.clear()
        _SESSIONS.clear()
after_fork = _after_fork()

def get_engine(dburi, **kwargs):
    try:
        return _ENGINES[dburi]
    except KeyError:
        engine = _ENGINES[dburi] = create_engine(dburi, **kwargs)
        after_fork.registered = True
        register_after_fork(after_fork, after_fork)
        return engine


def create_session(dburi, short_lived_sessions=False, **kwargs):
    engine = get_engine(dburi, **kwargs)
    if short_lived_sessions or dburi not in _SESSIONS:
        _SESSIONS[dburi] = sessionmaker(bind=engine)
    return engine, _SESSIONS[dburi]

engine = create_engine(DATABASE_URL)
metadata = MetaData(bind=engine)

session_maker = create_session(DATABASE_URL)[1]


class SessionPropertyMixin(object):

    def save(self, session=None, commit=True, close=False):

        if session:
            session.add(self)
            session.commit()

        if close:
            session.close()

def reduce_datetimes(row):
    for i in range(len(row)):
        if isinstance(row[i], datetime):
            row[i] = '{}'.format(row[i])
    return row

class ResultSet(object):
    """A ResultSet from a query."""
    def __init__(self, rows):
        self._rows = rows
        self._all_rows = []

    def __repr__(self):
        return '<ResultSet>'

    def __iter__(self):
        if self._all_rows:
            for row in self._all_rows:
                yield row
        else:
            yield self._rows.next()

    def next(self):
        try:
            return self._rows.next()
        except StopIteration:
            raise StopIteration("ResultSet contains no more rows.")


    def _fetch_all(self):
        return list(self._rows)

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
            self._all_rows = self._fetch_all()
        return self._all_rows



class Database(object):
    """A Database connection."""

    def __init__(self, conn_str):
        self._conn_str = conn_str
        self.db = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)

        # Enable hstore if it's available.
        self._enable_hstore()


    def _enable_hstore(self):
        try:
            register_hstore(self.db)
        except ProgrammingError:
            pass

    def query(self, query, params=None, fetchall=False):
        """Executes the given SQL query against the Database. Parameters
        can, optionally, be provided. Returns a ResultSet, which can be
        iterated over to get result rows as dictionaries.
        """
        # Execute the given query.
        c = self.db.cursor()
        c.execute(query, params)

        # Row-by-row result generator.
        gen = (r for r in c)
        return ResultSet(gen)

        # If fetchall is True, return a list.
        # return list(gen) if fetchall else gen

    def query_file(self, path, params=None, fetchall=False):
        """Like Database.query, but takes a filename to load a query from."""
        # Read the given .sql file into memory.
        with open(path) as f:
            query = f.read()

        # Defer processing to self.query method.
        return self.query(query=query, params=params, fetchall=fetchall)
