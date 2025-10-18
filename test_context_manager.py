#!/usr/bin/env python3
"""Test script for enhanced context manager functionality."""

import records

def test_basic_context_manager():
    """Test basic database context manager."""
    print("Testing basic context manager...")
    
    with records.Database('sqlite:///:memory:') as db:
        db.query('CREATE TABLE test (id INTEGER, name TEXT)')
        db.query("INSERT INTO test VALUES (1, 'test')")
        result = db.query('SELECT * FROM test')
        rows = list(result)
        assert len(rows) == 1
        assert rows[0].id == 1
        assert rows[0].name == 'test'
    
    print("✓ Basic context manager works correctly")

def test_transaction_context_manager():
    """Test transaction context manager."""
    print("Testing transaction context manager...")
    
    with records.Database('sqlite:///:memory:') as db:
        db.query('CREATE TABLE test (id INTEGER, name TEXT)')
        
        # Test successful transaction
        try:
            with db.transaction() as conn:
                conn.query("INSERT INTO test VALUES (1, 'test1')")
                conn.query("INSERT INTO test VALUES (2, 'test2')")
            
            result = db.query('SELECT COUNT(*) as count FROM test')
            count = result.first().count
            assert count == 2
            print("✓ Transaction committed successfully")
            
        except Exception as e:
            print(f"Transaction failed: {e}")
            raise

def test_auto_cleanup():
    """Test automatic resource cleanup."""
    print("Testing automatic resource cleanup...")
    
    # Create and destroy database to test cleanup
    db = records.Database('sqlite:///:memory:')
    assert db.open == True
    
    db.close()
    assert db.open == False
    
    print("✓ Automatic cleanup works correctly")

if __name__ == "__main__":
    try:
        test_basic_context_manager()
        test_transaction_context_manager() 
        test_auto_cleanup()
        print("\n🎉 All context manager tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise