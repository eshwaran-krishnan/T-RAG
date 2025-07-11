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
                                       timeout=120)
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

# Tool wrapper functions that use API calls
def get_chromadb_status():
    """Get ChromaDB status through API"""
    try:
        result = api_client.process_query("What's the status of the ChromaDB database?")
        if result.get('success'):
            # Parse response for status information
            response_text = result.get('response', '').lower()
            if 'connected' in response_text and 'error' not in response_text:
                return {
                    "connected": True,
                    "collection_available": True,
                    "collection_name": "transcripts",
                    "status": "Connected via API"
                }
            else:
                return {
                    "connected": False,
                    "collection_available": False,
                    "error": "Database not accessible via API"
                }
        else:
            return {
                "connected": False,
                "collection_available": False,
                "error": result.get('error', 'API request failed')
            }
    except Exception as e:
        return {
            "connected": False,
            "collection_available": False,
            "error": f"Failed to get status: {str(e)}"
        }

def reinitialize_chromadb():
    """Reinitialize ChromaDB through API"""
    try:
        result = api_client.process_query("Please reinitialize the ChromaDB database")
        return {
            "success": result.get('success', False),
            "message": result.get('response', 'Reinitialization request sent via API')
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to reinitialize: {str(e)}"
        }

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

def get_current_time():
    """Get current time through API"""
    try:
        result = api_client.process_query("What's the current time?")
        if result.get('success'):
            return result.get('response', 'Time not available')
        else:
            return f"Error: {result.get('error', 'API request failed')}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_system_info():
    """Get system info through API"""
    try:
        result = api_client.process_query("Get system information including platform, CPU usage, and memory usage")
        if result.get('success'):
            response = result.get('response', '')
            return {
                "platform": "Available via API",
                "python_version": "Available via API", 
                "cpu_usage": "Check API response",
                "memory_usage": "Check API response",
                "full_response": response
            }
        else:
            return {
                "platform": "Unknown",
                "python_version": "Unknown",
                "cpu_usage": "Error",
                "memory_usage": "Error",
                "error": result.get('error', 'API request failed')
            }
    except Exception as e:
        return {
            "platform": "Unknown",
            "python_version": "Unknown", 
            "cpu_usage": "Error",
            "memory_usage": "Error",
            "error": str(e)
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
    
    # Cache for sidebar data to prevent constant API calls
    if 'cached_system_info' not in st.session_state:
        st.session_state.cached_system_info = None
    if 'cached_system_info_time' not in st.session_state:
        st.session_state.cached_system_info_time = None
    if 'cached_current_time' not in st.session_state:
        st.session_state.cached_current_time = None
    if 'cached_current_time_timestamp' not in st.session_state:
        st.session_state.cached_current_time_timestamp = None
    if 'cached_db_status' not in st.session_state:
        st.session_state.cached_db_status = None
    if 'cached_db_status_time' not in st.session_state:
        st.session_state.cached_db_status_time = None

def get_cached_system_info(force_refresh=False):
    """Get system info with caching to prevent frequent API calls"""
    cache_duration = 60  # Cache for 60 seconds
    current_time = time.time()
    
    if (force_refresh or 
        st.session_state.cached_system_info is None or 
        st.session_state.cached_system_info_time is None or
        (current_time - st.session_state.cached_system_info_time) > cache_duration):
        
        try:
            st.session_state.cached_system_info = get_system_info()
            st.session_state.cached_system_info_time = current_time
        except Exception as e:
            if st.session_state.cached_system_info is None:
                st.session_state.cached_system_info = {"error": str(e)}
    
    return st.session_state.cached_system_info

def get_cached_current_time(force_refresh=False):
    """Get current time with caching to prevent frequent API calls"""
    cache_duration = 30  # Cache for 30 seconds (shorter for time)
    current_timestamp = time.time()
    
    if (force_refresh or 
        st.session_state.cached_current_time is None or 
        st.session_state.cached_current_time_timestamp is None or
        (current_timestamp - st.session_state.cached_current_time_timestamp) > cache_duration):
        
        try:
            st.session_state.cached_current_time = get_current_time()
            st.session_state.cached_current_time_timestamp = current_timestamp
        except Exception as e:
            if st.session_state.cached_current_time is None:
                st.session_state.cached_current_time = f"Error: {str(e)}"
    
    return st.session_state.cached_current_time

def get_cached_db_status(force_refresh=False):
    """Get database status with caching to prevent frequent API calls"""
    cache_duration = 45  # Cache for 45 seconds
    current_time = time.time()
    
    if (force_refresh or 
        st.session_state.cached_db_status is None or 
        st.session_state.cached_db_status_time is None or
        (current_time - st.session_state.cached_db_status_time) > cache_duration):
        
        try:
            st.session_state.cached_db_status = get_chromadb_status()
            st.session_state.cached_db_status_time = current_time
        except Exception as e:
            if st.session_state.cached_db_status is None:
                st.session_state.cached_db_status = {"error": str(e), "connected": False}
    
    return st.session_state.cached_db_status

def main():
    # Initialize session state
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎯 AmplifAI Transcript Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard Controls")
        
        # Global refresh button
        if st.button("🔄 Refresh All Data", use_container_width=True, type="primary"):
            # Force refresh all cached data
            get_cached_db_status(force_refresh=True)
            get_cached_system_info(force_refresh=True) 
            get_cached_current_time(force_refresh=True)
            st.session_state.api_connected = api_client.check_api_connection()
            st.success("✅ All data refreshed!")
            time.sleep(0.5)  # Brief pause to show success message
            st.rerun()
        
        st.divider()
        
        # API Connection Status Section
        st.subheader("🌐 API Connection")
        
        # Check API connection
        if st.button("🔄 Refresh Connection", use_container_width=True):
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
            
            # Get API status
            try:
                api_status = api_client.get_status()
                if api_status:
                    st.metric("🛠️ Tools Available", api_status.get('tools_count', 0))
                    if api_status.get('azure_openai_connected'):
                        st.success("🧠 Azure OpenAI: Connected")
                    else:
                        st.warning("🧠 Azure OpenAI: Disconnected")
                        
                    if api_status.get('mcp_server_connected'):
                        st.success("🔧 MCP Server: Connected") 
                    else:
                        st.warning("🔧 MCP Server: Disconnected")
            except Exception as e:
                st.error(f"Status check failed: {e}")
        else:
            st.markdown('<p class="status-bad">❌ Disconnected</p>', unsafe_allow_html=True)
            st.error("Cannot connect to API server")
            st.markdown("**Troubleshooting:**")
            st.markdown("1. Check API server is running")
            st.markdown("2. Verify environment variables:")
            st.code(f"""STREAMLIT_API_URL={API_BASE_URL}
STREAMLIT_API_TOKEN={'Set' if API_BEARER_TOKEN else 'Not Set'}""")
        
        st.divider()
        
        # Database Status Section
        st.subheader("💾 Database Status")
        
        if st.session_state.api_connected:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                try:
                    db_status = get_cached_db_status()
                    
                    if db_status.get('connected') and db_status.get('collection_available'):
                        st.markdown('<p class="status-good">✅ Database OK</p>', unsafe_allow_html=True)
                        st.info(f"📂 Via API: {db_status.get('collection_name', 'transcripts')}")
                    else:
                        st.markdown('<p class="status-bad">❌ Database Issue</p>', unsafe_allow_html=True)
                        if 'error' in db_status:
                            st.error(f"Error: {db_status['error']}")
                    
                    # Show cache age
                    if st.session_state.cached_db_status_time:
                        cache_age = time.time() - st.session_state.cached_db_status_time
                        st.caption(f"🕒 Cached {int(cache_age)}s ago")
                        
                except Exception as e:
                    st.error(f"❌ Status check failed: {e}")
            
            with col2:
                if st.button("🔄", help="Refresh DB Status", key="refresh_db"):
                    get_cached_db_status(force_refresh=True)
                    st.rerun()
        else:
            st.info("Connect to API to check database status")
        
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
        
        # System Info
        with st.expander("🖥️ System Information"):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                try:
                    sys_info = get_cached_system_info()
                    st.write(f"**Platform:** {sys_info.get('platform', 'N/A')}")
                    st.write(f"**CPU Usage:** {sys_info.get('cpu_usage', 'N/A')}")
                    st.write(f"**Memory Usage:** {sys_info.get('memory_usage', 'N/A')}")
                    st.write(f"**Python:** {sys_info.get('python_version', 'N/A')}")
                    
                    # Show cache age
                    if st.session_state.cached_system_info_time:
                        cache_age = time.time() - st.session_state.cached_system_info_time
                        st.caption(f"🕒 Cached {int(cache_age)}s ago")
                        
                except Exception as e:
                    st.error(f"Failed to get system info: {e}")
            
            with col2:
                if st.button("🔄", help="Refresh System Info", key="refresh_sys"):
                    get_cached_system_info(force_refresh=True)
                    st.rerun()
        
        # Current time
        col1, col2 = st.columns([3, 1])
        
        with col1:
            try:
                current_time = get_cached_current_time()
                st.info(f"🕒 Current Time: {current_time}")
                
                # Show cache age for time
                if st.session_state.cached_current_time_timestamp:
                    cache_age = time.time() - st.session_state.cached_current_time_timestamp
                    st.caption(f"🕒 Cached {int(cache_age)}s ago")
                    
            except Exception as e:
                st.error(f"Failed to get current time: {e}")
        
        with col2:
            if st.button("🔄", help="Refresh Time", key="refresh_time"):
                get_cached_current_time(force_refresh=True)
                st.rerun()
    
    # Information about caching
    with st.sidebar:
        st.divider()
        with st.expander("ℹ️ About Data Caching"):
            st.markdown("""
            **Smart Caching Enabled** 🧠
            
            To prevent excessive API calls, status data is cached:
            - **Time**: 30 seconds
            - **Database**: 45 seconds  
            - **System Info**: 60 seconds
            
            Use refresh buttons (🔄) or "Refresh All Data" to update manually.
            
            This prevents the API from being overwhelmed with status requests every time you interact with the dashboard.
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
        # Show direct tools when agent not connected
        st.subheader("🛠️ Direct Tools (Agent Not Connected)")
        st.info("Connect the agent above for full AI chat functionality, or use these basic tools:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🕒 Get Current Time", use_container_width=True):
                try:
                    current_time = get_current_time()
                    st.success(f"⏰ Current time: {current_time}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            
            if st.button("🖥️ Get System Info", use_container_width=True):
                try:
                    sys_info = get_system_info()
                    st.json(sys_info)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("🔍 Check Database Status", use_container_width=True):
                try:
                    db_status = get_chromadb_status()
                    st.json(db_status)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            
            # Quick search
            search_query = st.text_input("🔍 Quick Search Transcripts", placeholder="Enter search terms...")
            if st.button("Search", use_container_width=True) and search_query:
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