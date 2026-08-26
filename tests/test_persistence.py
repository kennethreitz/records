"""Tests for persistence-across-reopen behavior (see PLAN.md, ISSUE_236_ANALYSIS.md).

These use the `sqlite_file_db` fixture (tests/conftest.py) rather than the
sqlite_memory-only `db` fixture, because in-memory sqlite state disappears on
close regardless of commit behavior -- it can't distinguish "committed" from
"never committed", which is exactly what these bugs hinge on.
"""


def test_sqlite_file_fixture_persists_across_reopen(sqlite_file_db):
    """Fixture-only sanity check for PLAN.md item 1: data committed through
    an explicit transaction on one `Database` instance must still be visible
    after that instance is closed and a new `Database` is opened on the same
    file. Uses `db.transaction()` (which already calls `tx.commit()`
    explicitly) rather than `db.query()`, so this test exercises the fixture
    itself and doesn't depend on the auto-commit fixes (PLAN.md items 4/5)
    that `db.query()` still needs.
    """
    db1 = sqlite_file_db()
    with db1.transaction() as conn:
        conn.query("CREATE TABLE foo (a integer)")
    db1.close()

    db2 = sqlite_file_db()
    assert "foo" in db2.get_table_names()


def test_query_persists_across_reopen(sqlite_file_db):
    """Regression test for PLAN.md item 4 / ISSUE_236 Bug #1: `db.query()`
    must commit writes made outside of an explicit transaction. Before the
    fix, `Connection.query()` never called `self._conn.commit()`, so under
    SQLAlchemy 2.x the INSERT was silently rolled back once the connection
    closed, and the row would be missing after reopening the database.
    """
    db1 = sqlite_file_db()
    db1.query("CREATE TABLE foo (a integer)")
    db1.query("INSERT INTO foo VALUES (42)")
    db1.close()

    db2 = sqlite_file_db()
    rows = db2.query("SELECT * FROM foo").all()
    assert [row.a for row in rows] == [42]


def test_bulk_query_persists_across_reopen(sqlite_file_db):
    """Regression test for PLAN.md item 5 / ISSUE_236 Bug #2:
    `db.bulk_query()` must commit writes made outside of an explicit
    transaction. Before the fix, `Connection.bulk_query()` never called
    `self._conn.commit()`, so under SQLAlchemy 2.x the INSERTs were silently
    rolled back once the connection closed, and the rows would be missing
    after reopening the database.
    """
    db1 = sqlite_file_db()
    db1.query("CREATE TABLE foo (a integer)")
    db1.bulk_query("INSERT INTO foo VALUES (:a)", {"a": 1}, {"a": 2})
    db1.close()

    db2 = sqlite_file_db()
    rows = db2.query("SELECT * FROM foo ORDER BY a").all()
    assert [row.a for row in rows] == [1, 2]


def test_bulk_query_file_persists_across_reopen(sqlite_file_db, tmpdir):
    """Regression test: `Connection.bulk_query_file()` duplicated
    `Connection.bulk_query()`'s `execute()` call instead of delegating to it,
    so it never picked up the PLAN.md item 5 / ISSUE_236 Bug #2 commit fix.
    Before the fix, INSERTs made via `db.bulk_query_file()` outside of an
    explicit transaction were silently rolled back once the connection
    closed, identical to Bug #2 but on the bulk-query-file code path.
    """
    sqlfile = str(tmpdir / "insert.sql")
    with open(sqlfile, "w") as f:
        f.write("INSERT INTO foo VALUES (:a)")

    db1 = sqlite_file_db()
    db1.query("CREATE TABLE foo (a integer)")
    db1.bulk_query_file(sqlfile, {"a": 1}, {"a": 2})
    db1.close()

    db2 = sqlite_file_db()
    rows = db2.query("SELECT * FROM foo ORDER BY a").all()
    assert [row.a for row in rows] == [1, 2]
