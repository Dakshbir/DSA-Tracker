# 🎯 DSA Tracker - AI-Powered Coding Progress Tracker

A full-stack application that syncs your LeetCode and Codeforces problems, tracks your progress, and uses AI to provide personalized insights and recommendations.

## ✨ Features

- **Multi-Platform Sync**: Automatically fetch all your solved problems from LeetCode and Codeforces
- **AI Agent Chat**: Ask CodeMentor AI questions about your progress, weak areas, and recommendations
- **Analytics Dashboard**: Beautiful visualizations of your problem-solving journey
- **Rating Distribution**: See your Codeforces rating breakdown
- **Smart Insights**: AI analyzes your patterns and suggests next steps

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database management
- **Groq** - Free LLM for AI agent
- **Selenium** - Web scraping (for future enhancements)
- **httpx** - Async HTTP client

### Frontend
- **React** - UI framework
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Lucide Icons** - Beautiful icons

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- A free Groq API key from https://console.groq.com/

### Backend Setup

1. **Clone and navigate**:
```bash
git clone https://github.com/Dakshbir/DSA-Tracker.git
cd DSA-Tracker/backend
```

2. **Create virtual environment**:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=your_key_here
```

5. **Run backend**:
```bash
python main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend**:
```bash
cd ../frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run frontend**:
```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

## 📖 Usage

### 1. Sync Your Profiles
- Open the frontend
- Enter your **LeetCode username** and click "Sync Data"
- Enter your **Codeforces username** and click "Sync Data"

The app will fetch all your solved problems and update the database.

### 2. View Your Progress
- **Platform-wise Progress**: Bar chart showing Easy/Medium/Hard breakdown
- **Codeforces Rating**: Distribution of problems by rating (800, 1200, 1600, etc.)
- **Statistics**: Total problems, Easy count, Medium count, Hard count

### 3. Chat with AI Agent
- Click the **"💬 Ask CodeMentor"** button
- Ask questions like:
  - "How many problems have I solved?"
  - "What should I practice next?"
  - "Show my recent submissions"
  - "What are my weak areas?"

The AI will analyze your data and provide personalized insights!

## 📊 Database Schema

```
Question
├── id (Primary Key)
├── platform (leetcode/codeforces)
├── question_id (unique per platform)
├── title
├── difficulty (Easy/Medium/Hard for LC, rating for CF)
├── topic
├── solved_date
└── notes

UserStats
├── platform
├── easy_count
├── medium_count
├── hard_count
├── total_solved
└── last_updated
```

## 🤖 AI Agent Architecture

The app uses a **ReAct Agent** (Reasoning + Acting) pattern:

1. **You ask a question** → AI reads it + system prompt
2. **AI reasons** → Which tools do I need?
3. **AI acts** → Calls tools to fetch data from database
4. **AI synthesizes** → Combines data with your question
5. **You get insight** → Personalized answer with analysis

### Available Tools
- `get_leetcode_statistics()` - LeetCode stats
- `get_codeforces_statistics()` - Codeforces stats
- `get_all_statistics()` - Combined stats
- `get_recent_submissions()` - Last N problems
- `search_questions_by_topic()` - Find by topic
- `analyze_weak_topics()` - Topics to practice
- `get_solving_streak()` - Current/longest streak

## 🔧 API Endpoints

### Sync Endpoints
- `POST /sync/leetcode/{username}` - Sync LeetCode data
- `POST /sync/codeforces/{username}` - Sync Codeforces data

### Query Endpoints
- `GET /questions/` - Get all problems
- `GET /stats/` - Get all statistics
- `GET /stats/{platform}` - Get platform stats

### AI Agent Endpoints
- `POST /agent/chat` - Chat with AI
- `POST /agent/clear` - Clear conversation memory

## 📈 Learning Outcomes

This project teaches:
- Full-stack development (FastAPI + React)
- Database design and ORM usage
- API integration (LeetCode GraphQL, Codeforces REST)
- Web scraping with Selenium
- AI agent architecture (ReAct pattern)
- LLM integration and prompt engineering
- Async/await patterns
- Real-time frontend updates

## 🚀 Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Persistent conversation history
- [ ] Community leaderboards
- [ ] Gamification (badges, levels)
- [ ] Export progress reports
- [ ] Mobile app
- [ ] Topic-wise recommendation engine
- [ ] Progress tracking over time

## 🤝 Contributing

Feel free to fork, modify, and submit pull requests!

## 📝 License

MIT License - feel free to use for learning and projects

## 🔐 Security Note

**NEVER commit sensitive data like API keys!** 

If you accidentally pushed your API key:
1. Regenerate it immediately at https://console.groq.com/
2. Remove from git history: `git filter-branch --tree-filter 'rm -f backend/.env' HEAD`
3. Force push: `git push --force-with-lease origin main`

Always use `.env` files and add them to `.gitignore`!

## 📞 Support

- Issues? Check existing GitHub issues
- Questions? Read the code comments
- Want to learn more? See the tech stack documentation

---

**Happy Learning! 🎓** This project is designed to help you master full-stack development, AI integration, and competitive programming tracking all at once!
