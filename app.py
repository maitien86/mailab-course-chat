import streamlit as st
import google.generativeai as genai

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

# Securely fetch API Key
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# Load syllabus.txt and version ID
def load_syllabus():
    try:
        with open("syllabus.txt", "r", encoding="utf-8") as f:
            content = f.read()
            version = content.split('\n')[0].replace('###', '').strip()
            return content, version
    except FileNotFoundError:
        return "You are an assistant for IS115.", "v0.0"

SYLLABUS_CONTENT, VERSION_ID = load_syllabus()

# Initialize Model with Master Syllabus
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. UI STYLING (SMU THEME & DARK TEXT) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* Main App Background */
        .stApp {
            background-color: #F0F2F6;
        }
        
        /* Sidebar Styling (SMU Deep Blue) */
        [data-testid="stSidebar"] {
            background-color: #002349;
            color: white;
        }

        /* Chat Bubbles Styling */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF;
            border: 1px solid #D1D5DB;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* Force Dark Text for Readability */
        [data-testid="stChatMessageContent"] p {
            color: #111827 !important;
            font-size: 1.05rem;
            font-weight: 450;
        }

        /* Header Text Shadow */
        .main-header {
            color: #002349;
            font-weight: 800;
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
    # SMU LOGO - Using official SMU colors/branding
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=200)
    
    st.markdown("---")
    st.header("Admin Dashboard")
    st.metric("Total Questions Asked", st.session_state.request_count)
    
    st.info(f"**Course:** IS115 Algorithms & Programming\n\n**Sections:** G1, G2, G3, G4")
    
    st.markdown("---")
    st.write(f"**Instructor:** Prof. Mai Anh Tien")
    st.write(f"**Version:** {VERSION_ID}")
    
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
# Course Branding at the Top
col1, col2 = st.columns([1, 4])
with col1:
    # Course Logo/Icon
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
with col2:
    st.markdown("<h1 class='main-header'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)
    st.caption("Official AI Teaching Assistant for Sections G1-G4 | Powered by MaiLab")

st.warning("🚀 **BETA NOTICE**: If the bot provides incorrect admin info, refer to the official eLearn syllabus or contact Prof. Mai Anh Tien.")

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt logic
if prompt := st.chat_input("Ask a question about algorithms, data structures, or course policies..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Format history for Gemini
            formatted_history = []
            for m in st.session_state.messages[:-1]:
                role = "model" if m["role"] == "assistant" else "user"
                formatted_history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(prompt)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            st.error(f"Error: {str(e)}")
