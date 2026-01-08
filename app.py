import streamlit as st
import google.generativeai as genai

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="💻", layout="wide")

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
            # Extract first line for versioning
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

# --- 3. CUSTOM UI STYLING (REMOVED BACKGROUND IMAGE) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* Transparent chat bubbles for clean look */
        .stChatMessage {
            background-color: rgba(240, 242, 246, 0.8);
            border-radius: 12px;
            border: 1px solid #ddd;
        }
        /* SMU Deep Blue Sidebar */
        [data-testid="stSidebar"] {
            background-color: #002349;
            color: white;
        }
        .stMetric {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & REQUEST COUNTER ---
# Initialize request count in session state
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("MaiLab Portal")
    # Using a professional coding icon/image instead of background
    st.image("https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&w=400&q=80")
    st.info("**IS115: Algorithms & Programming**\n\nSections G1, G2, G3, G4")
    
    # NEW: Request Counter Metric
    st.metric("Total Student Questions", st.session_state.request_count)
    
    st.markdown("---")
    st.write("**Instructor:** Prof. Mai Anh Tien")
    st.write(f"**Syllabus Version:** {VERSION_ID}")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. CHAT INTERFACE ---
st.title("🤖 IS115 AI Teaching Assistant")
st.warning("🚀 **BETA VERSION**: For technical issues, contact Prof. Mai Anh Tien (@Tienmai).")

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt logic
if prompt := st.chat_input("Ask about recursion, complexity, or course admin..."):
    # Increment request counter
    st.session_state.request_count += 1
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Response generation
    with st.chat_message("assistant"):
        try:
            # Properly format history for the Gemini API
            formatted_history = []
            for m in st.session_state.messages[:-1]:
                role = "model" if m["role"] == "assistant" else "user"
                formatted_history.append({"role": role, "parts": [m["content"]]})
            
            # Start the chat session
            chat = model.start_chat(history=formatted_history)
            
            # Send message and get response
            response = chat.send_message(prompt)
            full_res = response.text
            
            # Display results
            st.markdown(full_res)
            
            # Save assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": full_res})

        except Exception as e:
            if "429" in str(e):
                st.error("Rate limit reached. Please wait a moment.")
            else:
                st.error(f"Error processing response: {str(e)}")
