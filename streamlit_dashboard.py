"""
AmplifAI Agent Dashboard - Streamlit Interface

This dashboard provides a web interface for interacting with the AmplifAI Agent SDK,
which specializes in call transcript analysis using:
- Agent SDK with OpenRouter (GPT-4.1) 
- Native MCP server integration for tool access
- Comprehensive analysis of transcript databases
- Real-time insights with specific examples and transcript IDs
"""

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
API_BASE_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
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
            print(f"API connection failed: {e}")
            return False
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get status from API server"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Status request failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"Status request error: {e}")
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
                    "azure_connected": api_status.get('azure_openai_connected', False),  # Kept for compatibility - now represents Agent SDK
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
    page_title="AmplifAI Agent Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
        border-bottom: 2px solid #ecf0f1;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Status indicators */
    .status-good {
        color: #27ae60;
        font-weight: 500;
        background-color: #e8f5e8;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
    
    .status-bad {
        color: #c0392b;
        font-weight: 500;
        background-color: #fdf2f2;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
    
    /* Cards and containers */
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.08);
        margin: 0.5rem 0;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        margin: 0.75rem 0;
        word-wrap: break-word;
        font-family: 'Inter', sans-serif;
        line-height: 1.5;
    }
    
    .user-message {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 4px solid #6c757d;
    }
    
    .agent-message {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-left: 4px solid #495057;
    }
    
    /* Connection status */
    .connection-status {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 0.75rem 0;
        text-align: center;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }
    
    .status-connected {
        background-color: #e8f5e8;
        color: #27ae60;
        border: 1px solid #c3e6cb;
    }
    
    .status-disconnected {
        background-color: #fdf2f2;
        color: #c0392b;
        border: 1px solid #f5c6cb;
    }
    
    /* Button styling improvements */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border-radius: 0.5rem;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.12);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        font-family: 'Inter', sans-serif;
        border-radius: 0.5rem;
        border: 1px solid #ced4da;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.08);
    }
    
    /* Search results */
    .search-results {
        background-color: #ffffff;
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin: 0.75rem 0;
        border: 1px solid #e9ecef;
        border-left: 4px solid #6c757d;
        box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.08);
    }
    
    .result-metadata {
        background-color: #f8f9fa;
        padding: 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        margin-top: 0.75rem;
        border: 1px solid #e9ecef;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 1px;
        background-color: #e9ecef;
        margin: 1.5rem 0;
    }
    
    /* Success/Error/Info styling */
    .stSuccess {
        background-color: #e8f5e8;
        border: 1px solid #c3e6cb;
        color: #27ae60;
    }
    
    .stError {
        background-color: #fdf2f2;
        border: 1px solid #f5c6cb;
        color: #c0392b;
    }
    
    .stInfo {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
        color: #1976d2;
    }
    
    .stWarning {
        background-color: #fff3e0;
        border: 1px solid #ffcc80;
        color: #f57c00;
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
    st.markdown('<h1 class="main-header">AmplifAI Agent Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Dashboard Controls")
        
        # Global refresh button - simplified
        if st.button("Refresh Connection", use_container_width=True, type="primary", key="sidebar_refresh"):
            st.session_state.api_connected = api_client.check_api_connection()
            get_cached_tools(force_refresh=True)
            st.success("Connection refreshed successfully")
            time.sleep(0.5)
            st.rerun()
        
        st.divider()
        
        # API Connection Status Section
        st.subheader("API Connection")
        
        # Check API connection
        if st.button("Test Connection", use_container_width=True, key="sidebar_test_connection"):
            st.session_state.api_connected = api_client.check_api_connection()
            st.rerun()
        
        # Auto-check connection on first load
        if not st.session_state.api_checking:
            st.session_state.api_connected = api_client.check_api_connection()
            st.session_state.api_checking = True
        
        if st.session_state.api_connected:
            st.markdown('<p class="status-good">Connected</p>', unsafe_allow_html=True)
            st.info(f"API Endpoint: {api_client.base_url}")
            
            # Authentication status
            if api_client.bearer_token:
                st.success("Authentication: Enabled")
            else:
                st.info("Authentication: Public Access")
            
            # Get tools status - cached
            try:
                tools_info = get_cached_tools()
                if tools_info.get('status') == 'success':
                    st.metric("Tools Available", tools_info.get('count', 0))
                    if tools_info.get('azure_connected'):  # Note: This field name is kept for compatibility
                        st.success("Agent SDK (OpenRouter): Connected")
                    else:
                        st.warning("Agent SDK (OpenRouter): Disconnected")
                        
                    if tools_info.get('mcp_connected'):
                        st.success("MCP Servers: Connected") 
                    else:
                        st.warning("MCP Servers: Disconnected")
                    
                    # Show cache age
                    if 'cached_tools_time' in st.session_state and st.session_state.cached_tools_time:
                        cache_age = time.time() - st.session_state.cached_tools_time
                        st.caption(f"Cached {int(cache_age)}s ago")
                else:
                    st.error("Failed to get tools status")
            except Exception as e:
                st.error(f"Tools status error: {e}")
        else:
            st.markdown('<p class="status-bad">Disconnected</p>', unsafe_allow_html=True)
            st.error("Cannot connect to API server")
            st.markdown("**Troubleshooting:**")
            st.markdown("1. Check API server is running")
            st.markdown("2. Verify environment variables:")
            st.code(f"""STREAMLIT_API_URL={API_BASE_URL}
STREAMLIT_API_TOKEN={'Set' if API_BEARER_TOKEN else 'Not Set'}""")
        
        st.divider()
        
        # Chat Status Section  
        st.subheader("Chat Status")
        
        if st.session_state.api_connected:
            st.markdown('<p class="status-good">Ready to Chat</p>', unsafe_allow_html=True)
            
            # Show chat stats
            if st.session_state.chat_history:
                user_messages = len([m for m in st.session_state.chat_history if m["role"] == "user"])
                st.metric("Messages", f"{user_messages} sent")
                
                # Show last activity
                if st.session_state.chat_history:
                    last_msg = st.session_state.chat_history[-1]
                    last_time = datetime.fromisoformat(last_msg["timestamp"])
                    time_ago = datetime.now() - last_time
                    st.caption(f"Last activity: {int(time_ago.total_seconds())}s ago")
            else:
                st.info("No chat history yet")
        else:
            st.markdown('<p class="status-bad">Chat Unavailable</p>', unsafe_allow_html=True)
            st.info("Connect to API to start chatting")
        
        st.divider()
        
        # Information about Agent SDK approach
        with st.expander("About This Dashboard"):
            st.markdown("""
            **Agent SDK Powered**
            
            This dashboard connects to an AI agent specialized in call transcript analysis:
            - **Agent SDK with OpenRouter** (GPT-4.1) for advanced reasoning
            - **Native MCP integration** for seamless tool access
            - **Comprehensive analysis** of 1000+ transcript chunks
            - **Real-time insights** with specific transcript IDs
            
            **Key Features:**
            - Multiple examples and concrete findings
            - Evidence-based insights with transcript references
            - Proper formatting (tables, bullet points, lists)
            - Focus on actionable results over lengthy explanations
            
            The agent automatically uses available MCP tools for transcript search, analysis, and reporting!
            """)
    
    # Main content area - Simple interface
    simple_interface()

def simple_interface():
    """Simple unified interface for API-based AI chat and tools"""
    st.subheader("AI Chat Interface")
    
    # API connection info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.api_connected:
            st.success(f"Connected to API: {api_client.base_url}")
            if api_client.bearer_token:
                st.info("Authenticated with Bearer token")
            else:
                st.info("Using public access")
        else:
            st.error(f"Cannot connect to API: {api_client.base_url}")
            st.markdown("**Check:**")
            st.markdown("- API server is running")
            st.markdown("- Environment variables are set correctly")
    
    with col2:
        if st.button("Test Connection", use_container_width=True, key="main_test_connection"):
            with st.spinner("Testing..."):
                st.session_state.api_connected = api_client.check_api_connection()
                if st.session_state.api_connected:
                    st.success("Connected!")
                else:
                    st.error("Connection Failed!")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    
    # Chat interface or quick tools
    if st.session_state.api_connected:
        # Chat interface  
        st.subheader("Chat with AmplifAI Agent (GPT-4.1 + MCP Tools)")
        
        # Display chat history
        if st.session_state.chat_history:
            chat_container = st.container()
            
            with chat_container:
                for i, message in enumerate(st.session_state.chat_history):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #6c757d;">
                            <strong>You:</strong><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 4px solid #495057;">
                            <strong>Agent:</strong><br>
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if "execution_time" in message:
                            st.caption(f"Response time: {message['execution_time']:.2f}s")
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Your message:",
                placeholder="Ask me about call transcripts! I'll analyze patterns, find examples, and provide insights with transcript IDs.",
                key="chat_input"
            )
            
            col1, col2 = st.columns([4, 1])
            with col2:
                send_button = st.form_submit_button("Send", use_container_width=True)
        
        # Handle chat message
        if send_button and user_input.strip():
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user", 
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process the query via API
            with st.spinner("AI is thinking..."):
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
                        error_message = f"Error: {result.get('error', 'Unknown error')}"
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_message,
                            "timestamp": datetime.now().isoformat(),
                            "execution_time": end_time - start_time
                        })
                    
                    st.rerun()
                    
                except Exception as e:
                    error_message = f"API Error: {str(e)}"
                    print(f"Error in API query processing: {e}")
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_message,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.error(error_message)
        
        # Quick action buttons
        st.subheader("Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Database Overview", use_container_width=True, key="quick_database"):
                quick_query("Give me an overview of the transcript database - how many transcripts are there and what can I analyze?")
        
        with col2:
            if st.button("Common Issues", use_container_width=True, key="quick_issues"):
                quick_query("What are the most common customer issues in the call transcripts? Provide examples with transcript IDs.")
        
        with col3:
            if st.button("Call Trends", use_container_width=True, key="quick_trends"):
                quick_query("Analyze call patterns and trends in the transcript data. Show me specific examples.")
        
        with col4:
            if st.button("Agent Capabilities", use_container_width=True, key="quick_help"):
                quick_query("What can you help me analyze from the call transcripts? What tools do you have available?")
        
        # Clear chat button
        if st.button("Clear Chat History", type="secondary", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    else:
        # Show simplified message when agent not connected
        st.subheader("Connect to API for Full Functionality")
        st.info("Connect the API above to enable AI chat and tools functionality.")
        
        # Basic search still available when disconnected
        st.subheader("Basic Search (When Connected)")
        search_query = st.text_input("Search Transcripts", placeholder="Enter search terms...", disabled=not st.session_state.api_connected, key="basic_search_input")
        if st.button("Search", use_container_width=True, disabled=not st.session_state.api_connected, key="basic_search_button") and search_query:
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
                                        st.error(f"Search error: {e}")

def quick_query(query: str):
    """Execute a quick query via API"""
    if not st.session_state.api_connected:
        st.error("API not connected")
        return
    
    # Add to chat history and trigger processing
    st.session_state.chat_history.append({
        "role": "user", 
        "content": query,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        with st.spinner("Processing..."):
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
                error_message = f"Error: {result.get('error', 'Unknown error')}"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": end_time - start_time
                })
            
            st.rerun()
            
    except Exception as e:
        error_message = f"API Error: {str(e)}"
        print(f"Error in quick query: {e}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": error_message,
            "timestamp": datetime.now().isoformat()
        })
        st.error(error_message)

if __name__ == "__main__":
    main()
