import streamlit as st
from openai import OpenAI
import os
import random
import re
from datetime import datetime

# ==========================================
# 1. INITIALIZATION & STYLING
# ==========================================

# Initialize the client pointing to NVIDIA's API Gateway
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")

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
        margin-bottom: 2px;
        color: #ffffff !important;
    }
    
    .chat-bubble-assistant {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 14px 18px;
        border-radius: 16px 16px 16px 4px;
        margin-bottom: 2px;
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
    st.markdown("### 📡 Local Engine Status")
    st.caption("• Basic Math Parsing: **Active**")
    st.caption("• Newton's Rings Physics: **Active**")

# ==========================================
# 4. CHAT HISTORY (FIXED RENDER ENGINE)
# ==========================================
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-bubble-user">
                    <b>👤 {message['name']}:</b>
                </div>
            """, unsafe_allow_html=True)
            st.write(message['content'])
            st.markdown(f'<div class="chat-meta">🕒 {message["time"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-bubble-assistant">
                    <b>🤖 {message['name']}:</b>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(message['content'])
            st.markdown(f'<div class="chat-meta">🕒 {message["time"]}</div>', unsafe_allow_html=True)
            
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 25px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. QUICK ACTIONS CARD SYSTEM
# ==========================================
st.write("✨ **Quick Actions (Click to try):**")
card1, card2 = st.columns(2)

with card1:
    if st.button("🔬 Explain Newton's Rings"):
        st.session_state.preset_query = "What is Newton's ring?"
        st.rerun()

with card2:
    if st.button("➕ Try Simple Math"):
        st.session_state.preset_query = "What is 45 + 55?"
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
    
    # Standardize input for keyword validation
    clean_input = user_question.strip().lower()
    local_reply = None

    # --------------------------------------------------------
    # CLEAN OFFLINE LOGIC ENGINE
    # --------------------------------------------------------
    
    # 1. NEWTON'S RINGS INTERCEPTOR
    if "newton" in clean_input and "ring" in clean_input:
        local_reply = """
### 🔬 Newton's Rings (Physics - Optics)

**Newton's Rings** is a classic interference pattern created when monochromatic light reflects between a spherical surface (a plano-convex lens) and an adjacent flat glass plate.

#### How it Works:
* When a plano-convex lens is placed on a flat glass plate, a **variable-thickness air film** is formed between them.
* Light hitting this structure reflects from both the top surface of the plate and the bottom surface of the lens.
* These two reflected light rays interfere constructively or destructively depending on the optical path difference, forming **concentric alternating bright and dark rings**.

#### Key Characteristics:
1. **Center is Dark:** Due to a phase change of 180 degrees (or $\pi$ radians) when light reflects from the denser glass plate interface.
2. **Rings get Closer:** The fringe width decreases as the radius increases because the thickness of the air film does not change linearly.

#### Formula for Ring Diameters:
* **For Dark Rings:** $$D_n^2 = 4n\lambda R$$
* **For Bright Rings:** $$D_n^2 = 2(2n-1)\lambda R$$

*(Where $D_n$ is the diameter of the nth ring, $n$ is the ring number, $\lambda$ is the wavelength of light, and $R$ is the radius of curvature of the lens).*
"""

    # 2. BASIC MATHEMATICS INLINE PARSER
    else:
        numbers = re.findall(r'\d+\.?\d*', clean_input)
        
        if len(numbers) >= 2:
            num1 = float(numbers[0])
            num2 = float(numbers[1])
            
            if "+" in clean_input or "add" in clean_input or "plus" in clean_input or "sum" in clean_input:
                local_reply = f"📊 **Math Result (Local Calculation):** \n{num1} + {num2} = **{num1 + num2}**"
                
            elif "-" in clean_input or "subtract" in clean_input or "minus" in clean_input or "diff" in clean_input:
                if "from" in clean_input:
                    local_reply = f"📊 **Math Result (Local Calculation):** \n{num2} - {num1} = **{num2 - num1}**"
                else:
                    local_reply = f"📊 **Math Result (Local Calculation):** \n{num1} - {num2} = **{num1 - num2}**"
                    
            elif "/" in clean_input or "divide" in clean_input or "by" in clean_input:
                if num2 == 0:
                    local_reply = "⚠️ **Math Error:** Division by zero is undefined."
                else:
                    local_reply = f"📊 **Math Result (Local Calculation):** \n{num1} ÷ {num2} = **{num1 / num2:.4f}**"
                    
            elif "x" in clean_input or "*" in clean_input or "multiply" in clean_input or "times" in clean_input:
                local_reply = f"📊 **Math Result (Local Calculation):** \n{num1} × {num2} = **{num1 * num2}**"

    # --- CONVERSATIONAL GREETING INTERCEPTOR ---
    if not local_reply:
        if any(w in clean_input for w in ["hello", "hi", "hey"]):
            local_reply = "Hello! 👋 Your offline math parser and Newton's ring modules are loaded. How can I help you study today?"

    # ==========================================
    # 7. RESPONSE DELIVERY SYSTEM
    # ==========================================
    if local_reply:
        st.session_state.chat_history.append({"role": "assistant", "name": "Assistant (Local Mode)", "time": timestamp, "content": local_reply})
        st.rerun()
        
    else:
        # Fallback to Nvidia Cloud Gateway if user asks complex out-of-bounds questions
        with st.spinner("Analyzing context via Cloud Model..."):
            try:
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
                st.error("🚀 **The AI Brain is overloaded!** Our servers are experiencing heavy traffic. Please press Enter again.")
