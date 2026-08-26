Unreleased
==========

- Fixed silent data loss under SQLAlchemy 2.x: ``Database.query()``,
  ``Database.bulk_query()``, and ``Database.bulk_query_file()`` now commit
  writes made outside of an explicit ``Database.transaction()`` block, instead
  of relying on SQLAlchemy 1.x implicit-autocommit behavior that 2.x removed.
- Fixed a ``TypeError`` raised by ``Database.bulk_query()`` /
  ``Database.bulk_query_file()`` under SQLAlchemy 1.4+/2.x, caused by
  unpacking multiple parameter dicts as separate positional arguments to
  ``Connection.execute()`` instead of passing them as a single list.
- Fixed connection pool exhaustion: connections opened by ``Database.query()``
  / ``Database.query_file()`` (via ``close_with_result=True``) are now always
  returned to the pool, instead of relying on a SQLAlchemy 1.x GC-driven
  autoclose mechanism that 2.x no longer provides.
- Minimum supported SQLAlchemy version is now effectively 1.4 (``future=True``
  engines) through 2.x; pre-1.4 autocommit-style engines are unsupported,
  matching ``setup.py``'s existing ``SQLAlchemy>=2.0`` pin.
- ``Database.query()`` / ``Database.query_file()`` now always fully
  materialize their result set before returning, regardless of the
  ``fetchall`` argument, so the underlying connection can be returned to the
  pool immediately. Lazy/streaming iteration of large result sets is no
  longer available through ``Database.query(..., fetchall=False)`` — callers
  who need it must use ``conn = db.get_connection()`` /
  ``conn.query(..., fetchall=False)`` directly and manage ``conn.close()``
  themselves.
- ``Database.transaction()`` now re-raises the original exception after
  rolling back, instead of silently swallowing it. Callers relying on the
  previous silent-failure behavior will now see exceptions propagate.

v0.6.0 (04-29-2024)
===================

- Support for Python 3.6+ only.
- Support for SQLAlchemy 2+.
- Dropped support for Python 2.7 and 3.4, with the move to SQLAlchemy 2+.

v0.5.1 (09-01-2017)
===================

- Depend on ``tablib[pandas]``.
- Support for Bulk quies: ``Database.bulk_query()`` & ``Database.bulk_query_file()``.

v0.5.0 (11-15-2016)
===================

- Support for transactions: ``t = Database.transaction(); t.commit()``


v0.4.3 (02-16-2016)
===================

- The cake is a lie.

v0.4.2 (02-15-2016)
===================

- Packaging fix.

v0.4.1 (02-15-2016)
===================

- Bugfix for Python 3.

v0.4.0 (02-13-2016)
===================

- Refactored to be fully powered by SQLAlchemy!
- Support for all major databases (thanks, SQLAlchemy!).
- Support for non-alphanumeric column names.
- New ``Record`` class, for representing/accessing result rows.
- ``ResultSet`` renamed ``RecordCollection``.
- Removed Interactive Mode from the CLI.


v0.3.0 (02-11-2016)
===================

- New ``record`` command-line tool available!
- Various improvements.

v0.2.0 (02-10-2016)
===================

- Results are now represented as `Record`, a namedtuples class with dict-like qualities.
- New `ResultSet.export` method, for exporting to various formats.
- Slicing a `ResultSet` now works, and results in a new `ResultSet`.
- Lots of bugfixes and improvements!

v0.1.0 (02-07-2016)
===================

- Initial release.
