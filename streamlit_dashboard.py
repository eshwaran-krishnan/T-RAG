import streamlit as st
import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
API_BASE_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:7860")
API_BEARER_TOKEN = os.getenv("STREAMLIT_API_TOKEN", None)

# API client for external endpoint
class APIClient:
    """Client to communicate with the external FastAPI MCP server"""
    
    def __init__(self, base_url: str = API_BASE_URL, bearer_token: str = API_BEARER_TOKEN):
        self.base_url = base_url
        self.bearer_token = bearer_token
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Add Bearer token authentication if provided
        if self.bearer_token:
            self.session.headers.update({"Authorization": f"Bearer {self.bearer_token}"})
    
    def check_api_connection(self) -> bool:
        """Check if API server is running"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get status from API server"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Status request failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Status request error: {e}")
            return None
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query via API server"""
        try:
            payload = {"query": query}
            response = self.session.post(f"{self.base_url}/api/query", 
                                       json=payload, 
                                       timeout=180)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "response": f"API request failed with status {response.status_code}",
                    "error": f"HTTP {response.status_code}",
                    "total_rounds": 0,
                    "total_execution_time": 0,
                    "iteration_details": []
                }
        except Exception as e:
            return {
                "success": False,
                "response": f"Request error: {str(e)}",
                "error": str(e),
                "total_rounds": 0,
                "total_execution_time": 0,
                "iteration_details": []
            }

# Global API client
api_client = APIClient(base_url=API_BASE_URL, bearer_token=API_BEARER_TOKEN)

# Simplified caching - only for tools
def get_cached_tools(force_refresh=False):
    """Get available tools with caching to prevent frequent API calls"""
    cache_duration = 60  # Cache for 60 seconds (1 minute)
    current_time = time.time()
    
    # Initialize cache if not exists
    if 'cached_tools' not in st.session_state:
        st.session_state.cached_tools = None
    if 'cached_tools_time' not in st.session_state:
        st.session_state.cached_tools_time = None
    
    if (force_refresh or 
        st.session_state.cached_tools is None or 
        st.session_state.cached_tools_time is None or
        (current_time - st.session_state.cached_tools_time) > cache_duration):
        
        try:
            # Get tools via API status endpoint
            api_status = api_client.get_status()
            if api_status:
                st.session_state.cached_tools = {
                    "count": api_status.get('tools_count', 0),
                    "azure_connected": api_status.get('azure_openai_connected', False),
                    "mcp_connected": api_status.get('mcp_server_connected', False),
                    "status": "success"
                }
            else:
                st.session_state.cached_tools = {
                    "count": 0,
                    "azure_connected": False,
                    "mcp_connected": False,
                    "status": "failed"
                }
            st.session_state.cached_tools_time = current_time
        except Exception as e:
            if st.session_state.cached_tools is None:
                st.session_state.cached_tools = {
                    "count": 0,
                    "azure_connected": False,
                    "mcp_connected": False,
                    "status": "error",
                    "error": str(e)
                }
    
    return st.session_state.cached_tools

# Keep only the search function as it's user-initiated
def search_calls_transcript_database(**kwargs):
    """Search transcript database through API"""
    try:
        query = kwargs.get('query', '')
        max_results = kwargs.get('max_results', 5)
        search_query = f"Search for '{query}' in the transcript database, limit to {max_results} results"
        
        result = api_client.process_query(search_query)
        if result.get('success'):
            return {
                "success": True,
                "results": [],  # API returns formatted text, not structured results
                "total_found": 1 if result.get('response') else 0,
                "response_text": result.get('response', '')
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Search failed'),
                "results": [],
                "total_found": 0
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}",
            "results": [],
            "total_found": 0
        }

