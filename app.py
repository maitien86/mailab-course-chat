import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 1. SETTINGS & ACADEMIC CALENDAR ---
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

# --- 3. FORCEFUL UI STYLING (BLACK BACKGROUND / WHITE TEXT) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* 1. Force Main App Background to Black */
        .stApp {
            background-color: #000000 !important;
        }
        
        /* 2. Force Sidebar Background */
        [data-testid="stSidebar"] {
            background-color: #111111 !important;
            border-right: 1px solid #333333;
        }

        /* 3. Force Chat Bubbles to Dark Grey/Black */
        [data-testid="stChatMessage"] {
            background-color: #1A1A1A !important;
            border: 1px solid #444444 !important;
            border-radius: 12px !important;
        }

        /* 4. CRITICAL: Force ALL Text to White (Overrides Light Mode) */
        [data-testid="stChatMessageContent"] p, 
        [data-testid="stChatMessageContent"] li, 
        [data-testid="stChatMessageContent"] span,
        [data-testid="stChatMessageContent"] code,
        [data-testid="stChatMessageContent"] div,
        .stMarkdown, p, label, .stCaption {
            color: #FFFFFF !important; 
            font-weight: 400 !important;
        }

        /* 5. Header Colors */
        h1, h2, h3, .main-header {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        /* 6. Sidebar Text Color */
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* 7. Input Box Styling */
        .stChatInputContainer textarea {
            color: #FFFFFF !important;
            background-color: #222222 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & PROFESSOR INFO ---
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
    # SMU Branding
    st.image("https://vms.smu.edu.sg/images/Logo/smu-logo.png", width=180)
    
    st.markdown("---")
    st.subheader("👨‍🏫 Instructor Profile")
    st.markdown("""
    **Prof. Mai Anh Tien** Assistant Professor of Information Systems  
    *School of Computing and Information Systems* **Singapore Management University**
    
     
    **Email:** [atmai@smu.edu.sg](mailto:atmai@smu.edu.sg)
    **Telegram:** @Tienmai
    """)
    
    st.markdown("---")
    # Progress Tracker
    st.subheader(f"📅 Week {current_week} of 13")
    st.progress(progress_val / 100)
    
    st.markdown("---")
    st.metric("Total Questions Asked", st.session_state.request_count)
    st.write(f"Syllabus Version: {VERSION_ID}")
    
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

# Beta Version Notice
st.info("🚀 **BETA VERSION:** This is an experimental AI Teaching Assistant. If you encounter any issues, please contact Prof. Mai Anh Tien or your section TA.")

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Logic
if prompt := st.chat_input("Ask a question about algorithms..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Alternating history for Gemini
            history = [{"role": "model" if m["role"] == "assistant" else "user", 
                        "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {str(e)}")
