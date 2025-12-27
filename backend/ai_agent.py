"""
CodeMentor AI Agent - Your intelligent DSA practice assistant.
Using Groq for FREE, fast AI responses!

This agent can:
- Answer questions about your progress
- Analyze your solving patterns
- Recommend next steps
- Provide insights and motivation
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Force using the old AgentExecutor API - works better with Groq
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    USE_LANGGRAPH = False
except ImportError:
    # Fallback to LangGraph if old API not available
    try:
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import HumanMessage
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        USE_LANGGRAPH = True
    except ImportError:
        raise ImportError("Please install langchain packages: pip install langchain langgraph langchain-groq langchain-core")

from agent_tools import ALL_TOOLS

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("""
⚠️  GROQ_API_KEY not found!

To get a FREE Groq API key:
1. Go to: https://console.groq.com/
2. Sign up (free!)
3. Create an API key
4. Add to .env file: GROQ_API_KEY=your_key_here
""")


class CodeMentorAgent:
    """
    CodeMentor - AI agent for DSA tracking and guidance.
    
    This agent uses:
    1. Groq (Free LLM) for reasoning and responses
    2. Tools for database queries
    3. Memory for conversation context
    """
    
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        """
        Initialize the agent with Groq and tools.
        
        Available Groq models:
        - "llama-3.3-70b-versatile" (Default - Best balance)
        - "llama-3.1-8b-instant" (Fastest)
        - "mixtral-8x7b-32768" (Good for long context)
        """
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.7,  # Balanced creativity
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Define the agent's personality and instructions
        self.system_prompt = """You are CodeMentor, an expert AI assistant for DSA (Data Structures & Algorithms) practice tracking.

Your personality:
- Encouraging and motivating
- Analytical and insightful
- Patient and helpful
- Technical but friendly

Your capabilities:
- Analyze user's problem-solving progress
- Identify strengths and weaknesses
- Recommend practice strategies
- Answer questions about statistics
- Provide actionable insights

Guidelines:
1. Always use tools to fetch accurate data - don't make up statistics
2. Provide specific, actionable advice
3. Celebrate achievements and progress
4. Be honest about areas needing improvement
5. Use emojis sparingly but effectively
6. Keep responses concise but informative
7. When showing statistics, format them clearly

Important: When you use a tool, ALWAYS wait for the result before responding.
Don't say "I'll check" or "Let me fetch" - just use the tool and present the findings.

Remember: You're here to help the user improve their problem-solving skills!"""
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent with tools based on available API
        if USE_LANGGRAPH:
            # Modern LangGraph API
            self.agent_executor = create_react_agent(
                self.llm,
                tools=ALL_TOOLS,
                prompt=self.system_prompt
            )
        else:
            # Fallback to old API
            self.agent = create_tool_calling_agent(
                llm=self.llm,
                tools=ALL_TOOLS,
                prompt=self.prompt
            )
            
            # Create executor (runs the agent)
            from langchain.agents import AgentExecutor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=ALL_TOOLS,
                verbose=True,  # Show thinking process
                handle_parsing_errors=True,
                max_iterations=10,  # Prevent infinite loops
                return_intermediate_steps=False
            )
        
        print(f"✅ CodeMentor initialized with Groq ({model_name})!")
    
    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            user_message: User's question or request
            
        Returns:
            Agent's response as a string
        """
        try:
            if USE_LANGGRAPH:
                # Modern LangGraph API
                messages = [HumanMessage(content=user_message)]
                response = self.agent_executor.invoke({"messages": messages})
                # Extract output from the last message
                output = response["messages"][-1].content if response["messages"] else "I'm sorry, I couldn't process that request."
            else:
                # Old API
                response = self.agent_executor.invoke({
                    "input": user_message,
                })
                output = response.get("output", "I'm sorry, I couldn't process that request.")
            
            return output
            
        except Exception as e:
            error_message = f"I encountered an error: {str(e)}"
            print(f"❌ Error: {e}")
            return error_message
    
    def clear_memory(self):
        """Clear conversation history"""
        if not USE_LANGGRAPH and hasattr(self, 'memory'):
            self.memory.clear()
            print("🧹 Memory cleared!")
        else:
            print("🧹 Memory management not available in current mode")


# ============= ALTERNATIVE: LOCAL OLLAMA VERSION =============

class CodeMentorAgentLocal:
    """
    Local version using Ollama - runs on your machine!
    
    Setup:
    1. Install Ollama: https://ollama.ai/
    2. Run: ollama pull llama3.1
    3. No API key needed!
    """
    
    def __init__(self, model="llama3.1"):
        """Initialize with local Ollama"""
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError("Install langchain-ollama: pip install langchain-ollama")
        
        self.llm = ChatOllama(
            model=model,
            temperature=0.7
        )
        
        # Same setup as Groq version
        self.system_prompt = """You are CodeMentor, an expert AI assistant for DSA practice tracking.

Your role: Help users track and improve their problem-solving skills.

Guidelines:
- Use tools to fetch accurate data
- Provide actionable advice
- Be encouraging and motivating
- Keep responses clear and concise"""
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=ALL_TOOLS,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=ALL_TOOLS,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        print(f"✅ CodeMentor initialized with Ollama ({model})!")
    
    def chat(self, user_message: str) -> str:
        """Chat with local AI"""
        try:
            chat_history = self.memory.chat_memory.messages
            
            response = self.agent_executor.invoke({
                "input": user_message,
                "chat_history": chat_history
            })
            
            output = response.get("output", "I couldn't process that.")
            
            self.memory.chat_memory.add_user_message(user_message)
            self.memory.chat_memory.add_ai_message(output)
            
            return output
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_memory(self):
        """Clear conversation history"""
        self.memory.clear()
        print("🧹 Memory cleared!")


# ============= USAGE EXAMPLES =============

def test_agent():
    """Test the agent with sample queries"""
    
    print("=" * 60)
    print("🤖 CODEMENTOR AI AGENT TEST")
    print("=" * 60)
    
    # Choose which agent to use
    use_local = input("Use local Ollama? (y/n): ").lower() == 'y'
    
    if use_local:
        print("\n🏠 Using local Ollama...")
        agent = CodeMentorAgentLocal()
    else:
        print("\n☁️  Using Groq (cloud)...")
        agent = CodeMentorAgent()
    
    # Test queries
    test_queries = [
        "What's my overall progress?",
        "How many problems have I solved?",
        "What topics should I practice more?",
        "Show my recent submissions",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"👤 User: {query}")
        print(f"{'='*60}\n")
        
        response = agent.chat(query)
        
        print(f"\n🤖 CodeMentor: {response}\n")
        
        cont = input("Continue? (y/n): ")
        if cont.lower() != 'y':
            break
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    # Run tests if executed directly
    test_agent()