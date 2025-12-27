from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# SQLite database URL - creates a file named 'dsa_tracker.db'
# For production, you might use PostgreSQL or MySQL
DATABASE_URL = "sqlite:///./dsa_tracker.db"

# Create database engine
# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# SessionLocal class - each instance is a database session
# A session is like a "workspace" for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialize the database by creating all tables.
    This reads our models.py and creates corresponding tables.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

def get_db():
    """
    Dependency function that provides a database session.
    
    This is used with FastAPI's dependency injection.
    It ensures:
    1. A session is created for each request
    2. The session is properly closed after the request
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the route
    finally:
        db.close()  # Always close the session when done