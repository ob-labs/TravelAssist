"""
Streamlit UI for OBMMS Travel Assistant.

Provides an interactive web interface for travel planning
with a chat interface and map visualization.
"""

import sys
from pathlib import Path

# Ensure project root is on Python path (ui.py lives under src/frontend/)
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import logging
import streamlit as st
import pandas as pd

from src.agents import TravelWorkflow
from src.common import get_config
from src.common.constants import CITYDATA_DIR, UPLOAD_DIR
from src.common.geo import DEFAULT_LAT, DEFAULT_LONG
from src.common.logger import get_logger

from src.data.data_loader import (
    save_uploaded_file,
    load_dataset_from_archive,
)

# Setup logger
logger = get_logger(__name__)

# Page configuration: use ob-icon.png as browser favicon
_ICON_PATH = Path(__file__).resolve().parent / "images" / "ob-icon.png"
st.set_page_config(
    page_title="旅行规划助手",
    page_icon=str(_ICON_PATH) if _ICON_PATH.exists() else "🌏",
    layout="wide",
)
UI_LOGO_PATH = Path(__file__).resolve().parent / "images" / "logo.png"


# Avatar configuration
AVATARS = {
    "assistant": "🌏",
    "user": "🧑‍💻",
}

def initialize_session_state():
    """Initialize Streamlit session state variables."""

    # Ensure directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    if "messages" not in st.session_state:
        logger.info("[UI] Initializing new session")
        st.session_state["messages"] = []

    if "lats" not in st.session_state:
        st.session_state["lats"] = [DEFAULT_LAT]

    if "longs" not in st.session_state:
        st.session_state["longs"] = [DEFAULT_LONG]

    if "agents" not in st.session_state:
        logger.info("[UI] Creating TravelWorkflow instance...")
        st.session_state["agents"] = TravelWorkflow()
        logger.info("[UI] TravelWorkflow created successfully")


def generate_stream_response(streamer, message_buffer: list):
    """
    Generator for streaming response content.

    Args:
        streamer: The LLM response streamer.
        message_buffer: List to accumulate message content.

    Yields:
        Response content chunks.
    """
    for response in streamer:
        content = response.output.choices[0].message.content
        message_buffer.append(content)
        yield content

def render_sidebar():
    """
    Render the sidebar (data management, upload, dataset selection).
    """
    with st.sidebar:
        st.title("🔧 Data Management")
        st.logo(UI_LOGO_PATH)

        st.subheader("📤 Upload Dataset")

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload dataset archive",
            type=["zip", "tar", "gz", "bz2", "xz"],
            help="Download from Kaggle: china-city-attraction-details",
        )

        # Save uploaded file
        if uploaded_file:
            saved_path = save_uploaded_file(uploaded_file, UPLOAD_DIR)
            if saved_path:
                st.success(f"✓ Uploaded: {uploaded_file.name}")

        # List available archives
        uploaded_files = list(UPLOAD_DIR.glob("*"))

        if uploaded_files:
            st.subheader("📦 Available Datasets")

            selected_file = st.selectbox(
                "Select dataset to load",
                options=[f.name for f in uploaded_files],
                key="dataset_selector",
            )

            if st.button("🚀 Load Data", type="primary", use_container_width=True):
                selected_path = UPLOAD_DIR / selected_file

                success = load_dataset_from_archive(selected_path, CITYDATA_DIR)

                if success:
                    st.success("✅ Data loaded successfully!")
                    st.balloons()
                    st.rerun()

            st.info("⏱️ Data loading takes 30-60 minutes")
        

        st.divider()
        
        # 显示已加载的数据集文件列表
        loaded_files = list(CITYDATA_DIR.glob("*"))
        if loaded_files:
            st.subheader("📚 已加载的数据集")
            for f in loaded_files:
                st.markdown(f"- {f.name}")

        with st.expander("📖 How to get dataset"):
            st.markdown("""
            1. Visit [Kaggle](https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details)
            2. Download the dataset
            3. Upload here
            """)

        st.caption("TravelAssist v1.0")


