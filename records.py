# -*- coding: utf-8 -*-

import os
import sys
from sys import stdout
from collections import OrderedDict
from contextlib import contextmanager
from inspect import isclass
from typing import Any, Dict, Generator, Iterator, List, Optional, Union, Tuple, TYPE_CHECKING

import tablib
from docopt import docopt
from sqlalchemy import create_engine, exc, inspect, text

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine, Connection as SQLConnection


def isexception(obj: Any) -> bool:
    """Given an object, return a boolean indicating whether it is an instance
    or subclass of :py:class:`Exception`.
    """
    if isinstance(obj, Exception):
        return True
    if isclass(obj) and issubclass(obj, Exception):
        return True
    return False


class Record(object):
    """A row, from a query, from a database."""

    __slots__ = ("_keys", "_values")

    def __init__(self, keys: List[str], values: List[Any]) -> None:
        self._keys = keys
        self._values = values

        # Ensure that lengths match properly.
        assert len(self._keys) == len(self._values)

    def keys(self) -> List[str]:
        """Returns the list of column names from the query."""
        return self._keys

    def values(self) -> List[Any]:
        """Returns the list of values from the query."""
        return self._values

    def __repr__(self) -> str:
        return "<Record {}>".format(self.export("json")[1:-1])

    def __getitem__(self, key: Union[int, str]) -> Any:
        # Support for index-based lookup.
        if isinstance(key, int):
            return self.values()[key]

        # Support for string-based lookup.
        usekeys = self.keys()
        if hasattr(
            usekeys, "_keys"
        ):  # sqlalchemy 2.x uses (result.RMKeyView which has wrapped _keys as list)
            usekeys = usekeys._keys
        if key in usekeys:
            i = usekeys.index(key)
            if usekeys.count(key) > 1:
                raise KeyError("Record contains multiple '{}' fields.".format(key))
            return self.values()[i]

        raise KeyError("Record contains no '{}' field.".format(key))

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(e)

    def __dir__(self) -> List[str]:
        standard = dir(super(Record, self))
        # Merge standard attrs with generated ones (from column names).
        return sorted(standard + [str(k) for k in self.keys()])

    def get(self, key: Union[int, str], default: Any = None) -> Any:
        """Returns the value for a given key, or default."""
        try:
            return self[key]
        except KeyError:
            return default

    def as_dict(self, ordered: bool = False) -> Union[Dict[str, Any], OrderedDict]:
        """Returns the row as a dictionary, as ordered."""
        items = zip(self.keys(), self.values())

        return OrderedDict(items) if ordered else dict(items)

    @property
    def dataset(self) -> tablib.Dataset:
        """A Tablib Dataset containing the row."""
        data = tablib.Dataset()
        data.headers = self.keys()

        row = _reduce_datetimes(self.values())
        data.append(row)

        return data

    def export(self, format: str, **kwargs) -> Union[str, bytes]:
        """Exports the row to the given format."""
        return self.dataset.export(format, **kwargs)


