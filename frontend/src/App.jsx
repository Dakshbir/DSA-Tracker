import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Code2, Search, RefreshCw, AlertCircle, ChevronLeft, ChevronRight, Filter, Send } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const COLORS = {
  Easy: '#10b981',
  Medium: '#f59e0b', 
  Hard: '#ef4444',
  leetcode: '#ffa116',
  codeforces: '#1f8acb'
};

export default function App() {
  const [stats, setStats] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [syncUsername, setSyncUsername] = useState('');
  const [syncPlatform, setSyncPlatform] = useState('leetcode');
  const [syncEmail, setSyncEmail] = useState('');
  const [syncPassword, setSyncPassword] = useState('');
  const [message, setMessage] = useState(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  
  // Filter state
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterDifficulty, setFilterDifficulty] = useState('all');
  // Chat with AI Agent state
  const [showChatModal, setShowChatModal] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  
  useEffect(() => {
    fetchStats();
    fetchQuestions();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats/`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchQuestions = async () => {
    try {
      // Fetch ALL questions (increase limit to 1000)
      const response = await fetch(`${API_BASE_URL}/questions/?limit=1000`);
      const data = await response.json();
      setQuestions(data);
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
  };

  const handleSync = async () => {
    if (!syncUsername.trim()) {
      setMessage({ type: 'error', text: 'Please enter a username' });
      return;
    }

    if (syncPlatform === 'leetcode' && !syncEmail.trim()) {
      setMessage({ type: 'error', text: 'Please enter your LeetCode email' });
      return;
    }

    if (syncPlatform === 'leetcode' && !syncPassword.trim()) {
      setMessage({ type: 'error', text: 'Please enter your LeetCode password' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      let url = `${API_BASE_URL}/sync/${syncPlatform}/${syncUsername}`;
      
      // Add credentials for LeetCode
      if (syncPlatform === 'leetcode') {
        const params = new URLSearchParams({
          email: syncEmail,
          password: syncPassword
        });
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, { method: 'POST' });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Sync failed');
      }

      const result = await response.json();
      setMessage({
        type: 'success',
        text: `✅ ${result.message}! Added ${result.new_questions_added} new questions.`
      });

      await fetchStats();
      await fetchQuestions();
      setSyncUsername('');
      setSyncEmail('');
      setSyncPassword('');
      setCurrentPage(1); // Reset to first page
    } catch (error) {
      setMessage({ type: 'error', text: `❌ ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  // Filter questions based on selected filters
  const filteredQuestions = questions.filter(q => {
    const platformMatch = filterPlatform === 'all' || q.platform === filterPlatform;
    const difficultyMatch = filterDifficulty === 'all' || q.difficulty === filterDifficulty;
    return platformMatch && difficultyMatch;
  });

  // Pagination calculations
  const totalPages = Math.ceil(filteredQuestions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentQuestions = filteredQuestions.slice(startIndex, endIndex);

  // Chart data
  const chartData = stats.map(stat => ({
    platform: stat.platform,
    Easy: stat.easy_count,
    Medium: stat.medium_count,
    Hard: stat.hard_count,
    Total: stat.total_solved
  }));

  const totalStats = stats.reduce((acc, stat) => ({
    easy: acc.easy + stat.easy_count,
    medium: acc.medium + stat.medium_count,
    hard: acc.hard + stat.hard_count,
    total: acc.total + stat.total_solved
  }), { easy: 0, medium: 0, hard: 0, total: 0 });

  const pieData = [
    { name: 'Easy', value: totalStats.easy },
    { name: 'Medium', value: totalStats.medium },
    { name: 'Hard', value: totalStats.hard }
  ].filter(d => d.value > 0);

  // Codeforces rating distribution
  const codeforcesQuestions = questions.filter(q => q.platform === 'codeforces');
  const ratingCounts = {};
  codeforcesQuestions.forEach(q => {
    const rating = q.difficulty || 'Unrated';
    ratingCounts[rating] = (ratingCounts[rating] || 0) + 1;
  });
  
  // Sort ratings numerically
  const sortedRatings = Object.keys(ratingCounts).sort((a, b) => {
    const numA = parseInt(a) || 0;
    const numB = parseInt(b) || 0;
    return numA - numB;
  });
  
  const ratingChartData = sortedRatings.map(rating => ({
    rating: rating,
    count: ratingCounts[rating]
  }));

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return; // Don't send empty messages
    
    const messageToSend = chatInput; // Store before clearing
    
    // Add user message to chat
    const userMessage = { role: 'user', content: messageToSend };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);
    
    try {
      // Send to backend
      const response = await fetch(`${API_BASE_URL}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageToSend })
      });
      
      const data = await response.json();
      
      // Add agent response to chat
      const agentMessage = { 
        role: 'assistant', 
        content: data.response 
      };
      setChatMessages(prev => [...prev, agentMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '❌ Error: Could not get response from agent' 
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatInput('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Code2 size={40} className="text-purple-400" />
            <h1 className="text-4xl font-bold">DSA Tracker</h1>
          </div>
          <p className="text-gray-400">Track your coding journey across platforms</p>
        </div>

        {/* Sync Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 mb-8 border border-white/20">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Search size={24} />
            Sync Platform Data
          </h2>
          
          <div className="flex flex-wrap gap-4 items-end mb-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm mb-2 text-gray-300">Username</label>
              <input
                type="text"
                value={syncUsername}
                onChange={(e) => setSyncUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
              />
            </div>

            <div className="w-48">
              <label className="block text-sm mb-2 text-gray-300">Platform</label>
              <select
                value={syncPlatform}
                onChange={(e) => setSyncPlatform(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
              >
                <option value="leetcode">LeetCode</option>
                <option value="codeforces">Codeforces</option>
              </select>
            </div>

            <button
              onClick={handleSync}
              disabled={loading}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <RefreshCw size={20} className="animate-spin" />
                  Syncing...
                </>
              ) : (
                <>
                  <RefreshCw size={20} />
                  Sync Data
                </>
              )}
            </button>
          </div>

          {/* LeetCode Credentials Section */}
          {syncPlatform === 'leetcode' && (
            <div className="flex flex-wrap gap-4 mb-4 p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm mb-2 text-gray-300">LeetCode Email</label>
                <input
                  type="email"
                  value={syncEmail}
                  onChange={(e) => setSyncEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
                />
              </div>

              <div className="flex-1 min-w-[200px]">
                <label className="block text-sm mb-2 text-gray-300">LeetCode Password</label>
                <input
                  type="password"
                  value={syncPassword}
                  onChange={(e) => setSyncPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
                />
              </div>
            </div>
          )}

          {message && (
            <div className={`mt-4 p-3 rounded-lg flex items-start gap-2 ${
              message.type === 'success' ? 'bg-green-500/20 border border-green-500/50' : 'bg-red-500/20 border border-red-500/50'
            }`}>
              <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
              <span>{message.text}</span>
            </div>
          )}
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard title="Total Solved" value={totalStats.total} color="purple" />
          <StatCard title="Easy" value={totalStats.easy} color="green" />
          <StatCard title="Medium" value={totalStats.medium} color="yellow" />
          <StatCard title="Hard" value={totalStats.hard} color="red" />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Bar Chart */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold mb-4">Platform-wise Progress</h3>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                  <XAxis dataKey="platform" stroke="#fff" />
                  <YAxis stroke="#fff" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  />
                  <Legend />
                  <Bar dataKey="Easy" fill={COLORS.Easy} />
                  <Bar dataKey="Medium" fill={COLORS.Medium} />
                  <Bar dataKey="Hard" fill={COLORS.Hard} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                No data yet. Sync your profile to see stats!
              </div>
            )}
          </div>

          {/* Codeforces Rating Distribution */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold mb-4">Codeforces Rating Distribution</h3>
            {ratingChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ratingChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                  <XAxis dataKey="rating" stroke="#fff" angle={-45} textAnchor="end" height={80} />
                  <YAxis stroke="#fff" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                    formatter={(value) => [`${value} problems`, 'Count']}
                  />
                  <Bar dataKey="count" fill="#a78bfa" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                No Codeforces data yet. Sync your Codeforces profile!
              </div>
            )}
          </div>
        </div>

        {/* All Submissions with Filters and Pagination */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <TrendingUp size={24} />
              All Submissions ({filteredQuestions.length} total)
            </h3>
            
            {/* Filters */}
            <div className="flex gap-3">
              <select
                value={filterPlatform}
                onChange={(e) => {
                  setFilterPlatform(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-1 rounded-lg bg-white/10 border border-white/20 text-sm"
              >
                <option value="all">All Platforms</option>
                <option value="leetcode">LeetCode</option>
                <option value="codeforces">Codeforces</option>
              </select>
              
              <select
                value={filterDifficulty}
                onChange={(e) => {
                  setFilterDifficulty(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-3 py-1 rounded-lg bg-white/10 border border-white/20 text-sm"
              >
                <option value="all">All Difficulties</option>
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>
          
          {currentQuestions.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/20">
                      <th className="text-left py-3 px-4">Title</th>
                      <th className="text-left py-3 px-4">Platform</th>
                      <th className="text-left py-3 px-4">Difficulty</th>
                      <th className="text-left py-3 px-4">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentQuestions.map((q) => (
                      <tr key={q.id} className="border-b border-white/10 hover:bg-white/5">
                        <td className="py-3 px-4">{q.title}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-1 rounded text-sm" style={{ backgroundColor: COLORS[q.platform] + '40' }}>
                            {q.platform}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className="px-2 py-1 rounded text-sm font-medium"
                            style={{ backgroundColor: COLORS[q.difficulty] + '40', color: COLORS[q.difficulty] }}
                          >
                            {q.difficulty || 'N/A'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-400">
                          {new Date(q.solved_date).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <div className="text-sm text-gray-400">
                    Showing {startIndex + 1}-{Math.min(endIndex, filteredQuestions.length)} of {filteredQuestions.length}
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      <ChevronLeft size={20} />
                      Previous
                    </button>
                    
                    <div className="flex items-center gap-2">
                      {[...Array(totalPages)].map((_, i) => {
                        const page = i + 1;
                        // Show first, last, current, and pages around current
                        if (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 1 && page <= currentPage + 1)
                        ) {
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`px-3 py-1 rounded-lg ${
                                currentPage === page
                                  ? 'bg-purple-600'
                                  : 'bg-white/10 hover:bg-white/20'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        } else if (
                          page === currentPage - 2 ||
                          page === currentPage + 2
                        ) {
                          return <span key={page}>...</span>;
                        }
                        return null;
                      })}
                    </div>
                    
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      Next
                      <ChevronRight size={20} />
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-gray-400">
              {questions.length === 0 
                ? "No questions yet. Sync your profile to see your progress!"
                : "No questions match the selected filters."
              }
            </div>
          )}
        </div>

        {/* Chat with AI Agent */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold flex items-center gap-2">
              <TrendingUp size={24} />
              Chat with AI Agent
            </h3>
            
            <button
              onClick={() => setShowChatModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
            >
              💬 Ask CodeMentor
            </button>
          </div>
          
          <div className="text-gray-400">
            Have questions or need help with problems? Chat with our AI agent, CodeMentor, for instant assistance and tips!
          </div>
        </div>

        {/* Chat Modal */}
        {showChatModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="w-96 h-96 bg-purple-900 rounded-lg shadow-xl flex flex-col">
              {/* Header */}
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 p-4 rounded-t-lg flex justify-between items-center">
                <h3 className="text-white font-bold flex items-center gap-2">
                  🤖 CodeMentor AI
                </h3>
                <button
                  onClick={() => setShowChatModal(false)}
                  className="text-white hover:bg-purple-600 p-2 rounded"
                >
                  ✕
                </button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {chatMessages.length === 0 && !chatLoading ? (
                  <div className="text-gray-400 text-sm text-center mt-4">
                    💡 Ask me questions about your DSA progress!
                    <br/>
                    <br/>
                    Examples:
                    <br/>
                    • "How many problems have I solved?"
                    <br/>
                    • "What should I practice?"
                    <br/>
                    • "Show my recent submissions"
                  </div>
                ) : (
                  <>
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs px-3 py-2 rounded-lg ${
                            msg.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-purple-600 text-white'
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-purple-600 text-white px-3 py-2 rounded-lg flex items-center gap-2">
                          <RefreshCw size={16} className="animate-spin" />
                          CodeMentor is thinking...
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-white/20">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask a question..."
                    className="flex-1 px-4 py-2 rounded-lg bg-white/10 border border-white/20 focus:border-purple-400 focus:outline-none"
                  />
                  <button
                    onClick={sendChatMessage}
                    disabled={chatLoading}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {chatLoading ? (
                      <>
                        <RefreshCw size={20} className="animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send size={20} />
                        Send
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div className={`bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20`}>
      <div className="text-sm text-gray-400 mb-1">{title}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}