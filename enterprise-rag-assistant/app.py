import streamlit as st
import pandas as pd
import plotly.express as px
import json
import re
from rag.knowledgebase_rag import KnowledgeBaseRAG
from ui.components import header_component, sidebar_component, citations_component, chat_message_component
from utils.aws_clients import aws_manager
from utils.config import Config

# Initialize RAG Engine
rag_engine = KnowledgeBaseRAG()

def extract_visualization_data(answer_text):
    """
    Experimental function to extract JSON from the LLM answer if a visualization is requested.
    This pattern uses Claude to structure data into JSON.
    """
    # Look for JSON pattern in the text
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
    header_component()
    sidebar_component()

    # Initial session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # New Conversation button — resets chat history and Bedrock session context
    if st.sidebar.button("🔄 New Conversation", use_container_width=True):
        st.session_state.messages = []
        rag_engine.reset_session()
        st.rerun()

    # Display chat history
    for msg_idx, msg in enumerate(st.session_state.messages):
        chat_message_component(msg["role"], msg["content"])
        if msg.get("viz_data"):
            render_chart(msg["viz_data"])
        if msg.get("citations"):
            citations_component(msg["citations"], msg_key=f"msg_{msg_idx}")

    # User Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_message_component("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                # 1. Check if visualization is requested to adjust prompt logic
                # For this educational demo, we'll append a instruction if keywords are found
                final_prompt = prompt
                viz_keywords = ["chart", "plot", "graph", "visualize", "distribution", "trend"]
                if any(k in prompt.lower() for k in viz_keywords):
                    final_prompt += (
                        "\n\nIf you find structured data suitable for visualization, please also provide it "
                        "in the following JSON format inside a code block. "
                        "IMPORTANT: the keys inside each object in 'data' MUST exactly match the values of 'x_axis' and 'y_axis'.\n"
                        "```json\n"
                        "{\"chart_type\": \"bar|line|pie|histogram\", "
                        "\"x_axis\": \"<label for x>\", "
                        "\"y_axis\": \"<label for y>\", "
                        "\"data\": [{\"<label for x>\": \"Item A\", \"<label for y>\": 42}]}\n"
                        "```"
                    )

                # 2. Call RAG
                result = rag_engine.ask(final_prompt)
                answer = result.get("answer", "No answer generated.")
                citations = result.get("citations", [])

                # 3. Extract visualization if present
                viz_data = extract_visualization_data(answer)
                
                # Clean up answer if it contains the raw JSON block (optional)
                clean_answer = re.sub(r'```json\n.*?\n```', '', answer, flags=re.DOTALL).strip()

                st.markdown(clean_answer)
                render_chart(viz_data)
                citations_component(citations, msg_key="live")

                # Store history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": clean_answer,
                    "citations": citations,
                    "viz_data": viz_data
                })

if __name__ == "__main__":
    Config.validate()
    main()
