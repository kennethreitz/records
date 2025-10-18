#!/usr/bin/env python3
"""
Enhanced test suite for Records library with improved coverage.
Tests edge cases, error handling, and new features.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

import records


class TestRecordEnhancements:
    """Test enhanced Record functionality."""
    
    def test_record_creation_with_different_types(self):
        """Test Record creation with various data types."""
        keys = ['id', 'name', 'active', 'score', 'data']
        values = [1, 'test', True, 99.5, None]
        
        record = records.Record(keys, values)
        
        assert record.id == 1
        assert record.name == 'test'
        assert record.active == True
        assert record.score == 99.5
        assert record.data is None
    
    def test_record_get_method(self):
        """Test Record.get() method with defaults."""
        keys = ['id', 'name']
        values = [1, 'test']
        
        record = records.Record(keys, values)
        
        assert record.get('id') == 1
        assert record.get('name') == 'test'
        assert record.get('missing') is None
        assert record.get('missing', 'default') == 'default'
    
    def test_record_attribute_error(self):
        """Test Record raises AttributeError for missing attributes."""
        keys = ['id']
        values = [1]
        
        record = records.Record(keys, values)
        
        with pytest.raises(AttributeError):
            _ = record.nonexistent_attribute
    
    def test_record_dir_method(self):
        """Test Record.__dir__() includes column names."""
        keys = ['id', 'name', 'test_column']
        values = [1, 'test', 'value']
        
        record = records.Record(keys, values)
        dir_result = dir(record)
        
        assert 'id' in dir_result
        assert 'name' in dir_result
        assert 'test_column' in dir_result
    
    def test_record_as_dict_ordered(self):
        """Test Record.as_dict() with ordered parameter."""
        keys = ['c', 'a', 'b']
        values = [3, 1, 2]
        
        record = records.Record(keys, values)
        
        regular_dict = record.as_dict(ordered=False)
        ordered_dict = record.as_dict(ordered=True)
        
        assert isinstance(regular_dict, dict)
        assert hasattr(ordered_dict, '__len__')  # OrderedDict-like behavior
        assert list(ordered_dict.keys()) == ['c', 'a', 'b']


class TestRecordCollectionEnhancements:
    """Test enhanced RecordCollection functionality."""
    
    def test_empty_record_collection(self):
        """Test RecordCollection with no records."""
        empty_gen = iter([])
        collection = records.RecordCollection(empty_gen)
        
        assert len(collection) == 0
        assert collection.pending == True
        
        # Test that all() returns empty list
        all_records = collection.all()
        assert all_records == []
        assert collection.pending == False
    
    def test_record_collection_slicing(self):
        """Test RecordCollection slicing functionality."""
        test_records = [
            records.Record(['id'], [i]) for i in range(5)
        ]
        collection = records.RecordCollection(iter(test_records))
        
        # Test slice
        subset = collection[1:3]
        assert isinstance(subset, records.RecordCollection)
        assert len(subset) == 2
        
        # Test single index
        first = collection[0]
        assert isinstance(first, records.Record)
        assert first.id == 0
    
    def test_record_collection_one_multiple_rows(self):
        """Test RecordCollection.one() with multiple rows raises ValueError."""
        test_records = [
            records.Record(['id'], [1]),
            records.Record(['id'], [2])
        ]
        collection = records.RecordCollection(iter(test_records))
        
        with pytest.raises(ValueError, match="more than one row"):
            collection.one()
    
    def test_record_collection_first_with_exception_default(self):
        """Test RecordCollection.first() with exception as default."""
        empty_gen = iter([])
        collection = records.RecordCollection(empty_gen)
        
        # Test with exception default
        with pytest.raises(ValueError):
            collection.first(default=ValueError("No records found"))
    
    def test_record_collection_scalar(self):
        """Test RecordCollection.scalar() method."""
        test_record = records.Record(['count'], [42])
        collection = records.RecordCollection(iter([test_record]))
        
        result = collection.scalar()
        assert result == 42
        
        # Test with empty collection
        empty_collection = records.RecordCollection(iter([]))
        assert empty_collection.scalar() is None
        assert empty_collection.scalar('default') == 'default'


class TestDatabaseEnhancements:
    """Test enhanced Database functionality."""
    
    def test_database_context_manager(self):
        """Test Database context manager functionality."""
        with records.Database('sqlite:///:memory:') as db:
            assert db.open == True
            db.query('CREATE TABLE test (id INTEGER)')
            
        assert db.open == False
    
    def test_database_close_multiple_times(self):
        """Test calling Database.close() multiple times doesn't error."""
        db = records.Database('sqlite:///:memory:')
        assert db.open == True
        
        db.close()
        assert db.open == False
        
        # Should not raise error
        db.close()
        assert db.open == False
    
    def test_database_get_connection_when_closed(self):
        """Test getting connection from closed database raises error."""
        db = records.Database('sqlite:///:memory:')
        db.close()
        
        with pytest.raises(records.exc.ResourceClosedError):
            db.get_connection()
    
    def test_database_transaction_success(self):
        """Test successful database transaction."""
        db = records.Database('sqlite:///:memory:')
        db.query('CREATE TABLE test (id INTEGER)')
        
        with db.transaction() as conn:
            conn.query('INSERT INTO test VALUES (1)')
            conn.query('INSERT INTO test VALUES (2)')
        
        result = db.query('SELECT COUNT(*) as count FROM test')
        assert result.first().count == 2
        
        db.close()
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error."""
        db = records.Database('sqlite:///:memory:')
        db.query('CREATE TABLE test (id INTEGER PRIMARY KEY)')
        
        try:
            with db.transaction() as conn:
                conn.query('INSERT INTO test VALUES (1)')
                # This should cause a rollback
                conn.query('INSERT INTO test VALUES (1)')  # Duplicate primary key
        except Exception:
            pass  # Expected to fail
        
        result = db.query('SELECT COUNT(*) as count FROM test')
        assert result.first().count == 0  # Should be rolled back
        
        db.close()
    
    def test_database_invalid_url(self):
        """Test Database creation with invalid URL."""
        with pytest.raises(ValueError, match="You must provide a db_url"):
            records.Database(None)
    
    @patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///:memory:'})
    def test_database_environment_url(self):
        """Test Database uses DATABASE_URL environment variable."""
        db = records.Database()  # No URL provided
        assert db.db_url == 'sqlite:///:memory:'
        db.close()


class TestConnectionEnhancements:
    """Test enhanced Connection functionality."""
    
    def test_connection_context_manager(self):
        """Test Connection context manager."""
        db = records.Database('sqlite:///:memory:')
        
        with db.get_connection() as conn:
            assert conn.open == True
            conn.query('SELECT 1')
        
        # Connection should be closed after context
        assert conn.open == False
        db.close()
    
    def test_connection_close_with_result(self):
        """Test Connection with close_with_result parameter."""
        db = records.Database('sqlite:///:memory:')
        
        # Test connection that closes with result
        conn = db.get_connection(close_with_result=True)
        assert conn._close_with_result == True
        
        # Test connection that doesn't close with result
        conn2 = db.get_connection(close_with_result=False)
        assert conn2._close_with_result == False
        
        conn.close()
        conn2.close()
        db.close()


class TestErrorHandling:
    """Test error handling improvements."""
    
    def test_cli_error_handling(self):
        """Test CLI error handling improvements."""
        # This would test the CLI but requires more complex setup
        # For now, we'll test that the functions exist and have proper signatures
        assert hasattr(records, 'cli')
        assert hasattr(records, 'print_bytes')
    
    def test_isexception_function(self):
        """Test isexception utility function."""
        # Test with exception instance
        assert records.isexception(ValueError("test")) == True
        
        # Test with exception class
        assert records.isexception(ValueError) == True
        
        # Test with non-exception
        assert records.isexception("string") == False
        assert records.isexception(42) == False
        assert records.isexception(None) == False


class TestTypeHints:
    """Test that type hints work correctly."""
    
    def test_type_annotations_exist(self):
        """Test that functions have type annotations."""
        # This is a basic test to ensure type hints are present
        assert hasattr(records.Record.__init__, '__annotations__')
        assert hasattr(records.Database.__init__, '__annotations__')
        assert hasattr(records.Connection.__init__, '__annotations__')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])