"""Shared pytest fixtures.

"""

import pytest

import records


@pytest.fixture(
    params=[
        # request: (sql_url_id, sql_url_template)
        ("sqlite_memory", "sqlite:///:memory:"),
        # ('sqlite_file', 'sqlite:///{dbfile}'),
        # ('psql', 'postgresql://records:records@localhost/records')
    ],
    ids=lambda r: r[0],
)
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
def sqlite_file_db(tmpdir):
    """Factory for file-backed `records.Database` instances that all point at
    the same temporary sqlite file.

    Unlike the `db` fixture (currently sqlite_memory only, see PLAN.md item
    1), this lets a test open a database, write, close it, and reopen a
    *new* `Database` pointed at the same file to assert data survived. Not
    yet folded into `db`'s parametrization: several existing tests rely on
    `db.query()`/`db.transaction()` write paths that don't reliably persist
    across separate connections/closes on a real file until PLAN.md items
    2-8 land; parametrizing the shared `db` fixture before then would break
    them.

    Returns a callable; each call opens (and registers for teardown) a new
    `Database` against the same file.
    """
    dbfile = str(tmpdir / "db.sqlite")
    url = "sqlite:///{}".format(dbfile)
    opened = []

    def open_db():
        database = records.Database(url)
        opened.append(database)
        return database

    yield open_db

    for database in opened:
        if database.open:
            database.close()


@pytest.fixture
def foo_table(db):
    """Database with table `foo` created

    tear_down drops the table.

    Typically applied by `@pytest.mark.usefixtures('foo_table')`
    """
    db.query("CREATE TABLE foo (a integer)")
    yield
    db.query("DROP TABLE foo")
