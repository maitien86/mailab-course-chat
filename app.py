import streamlit as st
import google.generativeai as genai

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

# Securely fetch API Key from Streamlit Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY. Please add it to Streamlit Secrets.")
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

# Initialize Model with Master Syllabus [cite: 7]
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. FORCEFUL UI STYLING (FIXES ALL TEXT VISIBILITY) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* 1. Main App Background - Slate Grey */
        .stApp {
            background-color: #EDF1F7 !important;
        }
        
        /* 2. Sidebar Styling - SMU Deep Blue [cite: 25] */
        [data-testid="stSidebar"] {
            background-color: #002349 !important;
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* 3. Chat Bubbles - Forced White Background */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 12px !important;
            margin-bottom: 12px !important;
        }

        /* 4. TOTAL TEXT OVERRIDE - Forced Dark Charcoal */
        /* Targets every possible text element inside the chat */
        [data-testid="stChatMessageContent"] p, 
        [data-testid="stChatMessageContent"] li, 
        [data-testid="stChatMessageContent"] ul, 
        [data-testid="stChatMessageContent"] ol,
        [data-testid="stChatMessageContent"] span,
        [data-testid="stChatMessageContent"] code,
        [data-testid="stChatMessageContent"] div {
            color: #1A1C1E !important; 
            font-weight: 500 !important;
            line-height: 1.6 !important;
        }

        /* 5. Header & Subheader Colors */
        h1, h2, h3, .main-header {
            color: #002349 !important;
            font-weight: 800 !important;
        }

        /* 6. Input Box Visibility */
        .stChatInputContainer textarea {
            color: #1A1C1E !important;
            background-color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & BRANDING ---
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    # Official SMU Branding [cite: 3, 4]
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=200)
    st.markdown("---")
    st.header("Admin Dashboard")
    st.metric("Total Questions Asked", st.session_state.request_count)
    st.info(f"**Course:** IS115 Algorithms & Programming\\n\\n**Sections:** G1, G2, G3, G4 [cite: 26-33]")
    st.markdown("---")
    st.write(f"Instructor: Prof. Mai Anh Tien [cite: 403]")
    st.write(f"Syllabus Version: {VERSION_ID}")
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
# Course Identity Header [cite: 7, 8]
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
with col2:
    st.markdown("<h1 class='main-header'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)
    st.caption("Official AI Teaching Assistant for Sections G1, G2, G3, G4")

st.warning("🚀 **BETA**: If you encounter display issues, please refresh or contact Prof. Mai Anh Tien.")

# Display history with forced visibility
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Multi-turn Chat Logic
if prompt := st.chat_input("Ask a question about the course..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Format history to alternate roles
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
