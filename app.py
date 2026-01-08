import streamlit as st
import google.generativeai as genai

# 1. API Configuration
# Ensure you have GEMINI_API_KEY in your Streamlit Cloud Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing API Key. Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
    st.stop()

# 2. System Instructions (Your "Syllabus")
SYSTEM_PROMPT = """
You are a helpful Teaching Assistant for [Insert Course Name]. 
- Use the following syllabus rules: [Insert Deadlines/Grading here].
- Provide hints rather than direct answers for coding/math problems.
- If a question is outside the course scope, politely redirect the student.
- Important: Always be professional and encouraging.
"""

# 3. Model Initialization
# Using 1.5-flash for the best balance of speed and free-tier limits
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# 4. Streamlit UI
st.set_page_config(page_title="Course AI Assistant", page_icon="🎓")
st.title("🎓 Course Chatbot")

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Logic
if prompt := st.chat_input("Ask a question about the course..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        try:
            # FIX: Format history correctly for Gemini
            # Streamlit uses "assistant", Gemini REQUIRES "model"
            formatted_history = []
            for m in st.session_state.messages[:-1]:
                role = "model" if m["role"] == "assistant" else "user"
                formatted_history.append({"role": role, "parts": [m["content"]]})

            # Start chat session with historical context
            chat = model.start_chat(history=formatted_history)
            
            # Request response (streaming for a better UI feel)
            response = chat.send_message(prompt, stream=True)
            
            # Stream the text to the UI
            full_response = ""
            placeholder = st.empty()
            for chunk in response:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            
            # Save assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Try clicking 'Clear Conversation' in the sidebar to reset the history.")
