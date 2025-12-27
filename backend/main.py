import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from contextlib import asynccontextmanager

# Import our database utilities and models
from database import get_db, init_db
from models import Question, UserStats
from platform_service import platform_service

# Import AI agent
try:
    from ai_agent import CodeMentorAgent, CodeMentorAgentLocal
    
    # Try Groq first
    if os.getenv("GROQ_API_KEY"):
        agent = CodeMentorAgent()
        AGENT_AVAILABLE = True
        print("✅ Using Groq AI Agent")
    else:
        # Fallback to local Ollama
        try:
            agent = CodeMentorAgentLocal()
            AGENT_AVAILABLE = True
            print("✅ Using Local Ollama AI Agent")
        except Exception as e:
            print(f"⚠️  No AI agent available. Set GROQ_API_KEY or install Ollama")
            AGENT_AVAILABLE = False
except Exception as e:
    print(f"⚠️  AI Agent not available: {e}")
    AGENT_AVAILABLE = False

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed (none for now)

# Initialize FastAPI app
app = FastAPI(
    title="DSA Tracker API",
    description="Track your DSA problem-solving progress across platforms",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allows frontend to make requests to backend
# In production, replace "*" with your frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models for request/response validation
class QuestionCreate(BaseModel):
    """Schema for creating a new question entry"""
    platform: str
    question_id: str
    title: str
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    notes: Optional[str] = None
    is_revision_needed: bool = False

class QuestionResponse(BaseModel):
    """Schema for question response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    platform: str
    question_id: str
    title: str
    difficulty: Optional[str]
    topic: Optional[str]
    solved_date: datetime
    notes: Optional[str]
    is_revision_needed: bool

class StatsResponse(BaseModel):
    """Schema for statistics response"""
    model_config = ConfigDict(from_attributes=True)
    
    platform: str
    easy_count: int
    medium_count: int
    hard_count: int
    total_solved: int
    last_updated: datetime


# ============= API ENDPOINTS =============

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "DSA Tracker API is running!",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.post("/questions/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new question entry.
    
    This endpoint:
    1. Receives question data
    2. Saves it to database
    3. Updates platform statistics
    """
    # Create new Question object
    db_question = Question(
        platform=question.platform,
        question_id=question.question_id,
        title=question.title,
        difficulty=question.difficulty,
        topic=question.topic,
        notes=question.notes,
        is_revision_needed=question.is_revision_needed
    )
    
    # Add to database
    db.add(db_question)
    db.commit()  # Save changes
    db.refresh(db_question)  # Get the saved object with ID
    
    # Update statistics
    update_stats(db, question.platform)
    
    return db_question

@app.get("/questions/", response_model=List[QuestionResponse])
async def get_questions(
    platform: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all questions with optional filters.
    
    Query parameters:
    - platform: Filter by platform (leetcode, codeforces)
    - difficulty: Filter by difficulty (Easy, Medium, Hard)
    - limit: Maximum number of results
    """
    query = db.query(Question)
    
    if platform:
        query = query.filter(Question.platform == platform)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    questions = query.order_by(Question.solved_date.desc()).limit(limit).all()
    return questions

@app.get("/stats/", response_model=List[StatsResponse])
async def get_stats(db: Session = Depends(get_db)):
    """
    Get statistics for all platforms.
    """
    stats = db.query(UserStats).all()
    return stats

@app.get("/stats/{platform}", response_model=StatsResponse)
async def get_platform_stats(platform: str, db: Session = Depends(get_db)):
    """
    Get statistics for a specific platform.
    """
    stats = db.query(UserStats).filter(UserStats.platform == platform).first()
    if not stats:
        raise HTTPException(status_code=404, detail=f"No stats found for platform: {platform}")
    return stats

@app.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Delete a question by ID"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    platform = question.platform
    db.delete(question)
    db.commit()
    
    # Update statistics
    update_stats(db, platform)
    
    return {"message": "Question deleted successfully"}


# ============= PLATFORM SYNC ENDPOINTS =============

@app.post("/sync/leetcode/{username}")
async def sync_leetcode(username: str, db: Session = Depends(get_db)):
    """
    Sync LeetCode data for a user.
    
    This endpoint:
    1. Fetches user stats from LeetCode
    2. Fetches recent submissions
    3. Saves new questions to database
    4. Updates statistics
    """
    try:
        # Fetch stats
        stats = await platform_service.fetch_leetcode_stats(username)
        
        # Fetch recent submissions
        submissions = await platform_service.fetch_leetcode_recent_submissions(username, limit=50)
        
        # Save submissions to database
        new_questions = 0
        for sub in submissions:
            # Check if question already exists
            existing = db.query(Question).filter(
                Question.platform == "leetcode",
                Question.question_id == sub["question_id"]
            ).first()
            
            if not existing:
                # Create new question entry with difficulty
                question = Question(
                    platform="leetcode",
                    question_id=sub["question_id"],
                    title=sub["title"],
                    difficulty=sub.get("difficulty", "Unknown"),  # Now includes difficulty!
                    solved_date=sub["solved_date"]
                )
                db.add(question)
                new_questions += 1
        
        db.commit()
        
        # Update statistics
        update_stats(db, "leetcode")
        
        return {
            "message": "LeetCode data synced successfully",
            "username": username,
            "stats": stats,
            "new_questions_added": new_questions,
            "total_submissions_fetched": len(submissions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= AI AGENT ENDPOINTS =============

class ChatRequest(BaseModel):
    """Schema for chat requests"""
    message: str

class ChatResponse(BaseModel):
    """Schema for chat responses"""
    response: str
    agent_available: bool

@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the CodeMentor AI agent.
    
    The agent can:
    - Answer questions about your progress
    - Analyze solving patterns
    - Recommend next steps
    - Provide insights
    
    Example queries:
    - "How am I doing overall?"
    - "What should I practice next?"
    - "Show my recent submissions"
    - "Analyze my weak topics"
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="AI Agent is not available. Please check ANTHROPIC_API_KEY in .env"
        )
    
    try:
        response = agent.chat(request.message)
        return ChatResponse(response=response, agent_available=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.post("/agent/clear")
async def clear_agent_memory():
    """Clear the agent's conversation memory"""
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI Agent is not available")
    
    agent.clear_memory()
    return {"message": "Agent memory cleared successfully"}


@app.post("/sync/codeforces/{username}")
async def sync_codeforces(username: str, db: Session = Depends(get_db)):
    """
    Sync Codeforces data for a user.
    
    Similar to LeetCode sync but for Codeforces.
    """
    try:
        # Fetch stats
        stats = await platform_service.fetch_codeforces_stats(username)
        
        # Fetch submissions (no limit - gets ALL submissions)
        submissions = await platform_service.fetch_codeforces_submissions(username)
        
        # Save submissions to database
        new_questions = 0
        for sub in submissions:
            # Check if question already exists
            existing = db.query(Question).filter(
                Question.platform == "codeforces",
                Question.question_id == sub["question_id"]
            ).first()
            
            if not existing:
                # Create new question entry
                question = Question(
                    platform="codeforces",
                    question_id=sub["question_id"],
                    title=sub["title"],
                    difficulty=sub["difficulty"],  # Actual rating: "1200", "1500", etc.
                    topic=sub.get("topic"),
                    solved_date=sub["solved_date"]
                )
                db.add(question)
                new_questions += 1
        
        db.commit()
        
        # Update statistics
        update_stats(db, "codeforces")
        
        return {
            "message": "Codeforces data synced successfully",
            "username": username,
            "stats": stats,
            "new_questions_added": new_questions,
            "total_submissions_fetched": len(submissions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= HELPER FUNCTIONS =============

def update_stats(db: Session, platform: str):
    """
    Update statistics for a platform by recounting questions.
    """
    # Count questions by difficulty
    easy = db.query(Question).filter(
        Question.platform == platform,
        Question.difficulty == "Easy"
    ).count()
    
    medium = db.query(Question).filter(
        Question.platform == platform,
        Question.difficulty == "Medium"
    ).count()
    
    hard = db.query(Question).filter(
        Question.platform == platform,
        Question.difficulty == "Hard"
    ).count()
    
    total = db.query(Question).filter(Question.platform == platform).count()
    
    # Get or create stats record
    stats = db.query(UserStats).filter(UserStats.platform == platform).first()
    
    if not stats:
        stats = UserStats(platform=platform)
        db.add(stats)
    
    # Update values
    stats.easy_count = easy
    stats.medium_count = medium
    stats.hard_count = hard
    stats.total_solved = total
    stats.last_updated = datetime.utcnow()
    
    db.commit()


if __name__ == "__main__":
    import uvicorn
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)