"""Create the database tables.

Run explicitly — `python -m app.init_db` from backend/ — rather than on app startup, so the
API never silently dials MySQL at import time and schema changes stay a deliberate step.

Note this creates *tables*, not the database itself. `CREATE DATABASE coffeelogs;` has to
happen first; SQLAlchemy connects to a schema, it cannot conjure one.
"""

from app import models  # noqa: F401  <- load-bearing, see below
from app.database import Base, engine

# That import is load-bearing: create_all iterates Base.metadata, which is only populated
# as a side effect of the model classes being *defined*. Without it, create_all succeeds
# and creates zero tables.


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Created tables:", ", ".join(Base.metadata.tables))


if __name__ == "__main__":
    main()
