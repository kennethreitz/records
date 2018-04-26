"""Shared pytest fixtures.

"""
import pytest

import records


@pytest.fixture(params=[
    # request: (sql_url_id, sql_url_template)

    ('sqlite_memory', 'sqlite:///:memory:'),
    ('sqlite_file', 'sqlite:///{dbfile}'),
    # ('psql', 'postgresql://records:records@localhost/records')
],
    ids=lambda r: r[0])
def db(request, tmpdir):
    """Instance of `records.Database(dburl)`

    Ensure, it gets closed after being used in a test or fixture.

    Parametrized with (sql_url_id, sql_url_template) tuple.
    If `sql_url_template` contains `{dbfile}` it is replaced with path to a
    temporary file.

    Feel free to parametrize for other databases and experiment with them.
    """
    id, url = request.param
    # replace {dbfile} in url with temporary db file path
    url = url.format(dbfile=str(tmpdir / "db.sqlite"))
    db = records.Database(url)
    yield db  # providing fixture value for a test case
    # tear_down
    db.close()


@pytest.fixture
def foo_table(db):
    """Database with table `foo` created

    tear_down drops the table.

    Typically applied by `@pytest.mark.usefixtures('foo_table')`
    """
    db.query('CREATE TABLE foo (a integer)')
    yield
    db.query('DROP TABLE foo')
