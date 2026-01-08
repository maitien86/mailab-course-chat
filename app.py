import streamlit as st
import google.generativeai as genai

# --- 1. SETTINGS & PRICING ---
COST_PER_1M_INPUT = 0.10  
COST_PER_1M_OUTPUT = 0.40 
MODEL_NAME = "gemini-2.5-flash-lite"

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="💻", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

def load_syllabus():
    try:
        with open("syllabus.txt", "r", encoding="utf-8") as f:
            content = f.read()
            version = content.split('\n')[0].replace('###', '').strip()
            return content, version
    except FileNotFoundError:
        return "Assistant for IS115.", "v0.0"

SYLLABUS_CONTENT, VERSION_ID = load_syllabus()

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. CORRECTED UI STYLING ---
def add_custom_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-attachment: fixed;
        }
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.92);
            border-radius: 12px;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(0, 35, 73, 0.95);
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & STATE ---
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("MaiLab Portal")
    st.image("https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&w=400&q=80")
    st.metric("Session Cost (USD)", f"${st.session_state.total_cost:.5f}")
    st.write(f"Instructor: Prof. Mai Anh Tien")
    st.write(f"Syllabus: {VERSION_ID}")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.rerun()

# --- 5. CHAT ---
st.title("🤖 IS115 AI Assistant")
st.warning("🚀 BETA: Contact Prof. Mai Anh Tien (@Tienmai) for issues.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            history = [{"role": "model" if m["role"] == "assistant" else "user", 
                        "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
            
            # Metadata tracking
            in_t = response.usage_metadata.prompt_token_count
            out_t = response.usage_metadata.candidates_token_count
            cost = (in_t * (COST_PER_1M_INPUT / 1000000)) + (out_t * (COST_PER_1M_OUTPUT / 1000000))
            st.session_state.total_cost += cost
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
