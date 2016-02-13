from collections import namedtuple

import records


IdRecord = namedtuple('IdRecord', 'id')

def check_id(i, row):
    assert row.id == i

class TestRecordCollection:
    def test_iter(self):
        rows = records.RecordCollection(IdRecord(i) for i in range(10))
        for i, row in enumerate(rows):
            check_id(i, row)

    def test_next(self):
        rows = records.RecordCollection(IdRecord(i) for i in range(10))
        for i in range(10):
            check_id(i, next(rows))

    def test_iter_and_next(self):
        rows = records.RecordCollection(IdRecord(i) for i in range(10))
        i = enumerate(iter(rows))
        check_id(*next(i))  # Cache first row.
        next(rows)  # Cache second row.
        check_id(*next(i))  # Read second row from cache.

    def test_multiple_iter(self):
        rows = records.RecordCollection(IdRecord(i) for i in range(10))
        i = enumerate(iter(rows))
        j = enumerate(iter(rows))

        check_id(*next(i))  # Cache first row.

        check_id(*next(j))  # Read first row from cache.
        check_id(*next(j))  # Cache second row.

        check_id(*next(i))  # Read second row from cache.

    def test_slice_iter(self):
        rows = records.RecordCollection(IdRecord(i) for i in range(10))
        for i, row in enumerate(rows[:5]):
            check_id(i, row)
        for i, row in enumerate(rows):
            check_id(i, row)
        assert len(rows) == 10