class RecordCollection(object):
    """A set of excellent Records from a query."""

    def __init__(self, rows: Iterator[Record]) -> None:
        self._rows = rows
        self._all_rows: List[Record] = []
        self.pending = True

    def __repr__(self) -> str:
        return "<RecordCollection size={} pending={}>".format(len(self), self.pending)

    def __iter__(self) -> Iterator[Record]:
        """Iterate over all rows, consuming the underlying generator
        only when necessary."""
        i = 0
        while True:
            # Other code may have iterated between yields,
            # so always check the cache.
            if i < len(self):
                yield self[i]
            else:
                # Throws StopIteration when done.
                # Prevent StopIteration bubbling from generator, following https://www.python.org/dev/peps/pep-0479/
                try:
                    yield next(self)
                except StopIteration:
                    return
            i += 1

    def next(self) -> Record:
        return self.__next__()

    def __next__(self) -> Record:
        try:
            nextrow = next(self._rows)
            self._all_rows.append(nextrow)
            return nextrow
        except StopIteration:
            self.pending = False
            raise StopIteration("RecordCollection contains no more rows.")

    def __getitem__(self, key: Union[int, slice]) -> Union[Record, 'RecordCollection']:
        is_int = isinstance(key, int)

        # Convert RecordCollection[1] into slice.
        if is_int:
            key = slice(key, key + 1)

        while key.stop is None or len(self) < key.stop:
            try:
                next(self)
            except StopIteration:
                break

        rows = self._all_rows[key]
        if is_int:
            return rows[0]
        else:
            return RecordCollection(iter(rows))

    def __len__(self) -> int:
        return len(self._all_rows)

    def export(self, format: str, **kwargs) -> Union[str, bytes]:
        """Export the RecordCollection to a given format (courtesy of Tablib)."""
        return self.dataset.export(format, **kwargs)

    @property
    def dataset(self):
        """A Tablib Dataset representation of the RecordCollection."""
        # Create a new Tablib Dataset.
        data = tablib.Dataset()

        # If the RecordCollection is empty, just return the empty set
        # Check number of rows by typecasting to list
        if len(list(self)) == 0:
            return data

        # Set the column names as headers on Tablib Dataset.
        first = self[0]

        data.headers = first.keys()
        for row in self.all():
            row = _reduce_datetimes(row.values())
            data.append(row)

        return data

    def all(self, as_dict=False, as_ordereddict=False):
        """Returns a list of all rows for the RecordCollection. If they haven't
        been fetched yet, consume the iterator and cache the results."""

        # By calling list it calls the __iter__ method
        rows = list(self)

        if as_dict:
            return [r.as_dict() for r in rows]
        elif as_ordereddict:
            return [r.as_dict(ordered=True) for r in rows]

        return rows

    def as_dict(self, ordered=False):
        return self.all(as_dict=not (ordered), as_ordereddict=ordered)

    def first(self, default=None, as_dict=False, as_ordereddict=False):
        """Returns a single record for the RecordCollection, or `default`. If
        `default` is an instance or subclass of Exception, then raise it
        instead of returning it."""

        # Try to get a record, or return/raise default.
        try:
            record = self[0]
        except IndexError:
            if isexception(default):
                raise default
            return default

        # Cast and return.
        if as_dict:
            return record.as_dict()
        elif as_ordereddict:
            return record.as_dict(ordered=True)
        else:
            return record

    def one(self, default=None, as_dict=False, as_ordereddict=False):
        """Returns a single record for the RecordCollection, ensuring that it
        is the only record, or returns `default`. If `default` is an instance
        or subclass of Exception, then raise it instead of returning it."""

        # Ensure that we don't have more than one row.
        try:
            self[1]
        except IndexError:
            return self.first(
                default=default, as_dict=as_dict, as_ordereddict=as_ordereddict
            )
        else:
            raise ValueError(
                "RecordCollection contained more than one row. "
                "Expects only one row when using "
                "RecordCollection.one"
            )

    def scalar(self, default: Any = None) -> Any:
        """Returns the first column of the first row, or `default`."""
        row = self.one()
        return row[0] if row else default


