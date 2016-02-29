import pytest

import records

db = records.Database('sqlite:///:memory:')

db.query('CREATE TABLE foo (a integer)')

def test_failing_transaction():
    tx = db.transaction()
    try:
        db.query('INSERT INTO foo VALUES (42)')
        db.query('INSERT INTO foo VALUES (43)')
        raise ValueError()
        tx.commit()
        db.query('INSERT INTO foo VALUES (44)')
    except:
        tx.rollback()
    finally:
        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 0

def test_passing_transaction():
    tx = db.transaction()
    try:
        db.query('INSERT INTO foo VALUES (42)')
        db.query('INSERT INTO foo VALUES (43)')
        tx.commit()
    except:
        tx.rollback()
    finally:
        assert db.query('SELECT count(*) AS n FROM foo')[0].n == 2
