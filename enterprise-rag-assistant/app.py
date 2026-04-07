import streamlit as st

st.set_page_config(
    page_title="Jeeves: Enterprise AI", 
    page_icon="🔐", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
import json
import re
import uuid
import yaml
import os
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from utils.chat_store import ChatStore

from rag.knowledgebase_rag import KnowledgeBaseRAG
from ui.components import (
    header_component, 
    login_header_component,
    sidebar_component, 
    history_sidebar_component,
    citations_component, 
    chat_message_component
)
from utils.aws_clients import aws_manager
from utils.config import Config
from utils.chat_store import chat_store

def extract_visualization_data(answer_text):
    """Extract JSON from the LLM answer if a visualization is requested."""
    json_match = re.search(r'```json\n(.*?)\n```', answer_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except Exception:
            return None
    return None

def render_chart(viz_data):
    if not viz_data:
        return

    chart_type = viz_data.get("chart_type", "bar").lower()
    df = pd.DataFrame(viz_data.get("data", []))
    x = viz_data.get("x_axis")
    y = viz_data.get("y_axis")

    if df.empty:
        st.warning("No data available to visualize.")
        return

    # Fallback: if the axis labels don't match actual column names, use the first two columns
    cols = list(df.columns)
    if x not in cols:
        x = cols[0] if len(cols) > 0 else x
    if y not in cols and chart_type != "pie" and chart_type != "histogram":
        y = cols[1] if len(cols) > 1 else y

    st.subheader("📊 Visualization")

    if chart_type == "bar":
        fig = px.bar(df, x=x, y=y, title=f"{y} by {x}")
    elif chart_type == "line":
        fig = px.line(df, x=x, y=y, title=f"{y} over {x}")
    elif chart_type == "pie":
        fig = px.pie(df, names=x, values=y, title=f"Distribution of {y}")
    elif chart_type == "histogram":
        fig = px.histogram(df, x=x, title=f"Distribution of {x}")
    else:
        st.warning(f"Unsupported chart type: {chart_type}")
        return

    st.plotly_chart(fig, use_container_width=True)

def main():
    # --- Authentication Layer ---
    with open('auth/config.yaml') as file:
        config_auth = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config_auth['credentials'],
        config_auth['cookie']['name'],
        config_auth['cookie']['key'],
        config_auth['cookie']['expiry_days'],
        config_auth['preauthorized']
    )

    # We use a dedicated login page layout
    if not st.session_state.get("authentication_status"):
        login_header_component()
        
        # Centered Login Card using Native Container
        col1, col2, col3 = st.columns([3, 2, 3])
        with col2:
            with st.container(border=True):
                # Branded Logo and Title
                if os.path.exists("assets/logo.png"):
                    st.image("assets/logo.png", width=80)
                
                st.markdown("### Jeeves: Enterprise AI")
                st.markdown("Please log in to access your documents.")
                
                name, authentication_status, username = authenticator.login(location='main')
                
                if authentication_status is False:
                    st.error('Username/password is incorrect')
                elif authentication_status is None:
                    st.info('Please enter your credentials.')
            
            if not st.session_state.get("authentication_status"):
                return # Stop execution here if not logged in

    # --- Main Application (Post-Auth) ---
    header_component()
    
    user_id = st.session_state["username"] 
    user_display_name = st.session_state["name"]
    
    # Persistent RAG engine in session state 
    if "rag_engine" not in st.session_state:
        st.session_state.rag_engine = KnowledgeBaseRAG()

    # Initial session state for messages and active conversation tracking
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_store" not in st.session_state:
        st.session_state.chat_store = ChatStore()
    
    chat_store = st.session_state.chat_store
    
    if "current_conv_id" not in st.session_state:
        st.session_state.current_conv_id = None

    # --- UI Sidebar ---
    sidebar_component(authenticator, user_display_name)
    history_sidebar_component(chat_store, user_id)

    # --- Main Chat Area ---
    # Display chat history
    for msg_idx, msg in enumerate(st.session_state.messages):
        chat_message_component(msg["role"], msg["content"])
        if msg.get("viz_data"):
            render_chart(msg["viz_data"])
        if msg.get("citations"):
            citations_component(msg["citations"], msg_key=f"msg_{msg_idx}")

    # User Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # If no active conversation, create a new ID
        if st.session_state.current_conv_id is None:
            st.session_state.current_conv_id = str(uuid.uuid4())

        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_message_component("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                final_prompt = prompt

                # Call RAG with history context
                result = st.session_state.rag_engine.ask(final_prompt, history=st.session_state.messages[:-1])
                answer = result.get("answer", "No answer generated.")
                citations = result.get("citations", [])
                
                # Extract visualization data and clean answer
                viz_data = extract_visualization_data(answer)
                clean_answer = re.sub(r'```json\n.*?\n```', '', answer, flags=re.DOTALL).strip()

                st.markdown(clean_answer)
                render_chart(viz_data)
                citations_component(citations, msg_key="live")

                # Update messages in session
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_answer,
                    "citations": citations,
                    "viz_data": viz_data
                })
                
                # Persistence: Save full conversation to DynamoDB
                # The first user message is used for the title.
                current_messages = st.session_state.messages
                title = current_messages[0]["content"] if current_messages else "New Chat"
                
                if chat_store.save_conversation(
                    user_id=user_id,
                    conversation_id=st.session_state.current_conv_id,
                    title=title,
                    messages=current_messages,
                    bedrock_session_id=st.session_state.rag_engine.session_id
                ):
                    st.toast("✅ Conversation Saved", icon="💾")
                else:
                    st.error("Error saving conversation to DynamoDB.")
                    print(f"DEBUG: Save failed for user {user_id}, conv {st.session_state.current_conv_id}")
                
                # Rerun to update sidebar and sync state with DB
                st.rerun()

if __name__ == "__main__":
    Config.validate()
    main()
