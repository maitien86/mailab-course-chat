import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"
TERM_START_DATE = datetime(2026, 1, 5)  # Term 2 Start: Monday, Jan 5, 2026

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

def load_syllabus():
    try:
        with open("syllabus.txt", "r", encoding="utf-8") as f:
            content = f.read()
            version = content.split('\n')[0].replace('###', '').strip()
            return content, version
    except FileNotFoundError:
        return "You are an assistant for IS115.", "v0.0"

SYLLABUS_CONTENT, VERSION_ID = load_syllabus()
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYLLABUS_CONTENT)

# --- 3. UI STYLING (BLUE BACKGROUND & WHITE TEXT) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* 1. Main App Background - Deep Blue */
        .stApp {
            background-color: #002349 !important;
        }
        
        /* 2. Sidebar Styling - Darker Navy Blue */
        [data-testid="stSidebar"] {
            background-color: #001529 !important;
            border-right: 1px solid #1E3A8A;
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* 3. Chat Bubbles - Medium Blue with White Text */
        [data-testid="stChatMessage"] {
            background-color: #1E3A8A !important;
            border: 1px solid #3B82F6 !important;
            border-radius: 12px !important;
            margin-bottom: 12px !important;
        }

        /* 4. FORCE WHITE TEXT COLOR */
        [data-testid="stChatMessageContent"] p, 
        [data-testid="stChatMessageContent"] li, 
        [data-testid="stChatMessageContent"] span,
        [data-testid="stChatMessageContent"] code,
        [data-testid="stChatMessageContent"] div {
            color: #FFFFFF !important; 
            font-weight: 400 !important;
        }

        /* 5. Header Colors */
        h1, h2, h3, .main-header {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        /* 6. Progress Bar Color Fix */
        .stProgress > div > div > div > div {
            background-color: #3B82F6 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & PROGRESS TRACKER ---
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

# Calculate Progress
def get_course_progress():
    today = datetime.now()
    days_passed = (today - TERM_START_DATE).days
    current_week = max(1, min(13, (days_passed // 7) + 1))
    progress_percent = min(100, int((current_week / 13) * 100))
    return current_week, progress_percent

current_week, progress_val = get_course_progress()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=180)
    st.markdown("---")
    
    # Progress Tracker
    st.subheader(f"📅 Week {current_week} of 13")
    st.progress(progress_val / 100)
    st.caption(f"Course Completion: {progress_val}%")
    
    st.markdown("---")
    st.metric("Questions This Session", st.session_state.request_count)
    st.info(f"**IS115 Sections:** G1, G2, G3, G4")
    st.write(f"Instructor: Prof. Mai Anh Tien")
    st.write(f"Version: {VERSION_ID}")
    
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=70)
with col2:
    st.markdown("<h1 class='main-header'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            history = [{"role": "model" if m["role"] == "assistant" else "user", 
                        "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {str(e)}")
