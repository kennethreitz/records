"""Test manipulating database table in various transaction scenarios.

Varying conditions:

- db for different database backends (see `db` fixture)
- query run via

    - `db=records.Database(); db.query()
    - `conn=db.get_connection(); conn.query()`

- transaction
    - not used at all
    - used and created in different ways
    - transaction succeeds
    - transaction fails or raise
"""
import pytest

@pytest.mark.usefixtures('foo_table')
def test_plain_db(db):
    """Manipulate database by `db.query` without transactions.
    """
    db.query('INSERT INTO foo VALUES (42)')
    db.query('INSERT INTO foo VALUES (43)')
    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2
    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_plain_conn(db):
    """Manipulate database by `conn.query` without transactions.
    """
    conn = db.get_connection()
    conn.query('INSERT INTO foo VALUES (42)')
    conn.query('INSERT INTO foo VALUES (43)')
    assert conn.query('SELECT count(*) AS n FROM foo')[0].n == 2
    assert_db_connection_count(db, 1)

    # Explictly close the connection.
    conn.close()
    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_plain_conn_context_manager(db):
    """Manipulate database by `conn.query` without transactions.
    """
    with db.get_connection() as conn:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        assert conn.query('SELECT count(*) AS n FROM foo')[0].n == 2

    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_failing_transaction_self_managed(db):
    conn = db.get_connection()
    tx = conn.transaction()
    try:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        raise ValueError()
        tx.commit()
        conn.query('INSERT INTO foo VALUES (44)')
    except ValueError:
        tx.rollback()
    finally:
        conn.close()
        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 0

    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_failing_transaction(db):
    with db.transaction() as conn:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        raise ValueError()

    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 0
    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_passing_transaction_self_managed(db):
    conn = db.get_connection()
    tx = conn.transaction()
    conn.query('INSERT INTO foo VALUES (42)')
    conn.query('INSERT INTO foo VALUES (43)')
    tx.commit()
    conn.close()
    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2
    assert_db_connection_count(db, 0)


@pytest.mark.usefixtures('foo_table')
def test_passing_transaction(db):
    with db.transaction() as conn:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')

    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2
    assert_db_connection_count(db, 0)


def assert_db_connection_count(db, expected_count):
    if db.dialect != 'sqlite':
        assert db.checkedout == expected_count
