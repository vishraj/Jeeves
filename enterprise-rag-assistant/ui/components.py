import streamlit as st
from datetime import datetime
import os

def header_component():
    st.set_page_config(page_title="Jeeves: Enterprise AI", layout="wide")
    
    # Hero Header with Logo
    col1, col2 = st.columns([0.1, 0.9])
    with col1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=70)
    with col2:
        st.title("Jeeves: Enterprise AI")
        
    st.markdown("""
    Query your enterprise documents using natural language. 
    This assistant uses **Amazon Bedrock Knowledge Bases** and **Anthropic Claude**.
    """)

def login_header_component():
    """Header shown on the login page specifically."""
    st.set_page_config(page_title="Login | Jeeves AI", page_icon="🔐")
    
    # Custom CSS for a professional login page
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #0e1117 0%, #111827 100%);
        }
        /* Style for the native container to make it look like a premium card */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 1.2rem !important;
            padding: 2rem;
            margin-top: 5vh;
        }
        h1, h2, h3, p {
            color: #f8fafc !important;
            text-align: center;
        }
        /* Center the logo */
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
        }
        </style>
    """, unsafe_allow_html=True)

def sidebar_component(authenticator, username):
    with st.sidebar:
        st.header("👤 Profile")
        st.write(f"Logged in as: **{username}**")
        authenticator.logout('Logout', 'main')
        
        st.divider()
        
        st.header("⚙️ Settings")
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_conv_id = None
            if "rag_engine" in st.session_state:
                st.session_state.rag_engine.reset_session()
            st.rerun()

        st.divider()

def history_sidebar_component(chat_store, user_id):
    with st.sidebar:
        st.header("💬 Chat History")
        conversations = chat_store.list_conversations(user_id)
        
        if not conversations:
            st.info("No past conversations.")
            return

        for conv in conversations:
            cols = st.columns([0.8, 0.2], vertical_alignment="center")
            conv_id = conv['conversation_id']
            title = conv.get('title', 'Untitled Chat')
            
            # Highlight active conversation
            is_active = st.session_state.get('current_conv_id') == conv_id
            btn_label = f"📄 {title[:30]}..." if len(title) > 30 else f"📄 {title}"
            
            if cols[0].button(btn_label, key=f"load_{conv_id}", use_container_width=True, 
                              type="secondary" if not is_active else "primary"):
                st.session_state.messages = conv.get('messages', [])
                st.session_state.current_conv_id = conv_id
                if "rag_engine" in st.session_state:
                    st.session_state.rag_engine.session_id = conv.get('bedrock_session_id')
                st.rerun()
            
            if cols[1].button("🗑️", key=f"del_{conv_id}", use_container_width=True, help="Delete Chat"):
                if chat_store.delete_conversation(user_id, conv_id):
                    if st.session_state.get('current_conv_id') == conv_id:
                        st.session_state.messages = []
                        st.session_state.current_conv_id = None
                    st.rerun()

def citations_component(citations, msg_key="default"):
    if not citations:
        return

    with st.expander("🔍 View Source Citations"):
        for idx, citation in enumerate(citations):
            st.markdown(f"**Source {idx + 1}:** {citation['source']}")
            st.caption(f"URI: {citation['uri']}")
            unique_key = f"citation_{msg_key}_{idx}"
            st.text_area(f"Relevant Excerpt {idx+1}", value=citation['text'], height=100, disabled=True, key=unique_key)
            st.divider()

def chat_message_component(role, content):
    with st.chat_message(role):
        st.markdown(content)
