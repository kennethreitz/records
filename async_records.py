"""
Async support for Records library using SQLAlchemy's async capabilities.
This module provides asynchronous database operations for improved performance
in modern web applications.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, Iterator, List, Optional, Union, AsyncIterator, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy import text
import tablib

from records import Record, RecordCollection, _reduce_datetimes


class AsyncRecord(Record):
    """Async version of Record with the same interface."""
    # Inherits all functionality from Record as it's just data
    pass


class AsyncRecordCollection:
    """An async version of RecordCollection for handling query results."""
    
    def __init__(self, rows: AsyncIterator[AsyncRecord]) -> None:
        self._rows = rows
        self._all_rows: List[AsyncRecord] = []
        self.pending = True
    
    def __repr__(self) -> str:
        return f"<AsyncRecordCollection size={len(self._all_rows)} pending={self.pending}>"
    
    async def __aiter__(self) -> AsyncIterator[AsyncRecord]:
        """Async iteration over all rows."""
        i = 0
        while True:
            if i < len(self._all_rows):
                yield self._all_rows[i]
            else:
                try:
                    yield await self.__anext__()
                except StopAsyncIteration:
                    return
            i += 1
    
    async def __anext__(self) -> AsyncRecord:
        try:
            nextrow = await self._rows.__anext__()
            self._all_rows.append(nextrow)
            return nextrow
        except StopAsyncIteration:
            self.pending = False
            raise StopAsyncIteration("AsyncRecordCollection contains no more rows.")
    
    def __len__(self) -> int:
        return len(self._all_rows)
    
    async def all(self, as_dict: bool = False, as_ordereddict: bool = False) -> List[Union[AsyncRecord, Dict[str, Any]]]:
        """Fetch all remaining rows and return as a list."""
        async for row in self:
            pass  # This will consume all remaining rows
        
        rows = self._all_rows
        if as_dict:
            return [r.as_dict() for r in rows]
        elif as_ordereddict:
            return [r.as_dict(ordered=True) for r in rows]
        
        return rows
    
    async def first(self, default: Any = None, as_dict: bool = False, as_ordereddict: bool = False) -> Any:
        """Returns the first record, or default if no records exist."""
        try:
            if len(self._all_rows) == 0:
                await self.__anext__()
            record = self._all_rows[0]
        except (IndexError, StopAsyncIteration):
            from records import isexception
            if isexception(default):
                raise default
            return default
        
        if as_dict:
            return record.as_dict()
        elif as_ordereddict:
            return record.as_dict(ordered=True)
        else:
            return record
    
    async def one(self, default: Any = None, as_dict: bool = False, as_ordereddict: bool = False) -> Any:
        """Returns exactly one record, or raises ValueError if more than one exists."""
        # Fetch at least 2 rows to check for multiple results
        rows_fetched = 0
        async for _ in self:
            rows_fetched += 1
            if rows_fetched >= 2:
                break
        
        if len(self._all_rows) > 1:
            raise ValueError(
                "AsyncRecordCollection contained more than one row. "
                "Expects only one row when using AsyncRecordCollection.one"
            )
        
        return await self.first(default=default, as_dict=as_dict, as_ordereddict=as_ordereddict)
    
    async def scalar(self, default: Any = None) -> Any:
        """Returns the first column of the first row, or default."""
        row = await self.one()
        return row[0] if row else default
    
    @property
    async def dataset(self) -> tablib.Dataset:
        """A Tablib Dataset representation of the AsyncRecordCollection."""
        data = tablib.Dataset()
        
        all_rows = await self.all()
        if len(all_rows) == 0:
            return data
        
        data.headers = all_rows[0].keys()
        for row in all_rows:
            row_data = _reduce_datetimes(row.values())
            data.append(row_data)
        
        return data
    
    async def export(self, format: str, **kwargs) -> Union[str, bytes]:
        """Export the AsyncRecordCollection to a given format."""
        dataset = await self.dataset
        return dataset.export(format, **kwargs)


class AsyncConnection:
    """Async database connection wrapper."""
    
    def __init__(self, connection: AsyncConnection, close_with_result: bool = False) -> None:
        self._conn = connection
        self.open = not connection.closed
        self._close_with_result = close_with_result
    
    async def close(self) -> None:
        """Close the async connection."""
        if not self._close_with_result and self.open:
            try:
                await self._conn.close()
            except Exception:
                pass
        self.open = False
    
    async def __aenter__(self) -> 'AsyncConnection':
        return self
    
    async def __aexit__(self, exc: Any, val: Any, traceback: Any) -> None:
        await self.close()
    
    def __repr__(self) -> str:
        return f"<AsyncConnection open={self.open}>"
    
    async def query(self, query: str, fetchall: bool = False, **params) -> AsyncRecordCollection:
        """Execute an async SQL query."""
        if not self.open:
            raise RuntimeError("Connection is closed")
        
        # Execute the query
        result = await self._conn.execute(text(query).bindparams(**params))
        
        # Create async generator for rows
        async def row_generator() -> AsyncIterator[AsyncRecord]:
            if result.returns_rows:
                async for row in result:
                    yield AsyncRecord(list(result.keys()), list(row))
        
        # Create AsyncRecordCollection
        collection = AsyncRecordCollection(row_generator())
        
        # Fetch all results if requested
        if fetchall:
            await collection.all()
        
        return collection


class AsyncDatabase:
    """Async version of Database class."""
    
    def __init__(self, db_url: Optional[str] = None, **kwargs) -> None:
        import os
        # If no db_url was provided, fallback to $DATABASE_URL
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        
        if not self.db_url:
            raise ValueError("You must provide a db_url.")
        
        # Convert sync URL to async URL if needed
        if not self.db_url.startswith(('postgresql+asyncpg://', 'sqlite+aiosqlite://', 'mysql+asyncmy://')):
            # Simple URL conversion for common cases
            if self.db_url.startswith('postgresql://'):
                self.db_url = self.db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif self.db_url.startswith('sqlite:///'):
                self.db_url = self.db_url.replace('sqlite:///', 'sqlite+aiosqlite:///', 1)
            elif self.db_url.startswith('mysql://'):
                self.db_url = self.db_url.replace('mysql://', 'mysql+asyncmy://', 1)
        
        # Create async engine
        self._engine: AsyncEngine = create_async_engine(self.db_url, **kwargs)
        self.open = True
    
    def get_engine(self) -> AsyncEngine:
        """Get the async engine."""
        if not self.open:
            raise RuntimeError("Database closed.")
        return self._engine
    
    async def close(self) -> None:
        """Close the async database."""
        if self.open:
            try:
                await self._engine.dispose()
            except Exception:
                pass
            finally:
                self.open = False
    
    async def __aenter__(self) -> 'AsyncDatabase':
        return self
    
    async def __aexit__(self, exc: Any, val: Any, traceback: Any) -> None:
        await self.close()
    
    def __repr__(self) -> str:
        return f"<AsyncDatabase open={self.open}>"
    
    async def get_connection(self, close_with_result: bool = False) -> AsyncConnection:
        """Get an async connection."""
        if not self.open:
            raise RuntimeError("Database closed.")
        
        conn = await self._engine.connect()
        return AsyncConnection(conn, close_with_result=close_with_result)
    
    async def query(self, query: str, fetchall: bool = False, **params) -> AsyncRecordCollection:
        """Execute an async query."""
        async with self.get_connection(True) as conn:
            return await conn.query(query, fetchall, **params)
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncConnection, None]:
        """Create an async transaction context manager."""
        if not self.open:
            raise RuntimeError("Database closed.")
        
        conn = await self._engine.connect()
        trans = await conn.begin()
        
        try:
            wrapped_conn = AsyncConnection(conn, close_with_result=True)
            yield wrapped_conn
            await trans.commit()
        except Exception:
            await trans.rollback()
            raise
        finally:
            await conn.close()
    
    async def get_table_names(self, **kwargs) -> List[str]:
        """Get table names asynchronously."""
        async with self.get_connection() as conn:
            # This is a simplified version - in practice you'd use async inspection
            result = await conn.query("SELECT name FROM sqlite_master WHERE type='table'", fetchall=True)
            return [row.name for row in await result.all()]