# Page configuration
st.set_page_config(
    page_title="AmplifAI Transcript Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-bad {
        color: #dc3545;
        font-weight: bold;
    }
    .search-results {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #17a2b8;
    }
    .result-metadata {
        background-color: #e9ecef;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .agent-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .connection-status {
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
    }
    .status-connected {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-disconnected {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for API client
def init_session_state():
    """Initialize session state variables"""
    if 'api_connected' not in st.session_state:
        st.session_state.api_connected = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'api_checking' not in st.session_state:
        st.session_state.api_checking = False

def main():
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎯 AmplifAI Transcript Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard Controls")
        
        # Global refresh button - simplified
        if st.button("🔄 Refresh Connection", use_container_width=True, type="primary"):
            st.session_state.api_connected = api_client.check_api_connection()
            get_cached_tools(force_refresh=True)
            st.success("✅ Connection refreshed!")
            time.sleep(0.5)
            st.rerun()
        
        st.divider()
        
        # API Connection Status Section
        st.subheader("🌐 API Connection")
        
        # Check API connection
        if st.button("🔄 Test Connection", use_container_width=True):
            st.session_state.api_connected = api_client.check_api_connection()
            st.rerun()
        
        # Auto-check connection on first load
        if not st.session_state.api_checking:
            st.session_state.api_connected = api_client.check_api_connection()
            st.session_state.api_checking = True
        
        if st.session_state.api_connected:
            st.markdown('<p class="status-good">✅ Connected</p>', unsafe_allow_html=True)
            st.info(f"🔗 API: {api_client.base_url}")
            
            # Authentication status
            if api_client.bearer_token:
                st.success("🔐 Authenticated")
            else:
                st.info("🔓 Public Access")
            
            # Get tools status - cached
            try:
                tools_info = get_cached_tools()
                if tools_info.get('status') == 'success':
                    st.metric("🛠️ Tools Available", tools_info.get('count', 0))
                    if tools_info.get('azure_connected'):
                        st.success("🧠 Azure OpenAI: Connected")
                    else:
                        st.warning("🧠 Azure OpenAI: Disconnected")
                        
                    if tools_info.get('mcp_connected'):
                        st.success("🔧 MCP Server: Connected") 
                    else:
                        st.warning("🔧 MCP Server: Disconnected")
                    
                    # Show cache age
                    if 'cached_tools_time' in st.session_state and st.session_state.cached_tools_time:
                        cache_age = time.time() - st.session_state.cached_tools_time
                        st.caption(f"🕒 Cached {int(cache_age)}s ago")
                else:
                    st.error("Failed to get tools status")
            except Exception as e:
                st.error(f"Tools status error: {e}")
        else:
            st.markdown('<p class="status-bad">❌ Disconnected</p>', unsafe_allow_html=True)
            st.error("Cannot connect to API server")
            st.markdown("**Troubleshooting:**")
            st.markdown("1. Check API server is running")
            st.markdown("2. Verify environment variables:")
            st.code(f"""STREAMLIT_API_URL={API_BASE_URL}
STREAMLIT_API_TOKEN={'Set' if API_BEARER_TOKEN else 'Not Set'}""")
        
        st.divider()
        
        # Chat Status Section  
        st.subheader("💬 Chat Status")
        
        if st.session_state.api_connected:
            st.markdown('<p class="status-good">✅ Ready to Chat</p>', unsafe_allow_html=True)
            
            # Show chat stats
            if st.session_state.chat_history:
                user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
                st.metric("💬 Messages", f"{user_messages} sent")
                
                # Show last activity
                if st.session_state.chat_history:
                    last_msg = st.session_state.chat_history[-1]
                    last_time = datetime.fromisoformat(last_msg["timestamp"])
                    time_ago = datetime.now() - last_time
                    st.caption(f"🕒 Last activity: {int(time_ago.total_seconds())}s ago")
            else:
                st.info("No chat history yet")
        else:
            st.markdown('<p class="status-bad">❌ Chat Unavailable</p>', unsafe_allow_html=True)
            st.info("Connect to API to start chatting")
        
        st.divider()
        
        # Information about simplified approach
        with st.expander("ℹ️ About This Dashboard"):
            st.markdown("""
            **Simplified & Efficient** ⚡
            
            This dashboard focuses on core functionality:
            - **Real-time chat** with AI agent
            - **Tools status** (cached for 1 minute)
            - **Minimal API calls** to prevent overload
            
            Status checks like system info, time, and database details have been removed to prevent excessive API requests.
            
            Use the chat interface to get real-time information when needed!
            """)
    
    # Main content area - Simple interface
    simple_interface()

def simple_interface():
    """Simple unified interface for API-based AI chat and tools"""
    st.subheader("🤖 AI Chat Interface")
    
    # API connection info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.api_connected:
            st.success(f"✅ Connected to API: {api_client.base_url}")
            if api_client.bearer_token:
                st.info("🔐 Authenticated with Bearer token")
            else:
                st.info("🔓 Using public access")
        else:
            st.error(f"❌ Cannot connect to API: {api_client.base_url}")
            st.markdown("**Check:**")
            st.markdown("- API server is running")
            st.markdown("- Environment variables are set correctly")
    
    with col2:
        if st.button("🔄 Test Connection", use_container_width=True):
            with st.spinner("Testing..."):
                st.session_state.api_connected = api_client.check_api_connection()
                if st.session_state.api_connected:
                    st.success("✅ Connected!")
                else:
                    st.error("❌ Failed!")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # Chat interface or quick tools
    if st.session_state.api_connected:
        # Chat interface
        st.subheader("💬 Chat with AI Agent")
        
        # Display chat history
        if st.session_state.chat_history:
            chat_container = st.container()
            
            with chat_container:
                for i, message in enumerate(st.session_state.chat_history):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #2196f3;">
                            <strong>👤 You:</strong><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #f3e5f5; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #9c27b0;">
                            <strong>🤖 Agent:</strong><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if "execution_time" in message:
                            st.caption(f"⏱️ Response time: {message['execution_time']:.2f}s")
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "💭 Your message:",
                placeholder="Ask me anything! I can search transcripts, get system info, perform calculations, etc.",
                key="chat_input"
            )
            
            col1, col2 = st.columns([4, 1])
            with col2:
                send_button = st.form_submit_button("📤 Send", use_container_width=True)
        
        # Handle chat message
        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user", 
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process the query via API
            with st.spinner("🤖 AI is thinking..."):
                try:
                    start_time = time.time()
                    result = api_client.process_query(user_input)
                    end_time = time.time()
                    
                    if result.get('success'):
                        response_content = result.get('response', 'No response received')
                        
                        # Add agent response to history with API details
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response_content,
                            "timestamp": datetime.now().isoformat(),
                            "execution_time": end_time - start_time,
                            "api_rounds": result.get('total_rounds', 0),
                            "api_execution_time": result.get('total_execution_time', 0)
                        })
                    else:
                        error_message = f"❌ Error: {result.get('error', 'Unknown error')}"
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_message,
                            "timestamp": datetime.now().isoformat(),
                            "execution_time": end_time - start_time
                        })
                    
                    st.rerun()
                    
                except Exception as e:
                    error_message = f"❌ API Error: {str(e)}"
                    print(f"Error in API query processing: {e}")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.error(error_message)
        
        # Quick action buttons
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🕒 Get Current Time", use_container_width=True):
                quick_query("What's the current time?")
        
        with col2:
            if st.button("🖥️ System Info", use_container_width=True):
                quick_query("Get system information")
        
        with col3:
            if st.button("🔍 Search Transcripts", use_container_width=True):
                quick_query("How can I search for transcripts?")
        
        with col4:
            if st.button("💾 Database Status", use_container_width=True):
                quick_query("What's the status of the transcript database?")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
    
    else:
        # Show simplified message when agent not connected
        st.subheader("🛠️ Connect to API for Full Functionality")
        st.info("Connect the API above to enable AI chat and tools functionality.")
        
        # Basic search still available when disconnected
        st.subheader("🔍 Basic Search (When Connected)")
        search_query = st.text_input("🔍 Search Transcripts", placeholder="Enter search terms...", disabled=not st.session_state.api_connected)
        if st.button("Search", use_container_width=True, disabled=not st.session_state.api_connected) and search_query:
            try:
                with st.spinner("Searching..."):
                    results = search_calls_transcript_database(query=search_query, max_results=5)
                    if results.get('success'):
                        st.success(f"Found {results.get('total_found', 0)} results")
                        if results.get('response_text'):
                            st.write("**Search Results:**")
                            st.write(results.get('response_text'))
                    else:
                        st.error(f"Search failed: {results.get('error')}")
            except Exception as e:
                st.error(f"❌ Search error: {e}")

def quick_query(query: str):
    """Execute a quick query via API"""
    if not st.session_state.api_connected:
        st.error("❌ API not connected")
        return
    
    # Add to chat history and trigger processing
    st.session_state.chat_history.append({
        "role": "user", 
        "content": query,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        with st.spinner("🤖 Processing..."):
            start_time = time.time()
            result = api_client.process_query(query)
            end_time = time.time()
            
            if result.get('success'):
                response_content = result.get('response', 'No response received')
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": end_time - start_time
                })
            else:
                error_message = f"❌ Error: {result.get('error', 'Unknown error')}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": end_time - start_time
                })
            
            st.rerun()
            
    except Exception as e:
        error_message = f"❌ API Error: {str(e)}"
        print(f"Error in quick query: {e}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": error_message,
            "timestamp": datetime.now().isoformat()
        })
        st.error(error_message)

if __name__ == "__main__":
    main()