import streamlit as st
import google.generativeai as genai

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY. Please add it to Streamlit Secrets.")
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

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. FORCEFUL UI STYLING (FIXES WHITE-ON-WHITE) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* Force App Background to Slate Grey */
        .stApp {
            background-color: #E5E7EB !important;
        }
        
        /* Force Sidebar to SMU Deep Blue */
        [data-testid="stSidebar"] {
            background-color: #002349 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Force Chat Bubbles to White */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF !important;
            border: 2px solid #D1D5DB !important;
            border-radius: 12px !important;
        }

        /* FORCE DARK TEXT COLOR - This is the most important part */
        [data-testid="stChatMessageContent"] p, 
        [data-testid="stChatMessageContent"] li,
        [data-testid="stChatMessageContent"] span {
            color: #111827 !important; 
            font-weight: 500 !important;
        }

        /* Header Color */
        h1, h2, h3 {
            color: #002349 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & LOGOS ---
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=200)
    st.markdown("---")
    st.metric("Total Questions Asked", st.session_state.request_count)
    st.info(f"**Course:** IS115 Algorithms & Programming\\n\\n**Sections:** G1, G2, G3, G4")
    st.write(f"Instructor: Prof. Mai Anh Tien")
    st.write(f"Version: {VERSION_ID}")
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
with col2:
    st.markdown("<h1>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)
    st.caption("Official AI Teaching Assistant for Sections G1-G4")

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
