import pytest
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from app.database import Base

# conftest's model imports are what populate Base.metadata; importing Base alone registers
# nothing. The suite runs on SQLite, which accepts a String with no length, so compiling
# against the MySQL dialect here is the only place a missing VARCHAR length surfaces without
# a live database.
TABLES = sorted(Base.metadata.tables.values(), key=lambda table: table.name)


@pytest.mark.parametrize("table", TABLES, ids=lambda table: table.name)
def test_every_table_compiles_against_mysql(table):
    ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))

    assert table.name in ddl
