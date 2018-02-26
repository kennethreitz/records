import pytest

import records

db = records.Database('sqlite:///:memory:')


@pytest.fixture
def table_setup(request):
    db.query('CREATE TABLE foo (a integer)')
    def drop_table():
        db.query('DROP TABLE foo')
    request.addfinalizer(drop_table)


def test_failing_transaction_self_managed(table_setup):
    conn = db.get_connection()
    tx = conn.transaction()
    try:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        raise ValueError()
        tx.commit()
        conn.query('INSERT INTO foo VALUES (44)')
    except:
        tx.rollback()
    finally:
        conn.close()
        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 0


def test_failing_transaction(table_setup):
    with db.transaction() as conn:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        raise ValueError()

    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 0


def test_passing_transaction_self_managed(table_setup):
    conn = db.get_connection()
    tx = conn.transaction()
    try:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')
        tx.commit()
    except:
        tx.rollback()
    finally:
        conn.close()
        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2


def test_passing_transaction(table_setup):
    with db.transaction() as conn:
        conn.query('INSERT INTO foo VALUES (42)')
        conn.query('INSERT INTO foo VALUES (43)')

    assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2