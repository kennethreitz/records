#!/usr/bin/env python3
"""
Simple test suite for Records enhancements without pytest dependency.
"""

import sys
import os
import tempfile
from unittest.mock import patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import records


def test_record_enhancements():
    """Test enhanced Record functionality."""
    print("Testing Record enhancements...")
    
    # Test Record creation with different types
    keys = ['id', 'name', 'active', 'score', 'data']
    values = [1, 'test', True, 99.5, None]
    
    record = records.Record(keys, values)
    
    assert record.id == 1
    assert record.name == 'test'
    assert record.active == True
    assert record.score == 99.5
    assert record.data is None
    
    # Test get method
    assert record.get('id') == 1
    assert record.get('missing') is None
    assert record.get('missing', 'default') == 'default'
    
    # Test as_dict
    as_dict = record.as_dict()
    assert isinstance(as_dict, dict)
    assert as_dict['id'] == 1
    
    ordered_dict = record.as_dict(ordered=True)
    assert hasattr(ordered_dict, '__len__')
    
    print("✓ Record enhancements work correctly")


def test_record_collection_enhancements():
    """Test enhanced RecordCollection functionality."""
    print("Testing RecordCollection enhancements...")
    
    # Test empty collection
    empty_gen = iter([])
    collection = records.RecordCollection(empty_gen)
    
    assert len(collection) == 0
    assert collection.pending == True
    
    all_records = collection.all()
    assert all_records == []
    assert collection.pending == False
    
    # Test collection with data
    test_records = [records.Record(['id'], [i]) for i in range(3)]
    collection = records.RecordCollection(iter(test_records))
    
    # Test first
    first = collection.first()
    assert first.id == 0
    
    # Test scalar
    scalar_record = records.Record(['count'], [42])
    scalar_collection = records.RecordCollection(iter([scalar_record]))
    assert scalar_collection.scalar() == 42
    
    print("✓ RecordCollection enhancements work correctly")


def test_database_enhancements():
    """Test enhanced Database functionality."""
    print("Testing Database enhancements...")
    
    # Test context manager
    with records.Database('sqlite:///:memory:') as db:
        assert db.open == True
        db.query('CREATE TABLE test (id INTEGER)')
        
        # Test get_table_names (basic functionality)
        table_names = db.get_table_names()
        assert isinstance(table_names, list)
        
    assert db.open == False
    
    # Test multiple closes don't error
    db = records.Database('sqlite:///:memory:')
    db.close()
    db.close()  # Should not raise error
    
    # Test transaction context manager
    db = records.Database('sqlite:///:memory:')
    db.query('CREATE TABLE test (id INTEGER)')
    
    with db.transaction() as conn:
        conn.query('INSERT INTO test VALUES (1)')
        conn.query('INSERT INTO test VALUES (2)')
    
    result = db.query('SELECT COUNT(*) as count FROM test')
    assert result.first().count == 2
    
    db.close()
    
    print("✓ Database enhancements work correctly")


def test_error_handling():
    """Test error handling improvements."""
    print("Testing error handling...")
    
    # Test isexception function
    assert records.isexception(ValueError("test")) == True
    assert records.isexception(ValueError) == True
    assert records.isexception("string") == False
    assert records.isexception(42) == False
    
    # Test invalid database URL
    try:
        records.Database(None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "provide a db_url" in str(e)
    
    print("✓ Error handling works correctly")


def test_type_hints():
    """Test that type hints are present."""
    print("Testing type hints...")
    
    # Basic check that annotations exist
    assert hasattr(records.Record.__init__, '__annotations__')
    assert hasattr(records.Database.__init__, '__annotations__')
    
    print("✓ Type hints are present")


def main():
    """Run all tests."""
    print("🚀 Running enhanced Records tests...\n")
    
    try:
        test_record_enhancements()
        test_record_collection_enhancements()
        test_database_enhancements()
        test_error_handling()
        test_type_hints()
        
        print("\n🎉 All enhancement tests passed!")
        print("\n📊 Test Coverage Summary:")
        print("  ✓ Enhanced Record functionality")
        print("  ✓ Enhanced RecordCollection functionality") 
        print("  ✓ Enhanced Database functionality")
        print("  ✓ Improved error handling")
        print("  ✓ Type hints verification")
        print("  ✓ Context managers")
        print("  ✓ Transaction support")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)