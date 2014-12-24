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


# Reflect each database table we need to use, via schemas.
class Slugs(Base, SessionPropertyMixin):
    __table__ = Table('slugs', metadata, autoload=True)

class Apps(Base, SessionPropertyMixin):
    __table__ = Table('apps', metadata, autoload=True)

    @classmethod
    def register(cls, app, session):
        # TODO: Check for existing record first.

        existing = session.query(cls).filter_by(app=app).first()

        if existing:
            self = existing
        else:
            self = cls()

        self.session = session
        self.save()

        return self


class Extracts(Base, SessionPropertyMixin):
    __table__ = Table('extracts', metadata, autoload=True)

    @classmethod
    def register(cls, slug, session):
        # TODO: Check for existing record first.

        existing = session.query(cls).filter_by(slug=slug).first()

        if existing:
            self = existing
        else:
            self = cls()

        self.session = session
        self.slug = slug
        self.updated_at = datetime.utcnow()
        self.save()

        return self

    def mark_fail(self, failure_step, meta=None):
        self.success = False
        self.failure_step = failure_step
        self.meta = meta
        self.updated_at = datetime.utcnow()
        self.save()

    def extract_fail(self, language, stdout, stderr):
        self.success = False
        self.failure_step = 'extract'
        self.language = language

        if not self.meta:
            self.meta = {}

        self.meta['stdout'] = stdout
        self.meta['stderr'] = stderr

        self.updated_at = datetime.utcnow()

        self.save()

    def mark_success(self):
        self.success = True
        self.updated_at = datetime.utcnow()
        self.save()

    def save(self):
        self.session.add(self)
        self.session.commit()


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
