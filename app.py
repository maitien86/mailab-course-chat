import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os

# --- 1. ROBUST IMPORTS ---
try:
    from PyPDF2 import PdfReader
    # New import path for 2026 stability
    from langchain_text_splitters import RecursiveCharacterTextSplitter 
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError as e:
    st.error(f"⚠️ Library Missing: {e}. Please ensure your requirements.txt is correct and reboot the app.")
    st.stop()

# --- 1. SETTINGS ---
MODEL_NAME = "gemini-2.5-flash-lite"
TERM_START_DATE = datetime(2026, 1, 5)

# --- 2. CONFIGURATION & RAG LOGIC ---
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

# Helper: Extract text from PDFs in a folder
def get_pdf_text():
    text = "123"
    pdf_folder = "data/" # Place your PDF files (e.g., Week1.pdf) here
    
    # DEBUG: See what's actually there
    if os.path.exists(pdf_folder):
        all_files = os.listdir(pdf_folder)
        st.sidebar.write(f"Files found: {all_files}")
    else:
        st.sidebar.error("CRITICAL: The folder '/data' does not exist at the root!")
        return ""
        
    if not os.path.exists(pdf_folder):
        return ""
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_reader = PdfReader(os.path.join(pdf_folder, filename))
            for page in pdf_reader.pages:
                text += page.extract_text()
    return text

# --- 3. RAG CORE LOGIC ---
def process_text_to_vectors(raw_text):
    if not raw_text or len(raw_text.strip()) < 50:
        return None
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(raw_text)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
        return FAISS.from_texts(chunks, embedding=embeddings)
    except Exception as e:
        st.error(f"Vector Error: {e}")
        return None

def get_github_pdf_text():
    text = ""
    folder = "data/"
    if os.path.exists(folder):
        files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
        for f in files:
            try:
                reader = PdfReader(os.path.join(folder, f))
                for page in reader.pages:
                    text += page.extract_text() or ""
            except: pass
    return text
# Helper: Create Vector Store
@st.cache_resource
def create_vector_store():
    raw_text = get_pdf_text()
    if not raw_text:
        return None
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(raw_text)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

# Initialize RAG
vector_db = create_vector_store()

# Load syllabus for system context
def load_syllabus():
    try:
        with open("syllabus.txt", "r", encoding="utf-8") as f:
            content = f.read()
            version = content.split('\n')[0].replace('###', '').strip()
            return content, version
    except FileNotFoundError:
        return "You are an assistant for IS115.", "v0.0"
        
SYLLABUS, VERSION_ID = load_syllabus()
model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYLLABUS)

# --- 3. FORCEFUL UI STYLING (BLACK BACKGROUND / WHITE TEXT) ---
def add_custom_style():
    st.markdown(
        """
        <style>
        /* 1. Force Main App Background to Black */
        .stApp {
            background-color: #000000 !important;
        }
        
        /* 2. Force Sidebar Background */
        [data-testid="stSidebar"] {
            background-color: #111111 !important;
            border-right: 1px solid #333333;
        }

        /* 3. Force Chat Bubbles to Dark Grey/Black */
        [data-testid="stChatMessage"] {
            background-color: #1A1A1A !important;
            border: 1px solid #444444 !important;
            border-radius: 12px !important;
        }

        /* 4. CRITICAL: Force ALL Text to White (Overrides Light Mode) */
        [data-testid="stChatMessageContent"] p, 
        [data-testid="stChatMessageContent"] li, 
        [data-testid="stChatMessageContent"] span,
        [data-testid="stChatMessageContent"] code,
        [data-testid="stChatMessageContent"] div,
        .stMarkdown, p, label, .stCaption {
            color: #FFFFFF !important; 
            font-weight: 400 !important;
        }

        /* 5. Header Colors */
        h1, h2, h3, .main-header {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        /* 6. Sidebar Text Color */
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        /* 7. Input Box Styling */
        .stChatInputContainer textarea {
            color: #FFFFFF !important;
            background-color: #222222 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_custom_style()

# --- 4. SIDEBAR & PROFESSOR INFO ---
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

# Calculate Progress
def get_course_progress():
    today = datetime.now()
    days_passed = (today - TERM_START_DATE).days
    current_week = max(1, min(13, (days_passed // 7) + 1))
    progress_percent = min(100, int((current_week / 13) * 100))
    return current_week, progress_percent

current_week, progress_val = get_course_progress()

with st.sidebar:
    # SMU Branding
    st.image("https://vms.smu.edu.sg/images/Logo/smu-logo.png", width=180)
    
    st.markdown("---")
    st.subheader("👨‍🏫 Instructor:")
    st.markdown("""
    **Prof. Mai Anh Tien**  
    *SCIS,* **Singapore Management University**
    
     
    **Email:** [atmai@smu.edu.sg](mailto:atmai@smu.edu.sg)
    **Telegram:** @Tienmai
    """)
    
    st.markdown("---")
    # Progress Tracker
    st.subheader(f"📅 Week {current_week} of 13")
    st.progress(progress_val / 100)

    combined_text = get_github_pdf_text()
    vector_db = process_text_to_vectors(combined_text)
    if vector_db:
        st.success("📚 Knowledge Base: Active")
    else:
        st.info("ℹ️ No PDFs found in /data folder")
        
    st.markdown("---")
    st.metric("Total Questions Asked", st.session_state.request_count)
    st.write(f"Syllabus Version: {VERSION_ID}")
    
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.rerun()

# --- 5. MAIN CHAT INTERFACE ---
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=70)
with col2:
    st.markdown("<h1 class='main-header'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)

# Beta Version Notice
st.info("🚀 **BETA VERSION:** This is an experimental AI Teaching Assistant. If you encounter any issues, please contact Prof. Mai Anh Tien or your section TA.")

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Logic
if prompt := st.chat_input("Ask a question about algorithms..."):
    st.session_state.request_count += 1
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Alternating history for Gemini
            history = [{"role": "model" if m["role"] == "assistant" else "user", 
                        "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {str(e)}")
