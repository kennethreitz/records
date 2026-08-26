"""Regression test for PLAN.md item 2 / ISSUE_236_ANALYSIS.md Bug #2.

`Connection.bulk_query()` used to call
`self._conn.execute(text(query), *multiparams)`, unpacking each params dict
as a separate positional argument. SQLAlchemy 1.4+/2.x's
`Connection.execute(statement, parameters=None)` only accepts a single
`parameters` argument (a dict, or a list of dicts for an executemany), so
this raised a `TypeError` any time `bulk_query` was called.
"""

def test_bulk_query_does_not_raise_typeerror(db):
    conn = db.get_connection()
    try:
        conn.query("CREATE TABLE foo (a integer)")

        conn.bulk_query("INSERT INTO foo (a) VALUES (:a)", {"a": 1}, {"a": 2})

        rows = conn.query("SELECT a FROM foo ORDER BY a")
        assert [row.a for row in rows] == [1, 2]
    finally:
        conn.close()
