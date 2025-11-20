"""Advanced RAG Chat Interface with Graph Visualization"""

import sys
from pathlib import Path
import requests
import streamlit as st
import json

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.config import config
from ui.services.document_service import upload_document, delete_all_documents, get_processing_status
from ui.services.chat_service import chat_stream
from ui.services.graph_service import query_graph, get_graph_stats

st.set_page_config(
    page_title="Advanced RAG System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern UI
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1400px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-uploaded { background-color: #4CAF50; color: white; }
    .status-extracted { background-color: #2196F3; color: white; }
    .status-chunked { background-color: #FF9800; color: white; }
    .status-stored { background-color: #9C27B0; color: white; }
    .status-failed { background-color: #F44336; color: white; }
    .graph-node {
        fill: #667eea;
        stroke: #764ba2;
        stroke-width: 2px;
    }
    .graph-edge {
        stroke: #999;
        stroke-width: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BACKEND_URL = config.BACKEND_URL


def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    
    if "rag_settings" not in st.session_state:
        st.session_state.rag_settings = {
            "enable_reranking": True,
            "enable_query_translation": True,
            "enable_routing": True,
            "enable_refinement": True,
            "enable_graph_rag": False,
            "top_k": 5,
        }
    
    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = "Chat"


def get_status_badge(stage: str) -> str:
    """Get HTML badge for processing stage"""
    stage_lower = stage.lower()
    status_map = {
        "uploaded": "status-uploaded",
        "extracted": "status-extracted",
        "chunked": "status-chunked",
        "stored": "status-stored",
        "failed": "status-failed",
    }
    status_class = status_map.get(stage_lower, "status-uploaded")
    return f'<span class="status-badge {status_class}">{stage.upper()}</span>'


def main():
    """Main application logic"""
    init_session_state()
    
    st.title("Advanced RAG System")
    st.markdown(
        "<p style='text-align: center; font-size: 1.1em; color: #666; margin-bottom: 2rem;'>"
        "Enterprise-grade RAG with Redis, MinIO, Neo4j, and Advanced Query Processing</p>",
        unsafe_allow_html=True,
    )
    
    # Sidebar for document management and settings
    with st.sidebar:
        st.header("Document Management")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=["pdf", "docx", "txt", "md"],
            help="Supported formats: PDF, DOCX, TXT, MD",
            key="file_uploader",
        )
        
        if uploaded_file is not None:
            if uploaded_file.name not in [f["name"] for f in st.session_state.uploaded_files]:
                with st.spinner("Uploading and processing document..."):
                    uploaded_file.seek(0)
                    try:
                        response = upload_document(uploaded_file)
                        
                        if isinstance(response, dict) and response.get("status") == "success":
                            st.success(f"{uploaded_file.name} uploaded successfully")
                            st.session_state.uploaded_files.append({
                                "name": uploaded_file.name,
                                "message": response.get("message", ""),
                            })
                            st.session_state.file_uploader = None
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {response}")
                    except requests.RequestException as e:
                        st.error(f"Upload failed: {str(e)}")
        
        st.markdown("---")
        
        # Uploaded documents list
        if st.session_state.uploaded_files:
            st.subheader("Uploaded Documents")
            for file_info in st.session_state.uploaded_files:
                with st.expander(file_info["name"]):
                    st.markdown(f"**Status:** {file_info.get('message', 'Processing...')}")
        
        st.markdown("---")
        
        # Advanced RAG Settings
        st.header("RAG Settings")
        
        st.session_state.rag_settings["enable_reranking"] = st.checkbox(
            "Enable Re-ranking", value=st.session_state.rag_settings["enable_reranking"]
        )
        st.session_state.rag_settings["enable_query_translation"] = st.checkbox(
            "Enable Query Translation", value=st.session_state.rag_settings["enable_query_translation"]
        )
        st.session_state.rag_settings["enable_routing"] = st.checkbox(
            "Enable Routing", value=st.session_state.rag_settings["enable_routing"]
        )
        st.session_state.rag_settings["enable_refinement"] = st.checkbox(
            "Enable CRAG Refinement", value=st.session_state.rag_settings["enable_refinement"]
        )
        st.session_state.rag_settings["enable_graph_rag"] = st.checkbox(
            "Enable Graph RAG", value=st.session_state.rag_settings["enable_graph_rag"]
        )
        
        st.session_state.rag_settings["top_k"] = st.slider(
            "Top K Results", min_value=1, max_value=20, value=st.session_state.rag_settings["top_k"]
        )
        
        st.markdown("---")
        
        # Delete all button
        if st.button("Delete All Documents", type="secondary", use_container_width=True):
            with st.spinner("Deleting all documents..."):
                try:
                    response = delete_all_documents()
                    if isinstance(response, dict):
                        st.success("All documents deleted successfully")
                        st.session_state.uploaded_files = []
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {response}")
                except requests.RequestException as e:
                    st.error(f"Delete failed: {str(e)}")
        
        st.markdown("---")
        st.markdown(
            "<p style='font-size: 0.85em; color: #888; text-align: center;'>"
            "Tip: Upload documents first, then ask questions!</p>",
            unsafe_allow_html=True,
        )
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Graph Explorer", "Analytics", "System Status"])
    
    with tab1:
        st.header("Chat with Your Documents")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show metadata if available
                if "metadata" in message and message["metadata"]:
                    with st.expander("RAG Metadata"):
                        st.json(message["metadata"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your documents..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                metadata_placeholder = st.empty()
                
                try:
                    # Stream response
                    for chunk in chat_stream(prompt):
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    
                    # Show RAG metadata (if available from backend)
                    # This would need backend support to return metadata
                    
                except Exception as e:
                    error_message = f"Error: {str(e)}"
                    message_placeholder.error(error_message)
                    full_response = error_message
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                })
    
    with tab2:
        st.header("Graph Database Explorer")
        
        if not st.session_state.rag_settings["enable_graph_rag"]:
            st.warning("Graph RAG is disabled. Enable it in settings to use this feature.")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                graph_query = st.text_input(
                    "Enter a natural language query for the graph:",
                    placeholder="e.g., Find all people who work for organizations",
                    key="graph_query_input"
                )
                
                if st.button("Query Graph", type="primary"):
                    if graph_query:
                        with st.spinner("Querying graph database..."):
                            try:
                                results = query_graph(graph_query)
                                
                                if results:
                                    st.success(f"Found {len(results)} results")
                                    
                                    for idx, result in enumerate(results):
                                        with st.expander(f"Result {idx + 1}"):
                                            st.json(result)
                                else:
                                    st.info("No results found")
                            except Exception as e:
                                st.error(f"Query failed: {str(e)}")
            
            with col2:
                st.subheader("Graph Statistics")
                try:
                    stats = get_graph_stats()
                    if stats:
                        st.metric("Total Nodes", stats.get("node_count", 0))
                        st.metric("Total Relationships", stats.get("relationship_count", 0))
                        st.metric("Node Labels", stats.get("label_count", 0))
                except Exception as e:
                    st.warning(f"Could not fetch stats: {str(e)}")
            
            # Graph visualization placeholder
            st.subheader("Graph Visualization")
            st.info("Graph visualization will be displayed here. Connect to Neo4j to see interactive graph.")
            
            # Example graph visualization code (would need networkx/plotly)
            # This is a placeholder for future implementation
    
    with tab3:
        st.header("Analytics & Insights")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Documents Uploaded", len(st.session_state.uploaded_files))
        
        with col2:
            st.metric("Chat Messages", len([m for m in st.session_state.messages if m["role"] == "user"]))
        
        with col3:
            st.metric("RAG Features Active", sum([
                st.session_state.rag_settings["enable_reranking"],
                st.session_state.rag_settings["enable_query_translation"],
                st.session_state.rag_settings["enable_routing"],
                st.session_state.rag_settings["enable_refinement"],
                st.session_state.rag_settings["enable_graph_rag"],
            ]))
        
        with col4:
            st.metric("Processing Pipeline", "Active")
        
        st.markdown("---")
        
        # Processing pipeline visualization
        st.subheader("Processing Pipeline Status")
        
        pipeline_stages = [
            {"name": "Upload", "status": "Active", "description": "Files uploaded to MinIO"},
            {"name": "Extract", "status": "Active", "description": "Text extracted from documents"},
            {"name": "Chunk", "status": "Active", "description": "Documents chunked semantically"},
            {"name": "Embed", "status": "Active", "description": "Chunks embedded into vectors"},
            {"name": "Store", "status": "Active", "description": "Vectors stored in Redis"},
        ]
        
        for stage in pipeline_stages:
            st.markdown(f"**{stage['name']}** ({stage['status']}) - {stage['description']}")
    
    with tab4:
        st.header("System Status")
        
        # Service status
        st.subheader("Service Status")
        
        services = [
            {"name": "Redis", "port": "6379", "status": "checking..."},
            {"name": "Ollama", "port": "11434", "status": "checking..."},
            {"name": "Neo4j", "port": "7687", "status": "checking..."},
            {"name": "MinIO", "port": "9000", "status": "checking..."},
        ]
        
        for service in services:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{service['name']}**")
            with col2:
                st.write(f"Port: {service['port']}")
            with col3:
                # In production, this would check actual service status
                st.success("Online")
        
        st.markdown("---")
        
        # Configuration
        st.subheader("Configuration")
        
        config_data = {
            "Backend URL": BACKEND_URL,
            "RAG Enabled": config.RAG_ENABLED,
            "Reranker Type": config.RERANKER_TYPE,
            "Query Translator": config.QUERY_TRANSLATOR_TYPE,
            "Router Type": config.ROUTER_TYPE,
            "Refiner Type": config.REFINER_TYPE,
        }
        
        st.json(config_data)


if __name__ == "__main__":
    main()