class Database(object):
    """A Database. Encapsulates a url and an SQLAlchemy engine with a pool of
    connections.
    """

    def __init__(self, db_url: Optional[str] = None, **kwargs) -> None:
        # If no db_url was provided, fallback to $DATABASE_URL.
        self.db_url = db_url or os.environ.get("DATABASE_URL")

        if not self.db_url:
            raise ValueError("You must provide a db_url.")

        # Create an engine.
        self._engine: 'Engine' = create_engine(self.db_url, **kwargs)
        self.open = True

    def get_engine(self) -> 'Engine':
        # Return the engine if open
        if not self.open:
            raise exc.ResourceClosedError("Database closed.")
        return self._engine

    def close(self) -> None:
        """Closes the Database and disposes of all connections."""
        if self.open:
            try:
                self._engine.dispose()
            except Exception:
                # Ignore errors during close to avoid masking original exceptions
                pass
            finally:
                self.open = False

    def __enter__(self) -> 'Database':
        return self

    def __exit__(self, exc: Any, val: Any, traceback: Any) -> None:
        self.close()

    def __del__(self) -> None:
        """Ensure database connections are closed when object is garbage collected."""
        if hasattr(self, 'open') and self.open:
            self.close()

    def __repr__(self) -> str:
        return "<Database open={}>".format(self.open)

    def get_table_names(self, internal: bool = False, **kwargs) -> List[str]:
        """Returns a list of table names for the connected database."""

        # Setup SQLAlchemy for Database inspection.
        return inspect(self._engine).get_table_names(**kwargs)

    def get_connection(self, close_with_result: bool = False) -> 'Connection':
        """Get a connection to this Database. Connections are retrieved from a
        pool.
        """
        if not self.open:
            raise exc.ResourceClosedError("Database closed.")

        return Connection(self._engine.connect(), close_with_result=close_with_result)

    @contextmanager
    def transaction(self) -> Generator['Connection', None, None]:
        """Create a database transaction context manager that automatically
        commits on success or rolls back on error.
        
        Usage:
            with db.transaction() as conn:
                conn.query("INSERT INTO table VALUES (?)", value=123)
                # Transaction is automatically committed here
        """
        if not self.open:
            raise exc.ResourceClosedError("Database closed.")
            
        conn = self._engine.connect()
        trans = conn.begin()
        
        try:
            wrapped_conn = Connection(conn, close_with_result=True)
            yield wrapped_conn
            trans.commit()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()

    def query(self, query: str, fetchall: bool = False, **params) -> RecordCollection:
        """Executes the given SQL query against the Database. Parameters can,
        optionally, be provided. Returns a RecordCollection, which can be
        iterated over to get result rows as dictionaries.
        """
        with self.get_connection(True) as conn:
            return conn.query(query, fetchall, **params)

    def bulk_query(self, query, *multiparams):
        """Bulk insert or update."""

        with self.get_connection() as conn:
            conn.bulk_query(query, *multiparams)

    def query_file(self, path, fetchall=False, **params):
        """Like Database.query, but takes a filename to load a query from."""

        with self.get_connection(True) as conn:
            return conn.query_file(path, fetchall, **params)

    def bulk_query_file(self, path, *multiparams):
        """Like Database.bulk_query, but takes a filename to load a query from."""

        with self.get_connection() as conn:
            conn.bulk_query_file(path, *multiparams)

    @contextmanager
    def transaction(self):
        """A context manager for executing a transaction on this Database."""

        conn = self.get_connection()
        tx = conn.transaction()
        try:
            yield conn
            tx.commit()
        except:
            tx.rollback()
        finally:
            conn.close()


