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

# Initialize Model with Master Syllabus
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. UI STYLING (FIXING WHITE-ON-WHITE ISSUE) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* Main App Background - Light Grey */
        .stApp {
            background-color: #F3F4F6;
        }
        
        /* Sidebar Styling (SMU Deep Blue) */
        [data-testid="stSidebar"] {
            background-color: #002349;
            color: white;
        }

        /* Chat Bubbles Styling - White with Grey Border */
        [data-testid="stChatMessage"] {
            background-color: #FFFFFF !important;
            border: 1px solid #D1D5DB;
            border-radius: 12px;
        }

        /* CRITICAL FIX: Force Dark Charcoal Text color */
        [data-testid="stChatMessageContent"] p {
            color: #1F2937 !important; 
            font-size: 1.05rem;
            font-weight: 400;
        }

        /* Metrics in sidebar color fix */
        [data-testid="stMetricValue"] {
            color: white !important;
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
    # Official SMU Logo
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=200)
    
    st.markdown("---")
    st.metric("Total Questions Asked", st.session_state.request_count)
    
    st.info(f"**Course:** IS115 Algorithms & Programming\\n\\n**Sections:** G1, G2, G3, G4")
    
    st.markdown("---")
    st.write(f"**Instructor:** Prof. Mai Anh Tien")
    st.write(f"**Version:** {VERSION_ID}")
    
    if st.button("Reset Session"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
with col2:
    st.markdown("<h1 style='color: #002349;'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)
    st.caption("Official AI Teaching Assistant for Sections G1-G4")

st.warning("🚀 **BETA NOTICE**: If you encounter issues, please contact Prof. Mai Anh Tien (@Tienmai).")

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt logic
if prompt := st.chat_input("Ask a question about the course..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Format history for Gemini API
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
