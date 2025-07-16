from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Define the database URL. For SQLite, this is the path to the database file.
# The file `sproutie.db` will be created in the root of your project folder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sproutie.db"

# Create the SQLAlchemy engine.
# The `connect_args` are needed only for SQLite to allow it to be used by
# multiple threads, which is the case with FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class. Each instance of this class will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. Our database model classes will inherit from this class.
Base = declarative_base()