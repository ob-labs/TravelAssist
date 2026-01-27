import streamlit as st
import pandas as pd
from obmms import AgentFlow
import dotenv
from pathlib import Path

from data_loader import (
    save_uploaded_file,
    load_dataset_from_archive,
)

dotenv.load_dotenv()

st.set_page_config(
    page_title="旅行规划助手",
    layout="wide"
)

# ==================== Path Configuration ====================
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
CITYDATA_DIR = BASE_DIR / "citydata"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Sidebar: Data Management ====================
with st.sidebar:
    st.title("🔧 Data Management")
    
    st.subheader("📤 Upload Dataset")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload dataset archive",
        type=["zip", "tar", "gz", "bz2", "xz"],
        help="Download from Kaggle: china-city-attraction-details"
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
            key="dataset_selector"
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
    
    with st.expander("📖 How to get dataset"):
        st.markdown("""
        1. Visit [Kaggle](https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details)
        2. Download the dataset
        3. Upload here
        """)
    
    st.caption("TravelAssist v1.0")


# ==================== Initialize Session State ====================
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "lats" not in st.session_state:
    st.session_state["lats"] = [39.9042]

if "longs" not in st.session_state:
    st.session_state["longs"] = [116.4074]

if "agents" not in st.session_state:
    st.session_state["agents"] = AgentFlow(
        table_name="obmms_demo",
        topk=20,
        enable_stream=True,
    )


# ==================== UI Layout ====================
col1, col2 = st.columns([1, 1])

with col1:
    st.header("景点地图")
    data = pd.DataFrame({
        'latitude': st.session_state["lats"],
        'longitude': st.session_state["longs"],
    })
    st.map(data)


def gen_stream_resp(resp, msg):
    """Generate streaming response"""
    for res in resp:
        msg.append(res.output.choices[0].message.content)
        yield res.output.choices[0].message.content


avatar_m = {
    "assistant": "🌏",
    "user": "🧑‍💻",
}

with col2:
    st.header("旅行咨询")
    prompt = st.chat_input("输入你的消息...")
    
    with st.container(height=600):
        for msg in st.session_state.messages:
            st.chat_message(msg["role"], avatar=avatar_m[msg["role"]]).write(msg["content"])

        msg = []
        if prompt is not None:
            st.chat_message("user", avatar=avatar_m["user"]).write(prompt)
            
            resp, geo, _, _, _, _ = st.session_state["agents"].chat(user_content=prompt)
            st.chat_message("assistant", avatar=avatar_m["assistant"]).write_stream(
                gen_stream_resp(resp, msg)
            )

            if geo is not None:
                st.session_state["lats"] = [p[0] for p in geo]
                st.session_state["longs"] = [p[1] for p in geo]
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": ''.join(msg)})

            st.rerun()
