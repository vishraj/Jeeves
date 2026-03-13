import streamlit as st

def header_component():
    st.set_page_config(page_title="Enterprise Document AI Assistant", layout="wide")
    st.title("🏢 Enterprise Document AI Assistant")
    st.markdown("""
    Query your enterprise documents using natural language. 
    This assistant uses **Amazon Bedrock Knowledge Bases** and **Anthropic Claude**.
    """)

def sidebar_component():
    with st.sidebar:
        st.header("Settings")
        st.info("Ensure your AWS credentials are configured correctly.")
        if st.button("Clear Chat"):
            st.session_state.messages = []
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
