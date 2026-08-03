"""Create the tables (not the database) — run explicitly: `python -m app.init_db`."""

# Load-bearing: Base.metadata is populated as a side effect of the model class definitions,
# so without this import create_all succeeds and creates zero tables.
from app import models  # noqa: F401
from app.database import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Created tables:", ", ".join(Base.metadata.tables))


if __name__ == "__main__":
    main()
