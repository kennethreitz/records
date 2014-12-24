import os
from datetime import datetime
from multiprocessing.util import register_after_fork

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


from psycopg2.extras import RealDictConnection, register_hstore

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


class Warehouse(object):
    def __init__(self, conn_str):
        self.db = RealDictConnection(conn_str)
        register_hstore(self.db)

    def query(self, q, params=None, fetchall=False):
        c = self.db.cursor()
        c.execute(q, params)

        gen = (r for r in c)

        if fetchall:
            return list(gen)
        else:
            return gen

    def query_file(self, path, params=None, fetchall=False):
        with open(path) as f:
            query = f.read()

        return self.query(query, params=params, fetchall=fetchall)
