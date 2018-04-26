import pytest


@pytest.mark.usefixtures("foo_table")
def test_issue105(db):
    assert db.query("select count(*) as n from foo").scalar() == 0
