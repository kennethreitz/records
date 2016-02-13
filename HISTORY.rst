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