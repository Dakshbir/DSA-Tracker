"""
Agent Tools - Functions the AI can call to interact with the database.

These are the "superpowers" we give to the AI agent.
Each tool is a function that the AI can decide to call based on user queries.
"""

from langchain.tools import tool
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Question, UserStats
from database import SessionLocal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


# ============= HELPER FUNCTION =============

def get_db_session():
    """Get a database session for tools to use"""
    return SessionLocal()


# ============= STATISTICS TOOLS =============

@tool
def get_leetcode_statistics() -> str:
    """
    Get statistics for LeetCode platform.
    
    Returns:
        JSON string with LeetCode statistics: total solved, easy, medium, hard counts
    """
    db = get_db_session()
    try:
        stats = db.query(UserStats).filter(UserStats.platform == "leetcode").first()
        
        if not stats:
            return json.dumps({"error": "No LeetCode data found. Please sync first."})
        
        result = {
            "platform": "leetcode",
            "total_solved": stats.total_solved,
            "easy_count": stats.easy_count,
            "medium_count": stats.medium_count,
            "hard_count": stats.hard_count,
            "last_updated": stats.last_updated.isoformat()
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_codeforces_statistics() -> str:
    """
    Get statistics for Codeforces platform.
    
    Returns:
        JSON string with Codeforces statistics: total solved, easy, medium, hard counts
    """
    db = get_db_session()
    try:
        stats = db.query(UserStats).filter(UserStats.platform == "codeforces").first()
        
        if not stats:
            return json.dumps({"error": "No Codeforces data found. Please sync first."})
        
        result = {
            "platform": "codeforces",
            "total_solved": stats.total_solved,
            "easy_count": stats.easy_count,
            "medium_count": stats.medium_count,
            "hard_count": stats.hard_count,
            "last_updated": stats.last_updated.isoformat()
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_all_statistics() -> str:
    """
    Get statistics for ALL platforms combined.
    
    Returns:
        JSON string with combined statistics across all platforms
    
    Example:
        get_all_statistics()
        Returns total problems solved across LeetCode, Codeforces, etc.
    """
    db = get_db_session()
    try:
        all_stats = db.query(UserStats).all()
        
        if not all_stats:
            return json.dumps({"error": "No statistics available. Please sync platforms first."})
        
        # Calculate totals
        total = sum(s.total_solved for s in all_stats)
        easy = sum(s.easy_count for s in all_stats)
        medium = sum(s.medium_count for s in all_stats)
        hard = sum(s.hard_count for s in all_stats)
        
        platforms = {
            stat.platform: {
                "total": stat.total_solved,
                "easy": stat.easy_count,
                "medium": stat.medium_count,
                "hard": stat.hard_count
            }
            for stat in all_stats
        }
        
        result = {
            "overall": {
                "total_solved": total,
                "easy_count": easy,
                "medium_count": medium,
                "hard_count": hard
            },
            "platforms": platforms
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


# ============= QUESTION QUERY TOOLS =============

@tool
def get_recent_submissions() -> str:
    """
    Get recently solved problems (last 10).
    
    Shows your 10 most recent problem submissions in chronological order.
    
    Returns:
        JSON string with list of recent problems including title, platform, difficulty, date
    """
    db = get_db_session()
    try:
        questions = db.query(Question).order_by(Question.solved_date.desc()).limit(10).all()
        
        if not questions:
            return json.dumps({"message": "No submissions found"})
        
        result = [{
            "title": q.title,
            "platform": q.platform,
            "difficulty": q.difficulty,
            "solved_date": q.solved_date.isoformat()
        } for q in questions]
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_leetcode_recent() -> str:
    """
    Get your 10 most recent LeetCode submissions.
    
    Shows the problems you've solved recently on LeetCode only.
    
    Returns:
        JSON string with recent LeetCode problems
    """
    db = get_db_session()
    try:
        questions = db.query(Question).filter(
            Question.platform == "leetcode"
        ).order_by(Question.solved_date.desc()).limit(10).all()
        
        if not questions:
            return json.dumps({"message": "No LeetCode submissions found"})
        
        result = [{
            "title": q.title,
            "difficulty": q.difficulty,
            "solved_date": q.solved_date.isoformat()
        } for q in questions]
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_codeforces_recent() -> str:
    """
    Get your 10 most recent Codeforces submissions.
    
    Shows the problems you've solved recently on Codeforces only.
    
    Returns:
        JSON string with recent Codeforces problems
    """
    db = get_db_session()
    try:
        questions = db.query(Question).filter(
            Question.platform == "codeforces"
        ).order_by(Question.solved_date.desc()).limit(10).all()
        
        if not questions:
            return json.dumps({"message": "No Codeforces submissions found"})
        
        result = [{
            "title": q.title,
            "difficulty": q.difficulty,
            "solved_date": q.solved_date.isoformat()
        } for q in questions]
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def list_all_topics() -> str:
    """
    List all topics/tags that you've solved problems for.
    
    Shows a comprehensive list of all problem topics you've encountered with counts.
    
    Returns:
        JSON string with topics and the number of problems solved in each
    """
    db = get_db_session()
    try:
        questions = db.query(Question).filter(Question.topic.isnot(None)).all()
        
        if not questions:
            return json.dumps({"message": "No topic data available"})
        
        topic_counts = {}
        for q in questions:
            if q.topic:
                topics = [t.strip() for t in q.topic.split(',')]
                for topic in topics:
                    if topic:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by count (descending)
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            "topics": [
                {"topic": topic, "problems_solved": count}
                for topic, count in sorted_topics
            ],
            "total_unique_topics": len(sorted_topics)
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


# ============= ANALYSIS TOOLS =============

@tool
def analyze_weak_topics() -> str:
    """
    Analyze which topics the user has solved the least.
    Helps identify areas needing more practice.
    
    Returns:
        JSON string with topic analysis
    
    Example:
        analyze_weak_topics()
        Returns topics you should practice more
    """
    db = get_db_session()
    try:
        # Get all questions with topics
        questions = db.query(Question).filter(Question.topic.isnot(None)).all()
        
        if not questions:
            return json.dumps({"message": "No topic data available"})
        
        # Count problems per topic
        topic_counts = {}
        for q in questions:
            if q.topic:
                # Split comma-separated topics
                topics = [t.strip() for t in q.topic.split(',')]
                for topic in topics:
                    if topic:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort by count (ascending) to find weakest
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1])
        
        # Get top 10 weakest topics
        weak_topics = sorted_topics[:10]
        
        result = {
            "weak_topics": [
                {"topic": topic, "problems_solved": count}
                for topic, count in weak_topics
            ],
            "recommendation": "Consider practicing these topics more!"
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_leetcode_difficulty_distribution() -> str:
    """
    Get difficulty distribution of your LeetCode problems.
    
    Shows how many Easy, Medium, and Hard problems you've solved on LeetCode.
    
    Returns:
        JSON string with Easy/Medium/Hard breakdown and percentages
    """
    db = get_db_session()
    try:
        questions = db.query(Question).filter(Question.platform == "leetcode").all()
        
        if not questions:
            return json.dumps({"message": "No LeetCode data available"})
        
        difficulty_counts = {}
        for q in questions:
            diff = q.difficulty or "Unknown"
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        total = len(questions)
        
        result = {
            "platform": "leetcode",
            "total_problems": total,
            "distribution": {
                diff: {
                    "count": count,
                    "percentage": round((count / total) * 100, 1)
                }
                for diff, count in sorted(difficulty_counts.items())
            }
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_codeforces_difficulty_distribution() -> str:
    """
    Get difficulty/rating distribution of your Codeforces problems.
    
    Shows how your Codeforces problems are distributed across different ratings (800, 1200, 1500, 1600, etc).
    
    Returns:
        JSON string with rating-wise breakdown and percentages
    """
    db = get_db_session()
    try:
        questions = db.query(Question).filter(Question.platform == "codeforces").all()
        
        if not questions:
            return json.dumps({"message": "No Codeforces data available"})
        
        difficulty_counts = {}
        for q in questions:
            diff = q.difficulty or "Unknown"
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        total = len(questions)
        
        result = {
            "platform": "codeforces",
            "total_problems": total,
            "distribution": {
                diff: {
                    "count": count,
                    "percentage": round((count / total) * 100, 1)
                }
                for diff, count in sorted(difficulty_counts.items())
            }
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


@tool
def get_solving_streak() -> str:
    """
    Calculate the user's current and longest solving streak.
    
    Returns:
        JSON string with streak information
    
    Example:
        get_solving_streak()
        Returns current streak and longest streak
    """
    db = get_db_session()
    try:
        questions = db.query(Question).order_by(Question.solved_date.desc()).all()
        
        if not questions:
            return json.dumps({"message": "No submissions yet"})
        
        # Get unique dates
        dates = sorted(set(q.solved_date.date() for q in questions))
        
        if not dates:
            return json.dumps({"current_streak": 0, "longest_streak": 0})
        
        # Calculate current streak
        current_streak = 1
        today = datetime.now().date()
        
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
            else:
                break
        
        # Calculate longest streak
        longest_streak = 1
        temp_streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        result = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_solved": dates[-1].isoformat(),
            "total_active_days": len(dates)
        }
        
        return json.dumps(result, indent=2)
    finally:
        db.close()


# ============= TOOL LIST =============

# Export all tools for the agent
ALL_TOOLS = [
    get_leetcode_statistics,
    get_codeforces_statistics,
    get_all_statistics,
    get_recent_submissions,
    get_leetcode_recent,
    get_codeforces_recent,
    list_all_topics,
    analyze_weak_topics,
    get_leetcode_difficulty_distribution,
    get_codeforces_difficulty_distribution,
    get_solving_streak
]