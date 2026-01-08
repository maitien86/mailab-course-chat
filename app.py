import streamlit as st
import google.generativeai as genai

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
    model_name="gemini-2.5-flash",
    system_instruction=SYLLABUS_TEXT
)

# 2. UI Layout
st.set_page_config(page_title="IS115 Course Bot", page_icon="💻")
st.title("💻 IS115: Algorithms & Programming")
st.caption(f"Powered by Gemini 2.5 Flash | {VERSION_ID}")

with st.sidebar:
    st.header("Course Resources")
    st.info(f"Current Syllabus: {VERSION_ID}")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("**Note:** Bot uses LockDown Browser rules for exams.")

# 3. Chat Logic
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about recursion, stacks, or course admin..."):
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