def render_top_info():
    """
    Render the top information.
    """
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown(
            """
            <div style="margin-left: 8px;">
            <b>👋 欢迎使用 OB 文旅助手 Demo, 根据您提供的以下信息为您推荐景点：</b>
            <ul>
                <li>1. 旅行起始地</li>
                <li>2. 行程范围</li>
                <li>3. 景点评分（100分制）</li>
                <li>4. 出行季节</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            """
            <div style="margin-left: 8px;">
            <b>例如，您可以试着问我：</b>
            <ul>
                <li>春天去杭州，西湖附近10公里内评分超过90分的景点推荐</li>
                <li>秋天去北京，在颐和园附近20公里范围内评分超过80分的景点有哪些</li>
                <li>冬天去大连，星海广场附近20公里范围内评分超过80分的景点推荐</li>
                <li>夏天去成都，太古里附近10公里内评分超过90分的景点推荐</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
                
def render_map(col):
    """
    Render the map visualization.

    Args:
        col: Streamlit column to render in.
    """
    with col:
        st.header("景点地图")
        map_data = pd.DataFrame({
            "latitude": st.session_state["lats"],
            "longitude": st.session_state["longs"],
        })
        st.map(map_data)
        
        


def render_chat(col):
    """
    Render the chat interface.

    Args:
        col: Streamlit column to render in.
    """
    with col:
        st.header("旅行咨询")
        
        # Chat input
        user_input = st.chat_input("输入你的消息...")

        # Chat history container
        with st.container(height=600):
            # Display existing messages
            for message in st.session_state.messages:
                avatar = AVATARS[message["role"]]
                with st.chat_message(message["role"], avatar=avatar):
                    # Check if message has status information
                    if message["role"] == "assistant" and "status_messages" in message:
                        # Display status messages
                        with st.expander("📋 工作流执行详情", expanded=False):
                            for msg in message["status_messages"]:
                                st.markdown(f"- {msg}")
                    
                    # Display main content
                    if message["content"]:
                        st.write(message["content"])

            # Process new input
            if user_input is not None:
                logger.info(f"[UI] User input received: {user_input[:100]}...")
                
                # Display user message
                st.chat_message("user", avatar=AVATARS["user"]).write(user_input)

                # Get workflow response
                logger.info("[UI] Calling workflow...")
                message_buffer = []
                streamer, workflow_response = st.session_state["agents"].run(
                    user_content=user_input
                )
                logger.info("[UI] Workflow response received")
                logger.info(f"[UI] Status messages count: {len(workflow_response.status_messages)}")
                if workflow_response.status_messages:
                    logger.info(f"[UI] Status messages: {workflow_response.status_messages}")

                # Display status messages from workflow execution
                if workflow_response.status_messages:
                    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
                        with st.expander("📋 工作流执行详情", expanded=True):
                            for msg in workflow_response.status_messages:
                                st.markdown(f"- {msg}")

                # Stream assistant response
                if streamer is not None:
                    st.chat_message("assistant", avatar=AVATARS["assistant"]).write_stream(
                        generate_stream_response(streamer, message_buffer)
                    )
                else:
                    # No streaming - check if this is a success (plan completed) or error
                    if workflow_response.success and (workflow_response.lats and workflow_response.longs):
                        # Successfully found attractions
                        success_msg = f"✅ 已为您找到 {len(workflow_response.lats)} 个景点，请在左侧地图查看位置。"
                        st.chat_message("assistant", avatar=AVATARS["assistant"]).write(success_msg)
                        message_buffer.append(success_msg)
                    else:
                        # Display error
                        error_msg = workflow_response.reply if workflow_response.reply else "处理出错"
                        st.chat_message("assistant", avatar=AVATARS["assistant"]).write(error_msg)
                        message_buffer.append(error_msg)

                # Update map coordinates
                if workflow_response.lats and workflow_response.longs:
                    logger.info(f"[UI] Updating map with {len(workflow_response.lats)} coordinates")
                    st.session_state["lats"] = workflow_response.lats
                    st.session_state["longs"] = workflow_response.longs

                # Save messages to history
                st.session_state.messages.append({
                    "role": "user",
                    "content": user_input,
                })
                
                # Save assistant message with status information
                assistant_message = {
                    "role": "assistant",
                    "content": "".join(message_buffer),
                }
                
                # Include status messages if available
                if workflow_response.status_messages:
                    assistant_message["status_messages"] = workflow_response.status_messages
                
                st.session_state.messages.append(assistant_message)
                logger.info(f"[UI] Message history updated, total: {len(st.session_state.messages)}")

                # # Reset if needed
                # if workflow_response.need_reset:
                #     logger.info("[UI] Resetting conversation")
                #     st.session_state.messages = []

                # Rerun to update map
                st.rerun()


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    render_sidebar()
    render_top_info()

    # Create two-column layout
    col_map, col_chat = st.columns([1, 1])
    # Render components
    render_map(col_map)
    render_chat(col_chat)


if __name__ == "__main__":
    main()
