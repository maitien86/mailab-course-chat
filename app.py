import streamlit as st
import google.generativeai as genai

# 1. Securely fetch the API Key from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("API Key not found. Please add GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# 2. Define the Bot's Persona (Customize this for your course!)
COURSE_NAME = "Reinforcement Learning & Human Behavior" # Example
SYSTEM_PROMPT = f"""
You are the official AI Teaching Assistant for the course: {COURSE_NAME}.
Your goal is to help students understand course concepts, assignments, and schedules.

Guidelines:
- If a student asks about Lab research, refer to 'MaiLab' at SMU.
- Be encouraging and academic in tone.
- If you are unsure about a specific administrative detail (like a deadline change), 
  advise the student to check the official syllabus or email the Professor.
- Do not answer questions completely unrelated to the course or computer science.
"""

# 3. Initialize the Gemini Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Use Flash for speed and higher free limits
    system_instruction=SYSTEM_PROMPT
)

# 4. Streamlit UI Setup
st.set_page_config(page_title="MaiLab Course Bot", page_icon="🤖")
st.title("📚 MaiLab Course Assistant")
st.caption(f"Ask me anything about {COURSE_NAME}")

# Initialize chat history in the browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Logic
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from Gemini
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Prepare history for Gemini (filtering for correct format)
        history = [
            {"role": m["role"], "parts": [m["content"]]} 
            for m in st.session_state.messages[:-1]
        ]
        
        # Start chat and send the new message
        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(prompt)
        
        full_response = response.text
        message_placeholder.markdown(full_response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})