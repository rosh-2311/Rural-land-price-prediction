import streamlit as st
import pandas as pd
import joblib
import os
from genai_helper import validate_price_with_ai, generate_advisory_report, get_ai_advisor_response, get_chat_response
from dotenv import load_dotenv
import json as py_json
import base64

# Load environment variables
load_dotenv()

# -----------------------------
# User Database & Persistence
# -----------------------------
USER_DB_FILE = "users.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                return py_json.load(f)
        except:
            pass
    return {
        "admin@land.com": {"password": "admin123", "name": "Admin Professional"},
        "test@user.com": {"password": "password123", "name": "Strategic Tester"}
    }

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        py_json.dump(users, f)

def save_feedback(data):
    # Save to JSON (existing)
    feedback_file_json = "feedback.json"
    existing = []
    if os.path.exists(feedback_file_json):
        with open(feedback_file_json, "r") as f:
            try: existing = py_json.load(f)
            except: existing = []
    existing.append(data)
    with open(feedback_file_json, "w") as f:
        py_json.dump(existing, f, indent=4)
    
    # Save to CSV (New)
    feedback_file_csv = "feedback_sheet.csv"
    df = pd.DataFrame([data])
    if not os.path.exists(feedback_file_csv):
        df.to_csv(feedback_file_csv, index=False)
    else:
        df.to_csv(feedback_file_csv, mode='a', header=False, index=False)

# Initialize Session State
if 'users' not in st.session_state:
    st.session_state['users'] = load_users()
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'auth_mode' not in st.session_state:
    st.session_state['auth_mode'] = 'login'
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'auth'
if 'advisory_report' not in st.session_state:
    st.session_state['advisory_report'] = None
if 'last_prediction' not in st.session_state:
    st.session_state['last_prediction'] = None
if 'ai_advice' not in st.session_state:
    st.session_state['ai_advice'] = {"query": "", "response": ""}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# --- Helper Navigation ---
def navigate_to(page):
    st.session_state['page'] = page
    st.rerun()

def logout():
    st.session_state['authenticated'] = False
    st.session_state['current_user'] = None
    st.session_state['page'] = 'auth'
    st.rerun()

st.set_page_config(
    page_title="Rural Land Price Predictor",
    page_icon="🌱",
    layout="wide"
)

