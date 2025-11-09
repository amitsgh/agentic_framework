"""Chat Interface"""

import sys
from pathlib import Path
import requests
import streamlit as st

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.parser.factory import get_parser_instance  # type: ignore
from app.core.config import config
from ui.services.document_service import upload_document, delete_all_documents
from ui.services.chat_service import chat_stream

st.set_page_config(
    page_title="Document Q&A Chat",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
    }
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
    }
    .upload-section h3 {
        color: white;
        margin-bottom: 1rem;
    }
    .sidebar .stButton>button {
        width: 100%;
        background-color: #ff4444;
        color: white;
        border: none;
    }
    .sidebar .stButton>button:hover {
        background-color: #cc0000;
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


def main():
    """Main logic"""

    init_session_state()

    st.title("Document Q&A Chat")
    st.markdown(
        "<p style='text-align: center; font-size: 1.1em; color: #666; margin-bottom: 2rem;'>"
        "Upload documents and ask questions about them</p>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Document Management")

        supported_extension = get_parser_instance().supported_extension()
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=supported_extension,
            help=f"Supported formats: {', '.join(supported_extension)}",
            key="file_uploader",
        )

        if uploaded_file is not None:
            if uploaded_file.name not in st.session_state.uploaded_files:
                with st.spinner("Uploading document..."):
                    uploaded_file.seek(0)
                    try:
                        response = upload_document(uploaded_file)

                        if isinstance(response, dict):
                            st.success(f"{uploaded_file.name} uploaded successfully!")
                            st.session_state.uploaded_files.append(uploaded_file.name)
                            st.session_state.file_uploader = (
                                None  # Clear the file uploader
                            )
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {response}")

                    except requests.RequestException as e:
                        st.error(f"Upload failed: {e}")

        st.markdown("---")

        if st.session_state.uploaded_files:
            st.subheader("Uploaded Documents")
            for file_name in st.session_state.uploaded_files:
                st.text(file_name)

        st.markdown("---")

        if st.button(
            "Delete All Documents", type="secondary", use_container_width=True
        ):
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
                    st.error(f"Delete failed: {e}")

        st.markdown("---")
        st.markdown(
            "<p style='font-size: 0.9em; color: #888; text-align: center;'>"
            "Tip: Upload documents first, then ask questions about them in the chat!</p>",
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                for chunk in chat_stream(prompt):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

            except Exception as e:
                error_message = f"Error: {str(e)}"
                message_placeholder.error(error_message)
                full_response = error_message

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


if __name__ == "__main__":
    main()
