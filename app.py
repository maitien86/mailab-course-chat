import streamlit as st
import google.generativeai as genai
import time

# --- 1. SETTINGS & PRICING (2026 PAID TIER) ---
COST_PER_1M_INPUT = 0.10  # USD
COST_PER_1M_OUTPUT = 0.40 # USD
MODEL_NAME = "gemini-2.5-flash-lite" #

# --- 2. CONFIGURATION & SYLLABUS LOADING ---
st.set_page_config(page_title="IS115 Assistant", page_icon="💻", layout="wide")

# Securely fetch API Key
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

# Initialize Model
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYLLABUS_CONTENT
)

# --- 3. CUSTOM UI STYLING (SMU/MAILAB THEME) ---
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
            border: 1px solid #ddd;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(0, 35, 73, 0.95); /* SMU Deep Blue */
            color: white;
        }
        .stMetric {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_code_with_all_tags=True
    )

add_custom_style()

# --- 4. SIDEBAR & COST TRACKING ---
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

with st.sidebar:
    st.title("MaiLab Portal")
    st.image("https://images.unsplash.com/photo-1516116216624-53e697fedbea?auto=format&fit=crop&w=400&q=80")
    st.info(f"**IS115: Algorithms & Programming**\n\nSections G1, G2, G3, G4 [cite: 403]")
    
    st.metric("Session Cost (USD)", f"${st.session_state.total_cost:.5f}")
    
    st.markdown("---")
    st.write(f"**Instructor:** Prof. Mai Anh Tien [cite: 403]")
    st.write(f"**Version:** {VERSION_ID}")
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.total_cost = 0.0
        st.rerun()

# --- 5. CHAT INTERFACE ---
st.title("🤖 IS115 AI Teaching Assistant")
st.warning("🚀 **BETA VERSION**: Any technical issues, contact Prof. Mai Anh Tien (@Tienmai).")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt
if prompt := st.chat_input("Ask about recursion, complexity, or course admin..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Response generation
    with st.chat_message("assistant"):
        try:
            # Format history (alternating user/model)
            formatted_history = []
            for m in st.session_state.messages[:-1]:
                role = "model" if m["role"] == "assistant" else "user"
                formatted_history.append({"role": role, "parts": [m["content"]]})
            
            chat = model.start_chat(history=formatted_history)
            
            # Request response with metadata tracking
            response = chat.send_message(prompt)
            
            # --- COST CALCULATION ---
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            
            turn_cost = (input_tokens * (COST_PER_1M_INPUT / 1_000_000)) + \
                        (output_tokens * (COST_PER_1M_OUTPUT / 1_000_000))
            
            st.session_state.total_cost += turn_cost
            
            # Display response
            st.markdown(response.text)
            st.caption(f"Used {input_tokens + output_tokens} tokens | Turn Cost: ${turn_cost:.5f}")
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            if "429" in str(e):
                st.error("Rate limit reached. Please wait a moment.")
            else:
                st.error(f"Error: {str(e)}")
