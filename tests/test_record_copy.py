import copy
import pickle

import pytest

import records


@pytest.mark.parametrize('copier', [copy.copy, copy.deepcopy, lambda row: pickle.loads(pickle.dumps(row))])
def test_record_can_be_copied(copier):
    original = records.Record(['id', 'items'], [1, ['value']])
    restored = copier(original)
    assert restored is not original
    assert restored.keys() == original.keys()
    assert restored.values() == original.values()
    assert restored.id == 1
    assert restored['items'] == ['value']


def test_shallow_and_deep_copy_semantics():
    original = records.Record(['items'], [['value']])
    assert copy.copy(original).values()[0] is original.values()[0]
    assert copy.deepcopy(original).values()[0] is not original.values()[0]


def test_uninitialized_record_has_no_state_attributes():
    row = records.Record.__new__(records.Record)
    for name in ('_keys', '_values', '__setstate__', 'missing'):
        with pytest.raises(AttributeError):
            getattr(row, name)


def test_missing_column_still_raises_attribute_error():
    row = records.Record(['id'], [1])
    with pytest.raises(AttributeError):
        row.missing