class Connection(object):
    """A Database connection."""

    def __init__(self, connection: 'SQLConnection', close_with_result: bool = False) -> None:
        self._conn = connection
        self.open = not connection.closed
        self._close_with_result = close_with_result

    def close(self) -> None:
        # No need to close if this connection is used for a single result.
        # The connection will close when the results are all consumed or GCed.
        if not self._close_with_result and self.open:
            try:
                self._conn.close()
            except Exception:
                # Ignore errors during close to avoid masking original exceptions
                pass
        self.open = False

    def __enter__(self) -> 'Connection':
        return self

    def __exit__(self, exc: Any, val: Any, traceback: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return "<Connection open={}>".format(self.open)
    
    def __del__(self) -> None:
        """Ensure connection is closed when object is garbage collected."""
        if self.open:
            self.close()

    def query(self, query, fetchall=False, **params):
        """Executes the given SQL query against the connected Database.
        Parameters can, optionally, be provided. Returns a RecordCollection,
        which can be iterated over to get result rows as dictionaries.
        """

        # Execute the given query.
        cursor = self._conn.execute(
            text(query).bindparams(**params)
        )  # TODO: PARAMS GO HERE

        # Row-by-row Record generator.
        row_gen = iter(Record([], []))

        if cursor.returns_rows:
            row_gen = (Record(cursor.keys(), row) for row in cursor)

        # Convert psycopg2 results to RecordCollection.
        results = RecordCollection(row_gen)

        # Fetch all results if desired.
        if fetchall:
            results.all()

        return results

    def bulk_query(self, query, *multiparams):
        """Bulk insert or update."""

        self._conn.execute(text(query), *multiparams)

    def query_file(self, path, fetchall=False, **params):
        """Like Connection.query, but takes a filename to load a query from."""

        # If path doesn't exists
        if not os.path.exists(path):
            raise IOError("File '{}' not found!".format(path))

        # If it's a directory
        if os.path.isdir(path):
            raise IOError("'{}' is a directory!".format(path))

        # Read the given .sql file into memory.
        with open(path) as f:
            query = f.read()

        # Defer processing to self.query method.
        return self.query(query=query, fetchall=fetchall, **params)

    def bulk_query_file(self, path, *multiparams):
        """Like Connection.bulk_query, but takes a filename to load a query
        from.
        """

        # If path doesn't exists
        if not os.path.exists(path):
            raise IOError("File '{}'' not found!".format(path))

        # If it's a directory
        if os.path.isdir(path):
            raise IOError("'{}' is a directory!".format(path))

        # Read the given .sql file into memory.
        with open(path) as f:
            query = f.read()

        self._conn.execute(text(query), *multiparams)

    def transaction(self):
        """Returns a transaction object. Call ``commit`` or ``rollback``
        on the returned object as appropriate."""

        return self._conn.begin()


def _reduce_datetimes(row: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Receives a row, converts datetimes to strings."""

    row_list = list(row)

    for i, element in enumerate(row_list):
        if hasattr(element, "isoformat"):
            row_list[i] = element.isoformat()
    return tuple(row_list)


def cli() -> None:
    supported_formats = "csv tsv json yaml html xls xlsx dbf latex ods".split()
    formats_lst = ", ".join(supported_formats)
    cli_docs = """Records: SQL for Humans™
A Kenneth Reitz project.

Usage:
  records <query> [<format>] [<params>...] [--url=<url>]
  records (-h | --help)

Options:
  -h --help     Show this screen.
  --url=<url>   The database URL to use. Defaults to $DATABASE_URL.

Supported Formats:
   %(formats_lst)s

   Note: xls, xlsx, dbf, and ods formats are binary, and should only be
         used with redirected output e.g. '$ records sql xls > sql.xls'.

Query Parameters:
    Query parameters can be specified in key=value format, and injected
    into your query in :key format e.g.:

    $ records 'select * from repos where language ~= :lang' lang=python

Notes:
  - While you may specify a database connection string with --url, records
    will automatically default to the value of $DATABASE_URL, if available.
  - Query is intended to be the path of a SQL file, however a query string
    can be provided instead. Use this feature discernfully; it's dangerous.
  - Records is intended for report-style exports of database queries, and
    has not yet been optimized for extremely large data dumps.
    """ % dict(
        formats_lst=formats_lst
    )

    # Parse the command-line arguments.
    arguments = docopt(cli_docs)

    query = arguments["<query>"]
    params = arguments["<params>"]
    format = arguments.get("<format>")
    if format and "=" in format:
        del arguments["<format>"]
        arguments["<params>"].append(format)
        format = None
    if format and format not in supported_formats:
        print(f"Error: '{format}' format not supported.", file=sys.stderr)
        print(f"Supported formats are: {formats_lst}", file=sys.stderr)
        sys.exit(62)

    # Can't send an empty list if params aren't expected.
    try:
        params = dict([i.split("=") for i in params])
    except ValueError:
        print("Error: Parameters must be given in key=value format.", file=sys.stderr)
        print("Example: records 'SELECT * FROM table WHERE id=:id' id=123", file=sys.stderr)
        sys.exit(64)

    # Be ready to fail on missing packages
    try:
        # Create the Database.
        db = Database(arguments["--url"])

        # Execute the query, if it is a found file.
        if os.path.isfile(query):
            rows = db.query_file(query, **params)

        # Execute the query, if it appears to be a query string.
        elif len(query.split()) > 2:
            rows = db.query(query, **params)

        # Otherwise, say the file wasn't found.
        else:
            print(f"Error: The given query file '{query}' could not be found.", file=sys.stderr)
            print("Please provide either a valid SQL file path or a SQL query string.", file=sys.stderr)
            sys.exit(66)

        # Print results in desired format.
        if format:
            content = rows.export(format)
            if isinstance(content, bytes):
                print_bytes(content)
            else:
                print(content)
        else:
            print(rows.dataset)
    except ImportError as impexc:
        print(f"Import Error: {impexc.msg}", file=sys.stderr)
        print("The specified database or format requires a package that is missing.", file=sys.stderr)
        print("Please install the required dependencies. For example:", file=sys.stderr)
        print("  pip install records[pg]  # for PostgreSQL support", file=sys.stderr)
        print("  pip install records[pandas]  # for DataFrame support", file=sys.stderr)
        sys.exit(60)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def print_bytes(content: bytes) -> None:
    try:
        stdout.buffer.write(content)
    except AttributeError:
        stdout.write(content)


# Run the CLI when executed directly.
if __name__ == "__main__":
    cli()
