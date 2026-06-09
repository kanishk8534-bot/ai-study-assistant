import streamlit as st
from openai import OpenAI
import os
import random
from datetime import datetime

# ==========================================
# 1. INITIALIZATION & STYLING
# ==========================================

# Initialize the client pointing to NVIDIA's API Gateway using your key
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "Bearer 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")

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

# Set page config once at the very top
st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")

# Inject clear, high-contrast text and UI styling 
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #05070f, #0b1528, #110924, #02040a) !important;
        background-size: 400% 400% !important;
        animation: auroraFlow 20s ease infinite !important;
        color: #f8fafc !important;
    }

    @keyframes auroraFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .top-header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid rgba(225, 225, 225, 0.1);
        margin-bottom: 20px;
    }
    
    .brand-logo-text {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* High-Contrast Explicit Speech Bubbles */
    .chat-bubble-user {
        background-color: rgba(59, 130, 246, 0.25) !important;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 14px 18px;
        border-radius: 16px 16px 4px 16px;
        margin-bottom: 6px;
        color: #ffffff !important;
    }
    
    .chat-bubble-assistant {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 14px 18px;
        border-radius: 16px 16px 16px 4px;
        margin-bottom: 6px;
        color: #f1f5f9 !important;
    }

    .chat-meta {
        font-size: 12px;
        color: #94a3b8 !important;
        margin-bottom: 15px;
        padding-left: 4px;
    }
    
    /* Input Box layout elements */
    .stTextInput div div input {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 14px !important;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%) !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State values
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "preset_query" not in st.session_state:
    st.session_state.preset_query = ""
if "last_processed" not in st.session_state:
    st.session_state.last_processed = ""

# ==========================================
# 2. UI HEADER
# ==========================================
st.markdown("""
    <div class='top-header-container'>
        <div class='brand-logo-text'>📚 AI Study Assistant</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR WORKSPACE
# ==========================================
with st.sidebar:
    st.markdown("### 🛠️ Workspace Controls")
    uploaded_file = st.file_uploader("Upload Notes/Syllabus (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.success(f"Loaded: {uploaded_file.name}")
        
    st.markdown("---")
    st.markdown("**💡 Hackathon Demo Pro-Tip:**\nUpload a complex physics or engineering PDF to show the judges how the AI extracts data instantly.")

# ==========================================
# 4. CHAT HISTORY (RENDERED ABOVE INPUT BOX)
# ==========================================
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-bubble-user">
                    <b>👤 {message['name']}:</b><br>{message['content']}
                </div>
                <div class="chat-meta">🕒 {message['time']}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-bubble-assistant">
                    <b>🤖 {message['name']}:</b><br>{message['content']}
                </div>
                <div class="chat-meta">🕒 {message['time']}</div>
            """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 25px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. QUICK ACTIONS CARD SYSTEM
# ==========================================
st.write("✨ **Quick Actions (Click to try):**")
card1, card2, card3 = st.columns(3)

with card1:
    if st.button("📝 Summarize Syllabus"):
        st.session_state.preset_query = "Provide a high-level summary of the essential topics from my study material."
        st.rerun()

with card2:
    if st.button("❓ Create a Quick Quiz"):
        st.session_state.preset_query = "Generate 3 practice questions along with their answers from this topic."
        st.rerun()

with card3:
    if st.button("🧠 Simplify Hard Terms"):
        st.session_state.preset_query = "Break down the most complex engineering or technical definitions here into plain english."
        st.rerun()

# ==========================================
# 6. INPUT AREA & PROCESSING LOGIC
# ==========================================
current_value = st.session_state.preset_query
user_question = st.text_input(
    "What are we studying today? (Type and press Enter)", 
    value=current_value, 
    placeholder="Ask me anything about your studies..."
)

# Clear preset query state immediately after processing
st.session_state.preset_query = ""

if user_question.strip() != "" and user_question != st.session_state.last_processed:
    st.session_state.last_processed = user_question
    
    # Generate timestamp text string
    timestamp = datetime.now().strftime("%I:%M %p")
    
    # Standardize input for quick local string matching
    clean_input = user_question.strip().lower().replace("?", "").replace("!", "").replace(".", "")
    local_reply = None

    # --- LOCAL CONVERSATION DATA MAP (INTENTS) ---
    student_intents = {
        "greetings": {
            "keywords": ["hello", "hi", "hey", "greetings", "yo"],
            "responses": [
                "Hello! 👋 Ready to crush some study goals today? What are we working on?",
                "Hello! 🧠 I am your Personal AI Tutor. What subject or concept are we exploring today?"
            ]
        },
        "status_check": {
            "keywords": ["how are you", "hows it going", "you good"],
            "responses": [
                "I'm running at 100% efficiency and fully charged! 🚀 Ready to break down notes or debug code. How are you doing?"
            ]
        }
    }

    # Match intent loop
    for intent, data in student_intents.items():
        if any(keyword in clean_input for keyword in data["keywords"]):
            local_reply = random.choice(data["responses"])
            break

    # --- COMMIT SESSIONS ---
    if local_reply:
        st.session_state.chat_history.append({"role": "user", "name": "You", "time": timestamp, "content": user_question})
        st.session_state.chat_history.append({"role": "assistant", "name": "Assistant", "time": timestamp, "content": local_reply})
        st.rerun()
        
    else:
        with st.spinner("Analyzing context..."):
            try:
                # Call NVIDIA Gateway with Gemma 3
                completion = client.chat.completions.create(
                    model="google/gemma-3n-e2b-it",
                    messages=[
                        {"role": "system", "content": "You are an expert, encouraging AI study assistant helping a university student."},
                        {"role": "user", "content": user_question}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                
                response_text = completion.choices[0].message.content
                
                st.session_state.chat_history.append({"role": "user", "name": "You", "time": timestamp, "content": user_question})
                st.session_state.chat_history.append({"role": "assistant", "name": "Assistant", "time": timestamp, "content": response_text})
                st.rerun()

            except Exception as e:
                st.toast("Error contacting API endpoint", icon="⏳")
                st.error("🚀 **The AI Brain is overloaded!** Our servers are experiencing heavy traffic. Please click 'Ask Assistant' again in a few seconds.")
