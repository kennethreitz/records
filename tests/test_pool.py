"""Regression test for PLAN.md item 8 / ISSUE_236 Bug #4: connection pool
exhaustion.

`Database.query()`/`Database.query_file()` open connections with
`close_with_result=True`. Before the fix, `Connection.close()` skipped
`self._conn.close()` whenever `close_with_result` was `True`, relying on a
SQLAlchemy 1.x GC-driven autoclose that SQLAlchemy 2.x no longer provides --
so the underlying pooled DB-API connection was never returned to the pool.
With a small pool, a handful of `db.query()` calls would exhaust the pool and
the next call would hang/time out waiting for a free connection.
"""

from sqlalchemy.pool import QueuePool

import records


def test_query_does_not_exhaust_connection_pool(tmpdir):
    dbfile = str(tmpdir / "db.sqlite")
    db = records.Database(
        "sqlite:///{}".format(dbfile),
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=2,
    )
    try:
        db.query("CREATE TABLE foo (a integer)")
        # More calls than the pool can hold at once. Before the fix, the
        # second call here would block on `pool_timeout` and raise a
        # TimeoutError because the first call's connection was never
        # returned to the pool.
        for _ in range(5):
            db.query("SELECT * FROM foo")
    finally:
        db.close()
