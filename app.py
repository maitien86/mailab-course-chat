import streamlit as st
import google.generativeai as genai
from datetime import datetime
import os

# --- 1. ROBUST IMPORTS ---
try:
    from PyPDF2 import PdfReader
    from langchain_text_splitters import RecursiveCharacterTextSplitter 
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError as e:
    st.error(f"Library Missing: {e}")
    st.stop()

# --- 2. CONFIGURATION ---
MODEL_NAME = "gemini-2.5-flash-lite"
st.set_page_config(page_title="IS115 Assistant", page_icon="🎓", layout="wide")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing GEMINI_API_KEY in Secrets.")
    st.stop()

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

# --- 4. UI STYLING (BLACK THEME) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #333333; }
    [data-testid="stChatMessage"] { background-color: #1A1A1A !important; border: 1px solid #444444 !important; }
    [data-testid="stChatMessageContent"] p, li, span, code, .stMarkdown { color: #FFFFFF !important; }
    h1, h2, h3, .main-header { color: #FFFFFF !important; }
    /* Fix for file uploader text visibility */
    .stFileUploader label { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR ---
if "messages" not in st.session_state: st.session_state.messages = []

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f6/Singapore_Management_University_logo.svg/1200px-Singapore_Management_University_logo.svg.png", width=180)
    st.markdown("---")
    st.subheader("👨‍🏫 Prof. Mai Anh Tien")
    
    # MANUAL UPLOADER (Backup)
    st.markdown("### 📚 Knowledge Base")
    uploaded_files = st.file_uploader("Upload course PDFs", type="pdf", accept_multiple_files=True)
    
    combined_text = get_github_pdf_text()
    if uploaded_files:
        for f in uploaded_files:
            reader = PdfReader(f)
            for page in reader.pages:
                combined_text += page.extract_text() or ""

    vector_db = process_text_to_vectors(combined_text)
    
    if vector_db:
        st.success("✅ Knowledge Base Active")
    else:
        st.info("ℹ️ No PDFs detected yet.")

    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. CHAT INTERFACE ---
st.markdown("<h1 class='main-header'>IS115: Algorithms & Programming</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        context = ""
        if vector_db:
            docs = vector_db.similarity_search(prompt, k=3)
            context = "\n".join([d.page_content for d in docs])
        
        full_instr = f"Answer using this context:\n{context}"
        try:
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=full_instr)
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
