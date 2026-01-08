import streamlit as st
import google.generativeai as genai
import time

# 1. Configuration & Model Setup
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# Function to load syllabus and extract version
def get_syllabus_data():
    try:
        with open("syllabus.txt", "r", encoding="utf-8") as f:
            content = f.read()
            # Find the first line for the version number
            version = content.split('\n')[0].replace('###', '').strip()
            return content, version
    except FileNotFoundError:
        return "You are a helpful TA for IS115.", "v0.0"

SYLLABUS_TEXT, VERSION_ID = get_syllabus_data()

# Initialize Gemini 2.5 Flash
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=SYLLABUS_TEXT
)

# 2. UI Layout
# --- UI CONFIGURATION ---
st.set_page_config(page_title="IS115 Assistant", page_icon="💻", layout="wide")

# Custom CSS for a professional background and styling
def add_custom_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1515879218367-8466d910aaa4?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80");
            background-size: cover;
            background-attachment: fixed;
        }
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.9); /* Transparent white for readability */
            border-radius: 15px;
            padding: 10px;
            margin: 5px 0;
        }
        h1 {
            color: #FFFFFF;
            text-shadow: 2px 2px 4px #000000;
        }
        </style>
        """,
        unsafe_allow_code_with_all_tags=True
    )

add_custom_style()

# --- SIDEBAR CONTENT ---
with st.sidebar:
    # Adding a course-related image in the sidebar
    st.image("https://images.unsplash.com/photo-1504639725590-34d0984388bd?auto=format&fit=crop&w=400&q=80", 
             caption="IS115: Thinking Computationally")
    
    st.header("Section G1-G4 Portal")
    st.info("Welcome to the MaiLab AI Assistant. Focus: Design, Complexity, and Efficiency.") [cite: 184, 185, 186]
    
    # Existing TA and Versioning Info...
    st.write(f"Instructor: Prof. Mai Anh Tien") [cite: 403]
    
# 3. Chat Logic
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
try:
    # Attempt to send the message
    response = chat.send_message(prompt, stream=True)
except Exception as e:
    if "429" in str(e):
        st.warning("Too many requests! Waiting 10 seconds to retry...")
        time.sleep(10)  # Wait before retrying
        response = chat.send_message(prompt, stream=True)
        
if prompt := st.chat_input("Ask course admin or course materials..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Format history: convert 'assistant' to 'model' for the API
        history = [{"role": "model" if m["role"] == "assistant" else "user", 
                    "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
        
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt, stream=True)
        
        full_res = ""
        holder = st.empty()
        for chunk in response:
            full_res += chunk.text
            holder.markdown(full_res + "▌")
        holder.markdown(full_res)
        
    st.session_state.messages.append({"role": "assistant", "content": full_res})
