from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Base class for all our models
Base = declarative_base()

class Question(Base):
    """
    Model representing a DSA question solved by the user.
    
    This is like a blueprint for our database table.
    Each attribute becomes a column in the database.
    """
    __tablename__ = "questions"  # Name of the table in database
    
    # Primary key - unique identifier for each question
    id = Column(Integer, primary_key=True, index=True)
    
    # Question details
    platform = Column(String, nullable=False)  # "leetcode" or "codeforces"
    question_id = Column(String, nullable=False)  # Platform-specific ID
    title = Column(String, nullable=False)
    difficulty = Column(String)  # LeetCode: "Easy"/"Medium"/"Hard", Codeforces: "800"/"1200"/etc
    topic = Column(String)  # "Arrays", "Dynamic Programming", etc.
    
    # Metadata
    solved_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)  # User's notes about the solution
    is_revision_needed = Column(Boolean, default=False)
    
    def __repr__(self):
        """String representation of the Question object"""
        return f"<Question(title='{self.title}', platform='{self.platform}', difficulty='{self.difficulty}')>"


class UserStats(Base):
    """
    Model to store aggregated statistics.
    This helps us quickly retrieve stats without recalculating each time.
    """
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, unique=True, nullable=False)
    
    # Counts by difficulty
    easy_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    hard_count = Column(Integer, default=0)
    
    # Total questions
    total_solved = Column(Integer, default=0)
    
    # Last updated timestamp
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserStats(platform='{self.platform}', total={self.total_solved})>"