# --- CSS INJECTION (Pure Premium Emerald) ---
def get_base64_bin(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def inject_custom_css():
    base64_bg = get_base64_bin("assets/login_bg.png")
    css = f"""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* {{ font-family: 'Outfit', sans-serif; }}
/* Global app layout with Agricultural Background */
.stApp {{
    background: linear-gradient(rgba(2, 44, 34, 0.7), rgba(2, 44, 34, 0.85)), 
                url('data:image/png;base64,{base64_bg}') no-repeat center center fixed !important;
    background-size: cover !important;
    color: #ecfdf5;
    overflow-x: hidden;
}}
.main-bg-overlay {{
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: url('https://www.transparenttextures.com/patterns/dark-matter.png');
    opacity: 0.15;
    z-index: -1;
}}
.glass-card {{
    background: rgba(6, 78, 59, 0.55);
    backdrop-filter: blur(30px) saturate(180%);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 42px;
    padding: 60px 45px;
    box-shadow: 0 35px 70px -15px rgba(0, 30, 20, 0.95);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}}
.logo-container {{
    width: 100%;
    text-align: center;
    margin-bottom: 30px;
}}
.logo-icon {{
    font-size: 65px;
    margin-bottom: 10px;
    display: block;
}}
.logo-text {{
    font-size: 36px !important;
    font-weight: 700 !important;
    color: #f0fdf4 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}}
.stTextInput, .stButton {{
    width: 100% !important;
}}
.stTextInput input {{
    background: rgba(2, 44, 34, 0.75) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 16px !important;
    color: #f0fdf4 !important;
    height: 60px !important;
}}
.stButton > button {{
    background: linear-gradient(135deg, #10b981 0%, #064e3b 100%) !important;
    border: none !important;
    border-radius: 18px !important;
    height: 60px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    color: white !important;
    margin-top: 10px !important;
    transition: all 0.4s !important;
}}
.stButton > button:hover {{
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 30px rgba(16, 185, 129, 0.3) !important;
}}
.premium-card {{
    background: rgba(6, 78, 59, 0.45);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 28px;
    padding: 35px;
    margin-bottom: 30px;
}}
[data-testid="stMetricValue"] {{
    background: linear-gradient(to right, #34d399, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    color: transparent !important;
}}
section[data-testid="stSidebar"] {{
    background-color: #011f18 !important;
    border-right: 1px solid rgba(16, 185, 129, 0.2) !important;
}}
h1, h2, h3 {{
    text-align: center;
    width: 100%;
}}
.report-title {{
    font-size: 42px !important;
    font-weight: 800 !important;
    color: #10b981 !important;
    margin-bottom: 10px !important;
}}
.report-meta {{
    color: #6ee7b7 !important;
    font-size: 1.2rem !important;
    border-bottom: 1px solid rgba(16, 185, 129, 0.2);
    padding-bottom: 20px;
    margin-bottom: 30px;
}}
@keyframes pulse-emerald {{
    0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }}
    70% {{ box-shadow: 0 0 0 15px rgba(16, 185, 129, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
}}
.pulse-btn > button {{
    animation: pulse-emerald 2s infinite;
}}
@keyframes pop-in {{
    0% {{ transform: scale(0.95); opacity: 0; }}
    100% {{ transform: scale(1); opacity: 1; }}
}}
.pop-out-card {{
    animation: pop-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    background: rgba(6, 78, 59, 0.8) !important;
    border: 2px solid #10b981 !important;
    padding: 20px;
    border-radius: 20px;
    margin-top: 15px;
}}
@keyframes float {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-10px); }}
    100% {{ transform: translateY(0px); }}
}}
.robot-mascot {{
    animation: float 3s ease-in-out infinite;
    cursor: pointer;
    transition: transform 0.3s;
}}
.robot-mascot:hover {{
    transform: scale(1.1);
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# -----------------------------
# PAGE 1: Authentication Portal
# -----------------------------
def page_auth():
    cols = st.columns([1, 1.2, 1])
    with cols[1]:
        st.markdown(f"""
            <div class="glass-card" style="margin-top: 50px;">
                <div class="logo-container">
                    <span class="logo-icon">📈🌱</span>
                    <h1 class="logo-text">Rural Land Price Predictor</h1>
                </div>
        """, unsafe_allow_html=True)
        
        if st.session_state['auth_mode'] == 'login':
            st.markdown("### Strategic Sign In")
            email = st.text_input("Email Address", placeholder="e.g. admin@land.com", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button("Sign In to Lab", use_container_width=True):
                if email in st.session_state['users'] and st.session_state['users'][email]['password'] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['current_user'] = st.session_state['users'][email]
                    st.session_state['current_user']['email'] = email
                    navigate_to('dashboard')
                else:
                    st.error("❌ Authentication failed. Check your credentials.")
            
            st.markdown("<p style='margin-top: 20px;'>New to the platform?</p>", unsafe_allow_html=True)
            if st.button("Create an Account (Sign Up)", use_container_width=True):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()
        else:
            st.markdown("### Register New Asset Manager")
            reg_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name")
            reg_email = st.text_input("Email Address", placeholder="Enter your email address", key="reg_email")
            reg_pass = st.text_input("Password", type="password", placeholder="Create a secure password", key="reg_password")
            
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button("Sign Up & Create Account", use_container_width=True):
                if not reg_name or not reg_email or not reg_pass:
                    st.warning("⚠️ Please fill in all fields.")
                elif reg_email in st.session_state['users']:
                    st.error("❌ This email is already registered.")
                else:
                    st.session_state['users'][reg_email] = {"password": reg_pass, "name": reg_name}
                    save_users(st.session_state['users'])
                    st.success(f"🎊 Welcome {reg_name}! Account created. Please Sign In.")
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()
            
            st.markdown("<p style='margin-top: 20px;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Back to Sign In", use_container_width=True):
                st.session_state['auth_mode'] = 'login'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# PAGE 2: Strategic Dashboard
# -----------------------------
def page_dashboard():
    user_info = st.session_state['current_user']
    with st.sidebar:
        st.markdown("### 🛡️ Secure Session")
        st.caption(f"Member: **{user_info['name']}**")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.divider()
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        # Robot removed from sidebar per request
        st.markdown('<p style="color: #6ee7b7; font-weight: 700; margin-top: 10px;">🤖 AI Strategic Advisor</p>', unsafe_allow_html=True)
        if st.button("Click for Chat with AI Advisor", use_container_width=True):
            navigate_to('chatbot')
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

    st.title("🛡️ Rural land price prediction")
    st.markdown(f"<p style='font-size: 1.3rem; color: #a7f3d0; margin-top: -15px;'>Greetings, <b>{user_info['name']}</b>.</p>", unsafe_allow_html=True)

    MODEL_PATH = "model/land_price_model.pkl"
    ENCODER_PATH = "model/district_encoder.pkl"
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        st.error("🚨 Critical Error: ML components missing.")
        return

    model = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)
    district_list = list(le.classes_)

    with st.sidebar:
        st.header("📍 Strategic Parameters")
        district = st.selectbox("Market District", district_list)
        year = st.selectbox("Target Year", [2026, 2027, 2028, 2029, 2030])
        st.subheader("🧪 Molecular Soil Data")
        zn = st.number_input("Zinc %", min_value=0.0, value=0.8, step=0.01)
        fe = st.number_input("Iron %", min_value=0.0, value=1.2, step=0.01)
        cu = st.number_input("Copper %", min_value=0.0, value=0.4, step=0.01)
        mn = st.number_input("Manganese %", min_value=0.0, value=0.9, step=0.01)
        b = st.number_input("Boron %", min_value=0.0, value=0.3, step=0.01)
        s = st.number_input("Sulphur %", min_value=0.0, value=0.7, step=0.01)

    st.markdown('<h3 style="color: #10b981; margin-top: 25px;">🌍 Environmental Valuation Indices</h3>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        dist_road = st.selectbox("🛣️ Proximity Index", ["Highway Facing", "< 1 km", "1-5 km", "> 5 km"])
        water_source = st.selectbox("💧 Resource Stability", ["Borewell (High Yield)", "Borewell (Low Yield)", "Canal Irrigation", "Rainfed / None"])
        land_type = st.radio("🌱 Type", ["Wet (Irrigated)", "Dry (Rainfed)"], horizontal=True)
    with col_b:
        local_demand = st.select_slider("📈 Market Volatility", options=["Low", "Medium", "High", "Very High"])
        land_size = st.number_input("📐 Land Mass (Acres)", min_value=0.1, value=1.0, step=0.1)
        msp_support = st.radio("🏛️ Policy Support", ["Available", "Not Available"], horizontal=True)
    infra_dev = st.multiselect("🏗️ Future Infrastructure", ["Upcoming Highway", "SEZ Project", "Metro/Rail Expansion", "New Irrigation Canal"])
    plot_specifics = st.multiselect("📍 Site Specifics", ["Corner Plot", "Irregular Shape", "Litigation Free", "Power Connection Available"])
    
    # st.markdown('</div>', unsafe_allow_html=True) # REMOVED to fix empty box

    if st.button("🚀 Predict and validate price", type="primary", use_container_width=True):
        st.session_state['advisory_report'] = None 
        input_df = pd.DataFrame([{"District": district, "Year": year, "Zn_%": zn, "Fe_%": fe, "Cu_%": cu, "Mn_%": mn, "B_%": b, "S_%": s}])
        input_df["District"] = le.transform(input_df["District"])
        base_price = model.predict(input_df)[0]
        soil_data = {"Zn_%": zn, "Fe_%": fe, "Cu_%": cu, "Mn_%": mn, "B_%": b, "S_%": s}
        user_inputs = {"land_size_acres": land_size, "distance_to_road": dist_road, "water_source": water_source, "land_type": land_type, "msp_support": msp_support, "infra_developments": infra_dev, "local_demand": local_demand, "plot_specifics": plot_specifics}

        with st.spinner("🤖 Neural Engine Optimizing Data..."):
            ai_result = validate_price_with_ai(district, base_price, soil_data, year, user_inputs)

        final_price = ai_result.get("final_price", base_price)
        reasoning = ai_result.get("price_difference_reasoning", "Stabilized Valuation.")
        roi_5yr = ai_result.get("roi_5yr", 0)
        
        st.session_state['last_prediction'] = {
            "district": district, "year": year, "base_price": base_price, "final_price": final_price,
            "soil_data": soil_data, "user_inputs": user_inputs, "ai_result": ai_result, "roi_5yr": roi_5yr,
            "reasoning": reasoning
        }
        st.balloons()

    # Display results if they exist
    if st.session_state['last_prediction']:
        res = st.session_state['last_prediction']
        p1, p2 = st.columns(2)
        with p1: st.metric("📊 Model Forecast", f"₹ {res['base_price']:,.0f}")
        with p2: st.metric("✅ AI Optimized Price", f"₹ {res['final_price']:,.0f}", delta=f"₹ {res['final_price'] - res['base_price']:,.0f}")

        a1, a2 = st.columns(2)
        with a1: st.metric("📈 Growth Factor", f"{((res['final_price']/res['base_price'])-1)*100:+.1f}%")
        with a2: st.metric("💰 5-Year ROI", f"{res['roi_5yr']}%")
        st.info(f"**💡 Machine Intelligent Insights:** {res['reasoning']}")

        st.divider()
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("🌾 Bio-Potential Index")
            suitability = res['ai_result'].get("suitability", {})
            st.markdown(f"**Analysis:** <span style='color: #10b981;'>{suitability.get('type', 'Unknown')}</span>", unsafe_allow_html=True)
            st.markdown(f"**Index Score:** `{suitability.get('score', 0)}/100`")
            st.progress(suitability.get('score', 0) / 100)
            st.write(f"*Strategic Crops:* {', '.join([f'`{c}`' for c in suitability.get('crops', [])])}")
        with c2:
            st.subheader("💰 Investment Outlook")
            p_pot = res['ai_result'].get("profit_potential", {})
            st.markdown(f"**Rating:** `{p_pot.get('score', 0)} / 10` ⭐")
            st.markdown(f"**Indicator:** {p_pot.get('recommendation', '🟡 Hold')}")
            target_aud = res['ai_result'].get("target_audience", {})
            st.markdown(f"**Market Fit:** `{target_aud.get('suitable_for', 'Unknown')}`")
            st.write(f"*Justification:* {target_aud.get('reason', '')}")
        
        st.subheader("📉 Valuation Comparison")
        chart_data = pd.DataFrame({
            "Valuation Source": ["ML Model", "AI Refined"],
            "Price (₹)": [res['base_price'], res['final_price']]
        }).set_index("Valuation Source")
        st.bar_chart(chart_data, color="#10b981")

        st.divider()
        st.markdown("### 📋 Professional Advisory Services")
        if st.button("📄 Generate Professional Advisory Report", use_container_width=True, type="secondary"):
            with st.spinner("👨‍💼 Agricultural Land Investment Advisor is Preparing Your Report..."):
                report = generate_advisory_report(
                    res['district'], res['year'], res['final_price'],
                    res['soil_data'], res['user_inputs']
                )
                st.session_state['advisory_report'] = report
                navigate_to('report')


    st.caption("Strategic Intelligence for Rural Assets | Team 14 | LandPriceML Enterprise")

# -----------------------------
# PAGE 3: Professional Report
# -----------------------------
def page_report():
    res = st.session_state['last_prediction']
    report_content = st.session_state['advisory_report']
    
    if not res or not report_content:
        navigate_to('dashboard')
        return

    st.markdown('<div class="main-bg-overlay"></div>', unsafe_allow_html=True)
    
    # Navigation Header
    header_cols = st.columns([3, 1])
    with header_cols[1]:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            navigate_to('dashboard')

    st.markdown('<div class="premium-card" style="margin-top: 10px; border: none; background: transparent;">', unsafe_allow_html=True)
    st.markdown('<p class="report-title">👨‍💼 Professional Land Valuation Advisory Report</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="report-meta">Prepared for: <b>{st.session_state["current_user"]["name"]}</b> | Asset Location: <b>{res["district"]}</b> | Year: <b>{res["year"]}</b></p>', unsafe_allow_html=True)
    
    # Render the report content
    st.markdown(report_content)
    
    st.divider()
    st.caption("Strategic Advisor Analysis | Confidential Investment Report | Generated via GenAI Strategic Core")
    
    # --- FEEDBACK SECTION ---
    st.markdown('<div style="background: rgba(16, 185, 129, 0.05); border: 1px solid #10b981; padding: 25px; border-radius: 20px; margin-top: 30px;">', unsafe_allow_html=True)
    st.subheader("📝 User Feedback & Valuation Correction")
    
    # Use session state to track if correction is needed for dynamic UI
    is_accurate = st.radio(
        "Is this valuation and report accurate?", 
        ["Yes, accurately reflects market", "No, price needs correction", "Needs minor adjustments"], 
        horizontal=True,
        key="feedback_accuracy"
    )
    
    corrected_value = 0.0
    if st.session_state.get("feedback_accuracy") == "No, price needs correction":
        corrected_value = st.number_input(
            "What is the correct price per acre based on your local knowledge? (₹)", 
            min_value=0.0, 
            step=10000.0,
            key="feedback_corrected_price"
        )
            
    comments = st.text_area(
        "Observations or general app feedback (e.g., UI, logic, features)", 
        placeholder="Share your professional insights here...",
        key="feedback_comments"
    )
    
    if st.button("Commit Professional Feedback", type="primary", use_container_width=True):
        fd_data = {
            "user": st.session_state['current_user']['email'],
            "district": res["district"],
            "year": res["year"],
            "predicted_price": res["final_price"],
            "user_accurate": is_accurate,
            "corrected_price": corrected_value,
            "comments": comments,
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_feedback(fd_data)
        st.success("✅ Thank you! Your feedback has been recorded in our spreadsheet and will be used to improve our core model.")
    
    st.markdown('</div>', unsafe_allow_html=True) # Close feedback section
    
    # Secondary Back Button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏁 Return to Dashboard", key="bottom_back"):
        navigate_to('dashboard')
        
    st.markdown('</div>', unsafe_allow_html=True) # Total closure

def page_ai_advisory():
    advice_data = st.session_state['ai_advice']
    if not advice_data["response"]:
        navigate_to('dashboard')
        return

    st.markdown('<div class="main-bg-overlay"></div>', unsafe_allow_html=True)
    
    # Navigation Header
    header_cols = st.columns([3, 1])
    with header_cols[1]:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            navigate_to('dashboard')

    st.markdown('<div class="premium-card" style="margin-top: 20px;">', unsafe_allow_html=True)
    st.markdown(f'<h2>🤖 AI Strategic Consultation</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #6ee7b7; text-align: center;">Query: "<i>{advice_data["query"]}</i>"</p>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown(f'<div class="pop-out-card" style="background: rgba(6, 78, 59, 0.4); border: 1px solid #10b981;">{advice_data["response"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏁 Return to Dashboard", key="bottom_back_ai"):
        navigate_to('dashboard')
    st.markdown('</div>', unsafe_allow_html=True)

def page_chatbot():
    st.markdown('<div class="main-bg-overlay"></div>', unsafe_allow_html=True)
    
    # Navigation Header
    header_cols = st.columns([3, 1])
    with header_cols[1]:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            navigate_to('dashboard')

    st.markdown('<div class="premium-card" style="margin-top: 20px; text-align: left;">', unsafe_allow_html=True)
    st.markdown(f'<h2 style="text-align: center;">🤖 AI Strategic Advisor Chat</h2>', unsafe_allow_html=True)
    st.markdown(f'<p style="color: #6ee7b7; text-align: center;">Strategic consultations for rural assets.</p>', unsafe_allow_html=True)
    st.divider()

    # Display chat history
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about investment, land quality, or market trends..."):
        # Add user message to history
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate bot response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                response = get_chat_response(st.session_state['chat_history'])
                st.markdown(response)
        
        # Add bot response to history
        st.session_state['chat_history'].append({"role": "assistant", "content": response})

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# Main Routing Logic
# -----------------------------
if not st.session_state['authenticated']:
    page_auth()
else:
    if st.session_state['page'] == 'dashboard':
        page_dashboard()
    elif st.session_state['page'] == 'report':
        page_report()
    elif st.session_state['page'] == 'ai_advisory':
        page_ai_advisory()
    elif st.session_state['page'] == 'chatbot':
        page_chatbot()
    else:
        page_dashboard()
