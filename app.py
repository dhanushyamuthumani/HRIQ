import streamlit as st
import os
import logging
from datetime import datetime

# Basic Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
import tempfile
import pandas as pd
import time
import requests
import plotly.express as px
import concurrent.futures
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
from core.text_extractor import extract_text
from core.ai_engine import (
    analyze_resume, 
    generate_interview_questions, 
    generate_client_pitch, 
    generate_boolean_sourcing, 
    generate_candidate_comparison, 
    parse_natural_language_query
)
from core.sourcing_engine import (
    parse_sourcing_criteria,
    search_github_candidates,
    draft_github_outreach
)
from core.experience_logic import process_experience
from core.duplicate_checker import detect_duplicates
from core.domain_mapper import map_domain
from core.scoring_engine import process_scoring
from core.matcher_engine import match_candidate_to_jd
from core.workflow_engine import generate_email
from core.search_engine import search_candidates
from core.folder_processor import get_files_from_folder
from utils.excel_generator import generate_excel
from utils.diagnostics import run_system_check
from core.persistence import save_talent_data, load_talent_data
from config import SUPPORTED_EXTENSIONS, OLLAMA_MODEL

# State initialized in main() via st.session_state

# Page Configuration - Standard Professional
st.set_page_config(
    page_title="HRIQ | Talent Intelligence",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM MINIMAL LIGHT THEME (SHADCN/UI STYLE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --background: #FFFFFF;
        --foreground: #0F172A;
        --card: #FFFFFF;
        --card-foreground: #0F172A;
        --popover: #FFFFFF;
        --popover-foreground: #0F172A;
        --primary: #4F46E5;
        --primary-foreground: #FFFFFF;
        --secondary: #F1F5F9;
        --secondary-foreground: #0F172A;
        --muted: #F8FAFC;
        --muted-foreground: #64748B;
        --accent: #F1F5F9;
        --accent-foreground: #0F172A;
        --destructive: #EF4444;
        --destructive-foreground: #FFFFFF;
        --border: #E2E8F0;
        --input: #E2E8F0;
        --ring: #94A3B8;
        --radius: 0.75rem;
    }

    /* Global Reset & Base */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--background) !important;
        color: var(--foreground) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--foreground) !important;
        font-weight: 700 !important;
    }

    /* Premium App Background */
    .stApp {
        background: radial-gradient(circle at 100% 0%, #F5F3FF 0%, #FFFFFF 50%), 
                    radial-gradient(circle at 0% 100%, #EEF2FF 0%, #FFFFFF 50%) !important;
        background-attachment: fixed !important;
    }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border) !important;
        box-shadow: none !important;
    }

    /* Navigation Radio Group Overrides (Make it look like Shadcn Sidebar) */
    .stRadio div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 6px !important;
    }

    .stRadio div[role="radiogroup"] label {
        padding: 10px 14px !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: var(--muted-foreground) !important;
        background-color: transparent !important;
        border: none !important;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .stRadio div[role="radiogroup"] label:hover {
        background-color: #F8FAFC !important;
        color: var(--foreground) !important;
    }

    /* Active navigation state */
    .stRadio div[role="radiogroup"] label:has(input:checked) {
        background-color: #F1F5F9 !important;
    }
    .stRadio div[role="radiogroup"] label:has(input:checked) p {
        color: var(--foreground) !important;
        font-weight: 600 !important;
    }
    
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        font-size: 0.92rem !important;
        margin: 0 !important;
    }

    /* Hide the radio button circle */
    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* Premium Card & Native Container Styling */
    .premium-card, div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 20px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* Override padding inside Streamlit's native containers */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 20px !important;
    }

    .premium-card:hover, div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05) !important;
    }

    /* Shadcn Badges */
    .shadcn-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 9999px;
        border: 1px solid var(--border);
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1;
        margin-right: 6px;
        margin-bottom: 6px;
        transition: all 0.2s;
    }
    
    .shadcn-badge-primary {
        background-color: var(--foreground);
        color: var(--background);
        border-color: transparent;
    }

    .shadcn-badge-secondary {
        background-color: var(--secondary);
        color: var(--secondary-foreground);
    }

    .shadcn-badge-success {
        background-color: #ECFDF5;
        color: #047857;
        border-color: #A7F3D0;
    }

    .shadcn-badge-warning {
        background-color: #FFFBEB;
        color: #B45309;
        border-color: #FDE68A;
    }

    .shadcn-badge-destructive {
        background-color: #FEF2F2;
        color: #B91C1C;
        border-color: #FCA5A5;
    }

    /* Circular Score Gauge */
    .score-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 10px;
    }

    .score-circle {
        position: relative;
        width: 110px;
        height: 110px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
        box-shadow: inset 0 0 0 10px #F1F5F9;
    }

    .score-value {
        font-size: 1.75rem;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--foreground);
    }

    /* Chat Bubbles Revamp */
    .bubble {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        line-height: 1.5;
        font-size: 0.92rem;
        max-width: 80%;
    }

    .bubble-user {
        background-color: var(--foreground) !important;
        color: var(--background) !important;
        border-bottom-right-radius: 2px;
        align-self: flex-end;
    }

    .bubble-ai {
        background-color: var(--card) !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border);
        border-bottom-left-radius: 2px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    /* Buttons Overrides */
    .stButton > button, .stDownloadButton > button {
        border-radius: 6px !important;
        padding: 6px 14px !important;
        background-color: #FFFFFF !important;
        color: var(--foreground) !important;
        border: 1px solid var(--border) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer;
        width: auto !important;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #F8FAFC !important;
        border-color: #CBD5E1 !important;
        color: var(--foreground) !important;
    }

    /* Primary buttons */
    .stButton > button[type="primary"], .stButton > button[kind="primary"] {
        background-color: var(--foreground) !important;
        color: var(--background) !important;
        border: 1px solid transparent !important;
    }

    .stButton > button[type="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background-color: #1E293B !important;
        color: var(--background) !important;
    }

    /* Forms Inputs Styling */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[role="combobox"] {
        border-radius: 6px !important;
        border: 1px solid var(--border) !important;
        background-color: #FFFFFF !important;
        color: var(--foreground) !important;
        padding: 8px 12px !important;
        font-size: 0.9rem !important;
        box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02) !important;
        transition: all 0.15s ease !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--ring) !important;
        box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.15) !important;
        outline: none !important;
    }

    /* Tab Overrides */
    div[role="tablist"] {
        border-bottom: 1px solid var(--border) !important;
        gap: 16px !important;
        padding-bottom: 0px !important;
    }

    button[role="tab"] {
        border: none !important;
        background-color: transparent !important;
        color: var(--muted-foreground) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 10px 4px !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0px !important;
        transition: all 0.2s !important;
    }

    button[role="tab"]:hover {
        color: var(--foreground) !important;
    }

    button[role="tab"][aria-selected="true"] {
        color: var(--foreground) !important;
        border-bottom: 2px solid var(--foreground) !important;
        font-weight: 600 !important;
    }

    /* Progress Indicators */
    .stProgress > div > div > div > div {
        background-color: var(--foreground) !important;
    }

    /* Hide standard headers */
    header, footer { visibility: hidden; }

    /* Brand Logo Text */
    .brand-text {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        color: var(--foreground);
        font-size: 1.4rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

def render_custom_tabs(tabs_list, key_prefix):
    """
    Renders premium, state-persisted tab switchers that look like Shadcn Segmented Control.
    Avoids Streamlit's default tab-resetting bug on page reruns.
    """
    state_key = f"{key_prefix}_active_tab"
    if state_key not in st.session_state:
        st.session_state[state_key] = tabs_list[0]
        
    cols = st.columns(len(tabs_list))
    for idx, name in enumerate(tabs_list):
        is_active = (st.session_state[state_key] == name)
        if cols[idx].button(
            name, 
            key=f"{key_prefix}_tab_{idx}", 
            use_container_width=True, 
            type="primary" if is_active else "secondary"
        ):
            st.session_state[state_key] = name
            st.rerun()
    return st.session_state[state_key]

def render_candidate_profile_card(c_data):
    # Let's create visual metrics first
    col_info_1, col_info_2, col_info_3, col_info_4 = st.columns(4)
    with col_info_1:
        st.metric("Working Role", c_data['working_role'])
    with col_info_2:
        st.metric("Total Experience", f"{c_data.get('total_experience_years', 0)} Years")
    with col_info_3:
        st.metric("Industry Domain", c_data.get('industry_domain', 'Other'))
    with col_info_4:
        # Custom Gauge circle for Score
        score = c_data.get('resume_score', 0)
        st.markdown(f"""
        <div class="score-container">
            <div class="score-circle" style="background: conic-gradient(#4F46E5 calc({score} * 1%), #E2E8F0 0);">
                <span class="score-value" style="position: relative; z-index: 10;">{score}</span>
            </div>
            <span style="font-size:0.8rem;color:#64748B;font-weight:500;">Resume Score</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabbed interface inside the deep dive
    active_detail_tab = render_custom_tabs(["📝 Overview", "💼 Client Pitch", "🎤 Interview Prep", "🎯 Job Fit Analyzer"], f"detail_{c_data['full_name']}")
    
    if active_detail_tab == "📝 Overview":
        st.markdown(f"### Profile Overview: {c_data['full_name']}")
        st.write(f"**Contact Info:** 📧 {c_data['email']} | 📞 {c_data['phone']}")
        st.write(f"**Tag Reference:** `{c_data['tag']}` | **Source File:** `{c_data.get('source_file', 'Direct Upload')}`")
        
        st.markdown("##### Technologies & Tools")
        techs = c_data.get("technologies", [])
        if techs:
            badges_html = "".join([f'<span class="shadcn-badge shadcn-badge-secondary">{t}</span>' for t in techs])
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.write("None listed")
            
        st.markdown("##### Professional Summary")
        st.write(c_data.get("summary", "N/A"))
        
        st.markdown("##### Elevator Pitch")
        st.info(c_data.get("elevator_pitch", "N/A"))
        
        st.markdown("##### Core Technical Evaluation")
        st.success(c_data.get('technical_evaluation', 'Assessment pending...'))
        
    elif active_detail_tab == "💼 Client Pitch":
        st.markdown("#### AI Client-Ready Pitch")
        st.caption("A formatted summary highlighting candidate value proposition without exposing personal details.")
        
        pitch_key = f"pitch_{c_data['full_name']}"
        if pitch_key not in st.session_state:
            st.session_state[pitch_key] = ""
            
        if not st.session_state[pitch_key]:
            if st.button("✨ Generate Client Pitch", key=f"btn_pitch_{c_data['full_name']}"):
                with st.spinner("Writing elevator summary..."):
                    st.session_state[pitch_key] = generate_client_pitch(c_data)
                st.rerun()
        else:
            st.markdown(st.session_state[pitch_key])
            if st.button("🔄 Regenerate Pitch", key=f"btn_pitch_regen_{c_data['full_name']}"):
                st.session_state[pitch_key] = ""
                st.rerun()

    elif active_detail_tab == "🎤 Interview Prep":
        st.markdown("#### Tailored Interview Guide")
        st.caption("5 specific questions and expected model answers customized to this candidate.")
        
        guide_key = f"guide_{c_data['full_name']}"
        if guide_key not in st.session_state:
            st.session_state[guide_key] = ""
            
        if not st.session_state[guide_key]:
            if st.button("✨ Generate Technical Guide", key=f"btn_guide_{c_data['full_name']}"):
                with st.spinner("Generating targeted questions..."):
                    st.session_state[guide_key] = generate_interview_questions(c_data)
                st.rerun()
        else:
            st.markdown(st.session_state[guide_key])
            if st.button("🔄 Regenerate Guide", key=f"btn_guide_regen_{c_data['full_name']}"):
                st.session_state[guide_key] = ""
                st.rerun()

    elif active_detail_tab == "🎯 Job Fit Analyzer":
        st.markdown("#### Interactive JD Match & Gap Analyzer")
        jd_text = st.text_area("Paste target Job Description:", placeholder="Paste key requirements for the candidate...", key=f"jd_input_{c_data['full_name']}")
        
        if jd_text:
            if st.button("⚡ Run Gap Analysis", key=f"btn_gap_{c_data['full_name']}"):
                with st.spinner("Comparing profiles..."):
                    match_res = match_candidate_to_jd(c_data, jd_text)
                    st.session_state[f"match_{c_data['full_name']}"] = match_res
                st.rerun()
        
        match_result = st.session_state.get(f"match_{c_data['full_name']}")
        if match_result:
            match_score = match_result.get("match_score", 0)
            st.markdown("---")
            col_res_1, col_res_2 = st.columns([1, 3])
            with col_res_1:
                st.markdown(f"""
                <div class="score-container" style="background:#F8FAFC; border-radius:12px; padding:15px; border:1px solid #E2E8F0;">
                    <div class="score-circle" style="background: conic-gradient(#10B981 calc({match_score} * 1%), #E2E8F0 0);">
                        <span class="score-value" style="color:#059669; position: relative; z-index: 10;">{match_score}%</span>
                    </div>
                    <span style="font-size:0.85rem;color:#0F172A;font-weight:600;">Match Fit</span>
                </div>
                """, unsafe_allow_html=True)
            with col_res_2:
                st.markdown(f"**Explanation:** {match_result.get('explanation', '')}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_lists_1, col_lists_2 = st.columns(2)
            with col_lists_1:
                st.markdown("##### ✅ Matching Strengths / Skills")
                matching = match_result.get("matching_skills", [])
                if matching:
                    matching_html = "".join([f'<span class="shadcn-badge shadcn-badge-success">{s}</span>' for s in matching])
                    st.markdown(matching_html, unsafe_allow_html=True)
                else:
                    st.write("No direct matching skills listed.")
            with col_lists_2:
                st.markdown("##### ⚠️ Missing Gaps / Skills")
                missing = match_result.get("missing_skills", [])
                if missing:
                    missing_html = "".join([f'<span class="shadcn-badge shadcn-badge-destructive">{s}</span>' for s in missing])
                    st.markdown(missing_html, unsafe_allow_html=True)
                else:
                    st.write("No critical gaps detected.")
    
    with st.expander("📄 View Extracted Text Preview"):
        st.text(c_data.get('raw_text', 'No preview available.'))

def main():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = load_talent_data()
    if 'queue' not in st.session_state:
        st.session_state.queue = []
    sys_status = run_system_check()
    if 'sys_status' not in st.session_state:
        st.session_state.sys_status = sys_status
    if 'uploader_visible' not in st.session_state:
        st.session_state.uploader_visible = False
    if 'folder_visible' not in st.session_state:
        st.session_state.folder_visible = False
    if 'selected_candidates' not in st.session_state:
        st.session_state.selected_candidates = []
    if 'jobs' not in st.session_state:
        st.session_state.jobs = {
            "active": False, "progress": 0.0, "status": "Inactive", 
            "current_file": "", "stop": False
        }
    if 'parsing_history' not in st.session_state:
        st.session_state.parsing_history = []
    if 'data_changed' not in st.session_state:
        st.session_state.data_changed = True # Initialize as true to ensure first load works

    # Sidebar
    with st.sidebar:
        col_logo_l, col_logo_c, col_logo_r = st.columns([1, 4, 1])
        with col_logo_c:
            st.image("logo.png", width=140)
        st.markdown("<br>", unsafe_allow_html=True)
        page = st.radio(
            "Navigation", 
            ["📤 Intake Hub", "🤖 AI Assistant", "📊 Talent Hub", "🌐 Web Sourcing", "📜 Parsing Tracker", "⚡ Bulk Actions", "🛡️ System Status"],
            index=0,
            key="main_nav"
        )
        st.markdown("---")
        
        # Live Status Widget
        status = st.session_state.sys_status
        if status['all_clear']:
            st.success("🟢 AI Connected")
        else:
            st.error("🔴 AI Offline")
            if st.button("Reconnect"):
                st.session_state.sys_status = run_system_check()
                st.rerun()
        
        # --- JOB MONITOR & DEDUPLICATION ---
        while st.session_state.queue:
            new_res = st.session_state.queue.pop(0)
            # Real-time Deduplication Logic
            existing_emails = {c.get('email') for c in st.session_state.processed_data if c.get('email') and c.get('email') != 'N/A'}
            existing_phones = {c.get('phone') for c in st.session_state.processed_data if c.get('phone') and c.get('phone') != 'N/A'}
            
            is_dup = (new_res.get('email') in existing_emails or new_res.get('phone') in existing_phones)
            
            if not is_dup:
                st.session_state.processed_data.append(new_res)
                save_talent_data(st.session_state.processed_data)
                st.session_state.data_changed = True # Signal that new data has arrived
            else:
                logger.info(f"Deduplicator: Skipped existing candidate {new_res.get('full_name')}")

        if st.session_state.jobs["active"]:
            st.markdown("---")
            st.markdown(f"##### ⚡ Processing: {st.session_state.jobs['status']}")
            st.progress(st.session_state.jobs["progress"])
            if st.session_state.jobs["current_file"]:
                st.caption(f"📄 Analyzing: **{st.session_state.jobs['current_file']}**")
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                if st.button("🔄 Sync", key="sync_job"): st.rerun()
            with c_r2:
                if st.button("🛑 Kill", key="global_kill", type="primary"):
                    st.session_state.jobs["stop"] = True

    # Routing
    if page == "📤 Intake Hub":
        render_intake_hub()
    elif page == "🤖 AI Assistant":
        render_assistant_v4()
    elif page == "📊 Talent Hub":
        render_talent_hub_v4()
    elif page == "🌐 Web Sourcing":
        render_web_sourcing()
    elif page == "📜 Parsing Tracker":
        render_parsing_tracker_v4()
    elif page == "⚡ Bulk Actions":
        render_bulk_actions()
    elif page == "🛡️ System Status":
        render_status_v4()

    # --- GLOBAL LIVE REFRESH (Non-blocking) ---
    if st.session_state.jobs["active"]:
        time.sleep(5.0) # Increased to 5s to reduce flicker
        st.rerun()

def render_intake_hub():
    st.markdown("<h2 style='font-weight: 700;'>Intake Hub</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280;'>Ingest and categorize resumes into your talent repository.</p>", unsafe_allow_html=True)
    
    active_tab = render_custom_tabs(["📂 Batch Upload", "📁 Folder Scan"], "intake")
    
    if active_tab == "📂 Batch Upload":
        with st.container(border=True):
            st.markdown("### 📤 Resource Integration")
            tag_val = st.text_input("Name this batch (Tag)", value="Global", key="hub_upload_tag")
            files = st.file_uploader("Upload resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)
            if files:
                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    btn_label = "🚀 Processing..." if st.session_state.jobs["active"] else "🚀 Execute Parallel Pipeline"
                    if st.button(btn_label, disabled=st.session_state.jobs["active"], key="run_p"):
                        run_pipeline_parallel(files, tag_val)
                with col_b2:
                    if st.button("🛑 Terminate", key="term_p", type="primary") if st.session_state.jobs["active"] else None:
                        st.session_state.jobs["stop"] = True
                        st.warning("Termination signal sent... Finishing current file.")
                
    elif active_tab == "📁 Folder Scan":
        with st.container(border=True):
            st.markdown("### 📁 Recursive Folder Intelligence")
            tag_val_folder = st.text_input("Name this folder collection (Tag)", value="Global", key="hub_folder_tag")
            folder_path = st.text_input("Enter absolute folder path", placeholder="e.g., C:\\Users\\Name\\Documents\\Resumes")
            if folder_path:
                found_files = get_files_from_folder(folder_path, SUPPORTED_EXTENSIONS)
                if found_files:
                    st.success(f"Found {len(found_files)} potential resumes.")
                    col_f1, col_f2 = st.columns([1, 1])
                    with col_f1:
                        f_btn_label = "⏳ Scanning..." if st.session_state.jobs["active"] else "⚡ Deep Scan (Turbo)"
                        if st.button(f_btn_label, disabled=st.session_state.jobs["active"], key="run_f"):
                            run_folder_pipeline_parallel(found_files, tag_val_folder)
                    with col_f2:
                        if st.button("🛑 Terminate Scan", key="term_f", type="primary") if st.session_state.jobs["active"] else None:
                            st.session_state.jobs["stop"] = True
                            st.warning("Termination signal sent...")
                else:
                    st.warning("No supported files found.")

def render_assistant_v4():
    st.markdown("<h2 style='font-weight: 700;'>🤖 AI Assistant (HRIQ Copilot)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280;'>Ask queries, compare candidates, or search your local database in natural language.</p>", unsafe_allow_html=True)
    
    # Hide the radio circle dot using CSS overrides
    st.markdown("""
        <style>
        div[role="radiogroup"] label > div:first-child {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Context Selectbox
    if st.session_state.processed_data:
        all_tags = sorted(list(set(c.get('tag', 'Global') for c in st.session_state.processed_data)))
        c_ctx_1, c_ctx_2 = st.columns([1, 4])
        with c_ctx_1:
            st.markdown("<span style='font-weight:600;font-size:0.9rem;display:inline-block;padding-top:10px;'>🎯 Search Context:</span>", unsafe_allow_html=True)
        with c_ctx_2:
            selected_context = st.selectbox("Focus assistant on:", ["Complete Hub"] + all_tags, index=0, label_visibility="collapsed")
    else:
        selected_context = "Complete Hub"

    st.markdown("---")

    # Render Chat Messages in standard Streamlit chat interface (ChatGPT style!)
    for msg_idx, msg in enumerate(st.session_state.history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # If the assistant message contains structured candidates, render them as custom cards!
            if msg.get("candidates"):
                st.markdown("<br>**Matching Profiles Found:**", unsafe_allow_html=True)
                for idx, cand in enumerate(msg["candidates"]):
                    # Premium Candidate Card
                    st.markdown(f"""
                    <div class="premium-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                            <div>
                                <h4 style="margin: 0; font-size: 1.1rem; color: #0F172A;">{cand['full_name']}</h4>
                                <p style="margin: 4px 0; color: #64748B; font-size: 0.88rem;">📍 {cand.get('location', 'N/A')} | 🏢 {cand.get('company', 'N/A')}</p>
                                <p style="margin: 4px 0; font-weight: 500; font-size: 0.9rem; color: #4F46E5;">{cand['working_role']} ({cand.get('total_experience_years', 0)} yrs exp)</p>
                            </div>
                            <div class="score-container" style="padding: 0;">
                                <div class="score-circle" style="width: 70px; height: 70px; font-size: 1.1rem; background: conic-gradient(#4F46E5 calc({cand['resume_score']} * 1%), #E2E8F0 0);">
                                    <span class="score-value" style="font-size: 1.1rem; z-index: 10;">{cand['resume_score']}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Embed details in an expander inside the card!
                    with st.expander(f"🔍 View {cand['full_name']}'s Bio & Assessment", expanded=False):
                        st.markdown(f"**Bio Summary:** {cand.get('summary', 'N/A')}")
                        st.markdown(f"**Technologies:**")
                        techs = cand.get("technologies", [])
                        if techs:
                            badges_html = "".join([f'<span class="shadcn-badge shadcn-badge-secondary">{t}</span>' for t in techs])
                            st.markdown(badges_html, unsafe_allow_html=True)
                        else:
                            st.write("None listed")
                        st.markdown(f"**Technical Evaluation:**")
                        st.success(cand.get('technical_evaluation', 'Assessment pending...'))
                        st.markdown(f"📧 **Contact:** {cand.get('email')} | 📞 {cand.get('phone')}")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("<span style='font-size: 0.85rem; font-weight: 600; color: #64748B;'>⚡ Quick Actions</span>", unsafe_allow_html=True)
                        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                        with col_b1:
                            if st.button("💼 Client Pitch", key=f"chat_pitch_{msg_idx}_{cand['full_name']}_{idx}"):
                                with st.spinner(f"Writing pitch for {cand['full_name']}..."):
                                    pitch = generate_client_pitch(cand)
                                    st.session_state.history.append({
                                        "role": "assistant",
                                        "content": f"### 💼 AI Client Pitch for **{cand['full_name']}**\n\n{pitch}"
                                    })
                                st.rerun()
                        with col_b2:
                            if st.button("🎤 Interview Prep", key=f"chat_guide_{msg_idx}_{cand['full_name']}_{idx}"):
                                with st.spinner(f"Writing interview prep for {cand['full_name']}..."):
                                    guide = generate_interview_questions(cand)
                                    st.session_state.history.append({
                                        "role": "assistant",
                                        "content": f"### 🎤 Interview Prep Guide for **{cand['full_name']}**\n\n{guide}"
                                    })
                                st.rerun()
                        with col_b3:
                            if st.button("📧 Email Pitch", key=f"chat_email_{msg_idx}_{cand['full_name']}_{idx}"):
                                with st.spinner(f"Drafting outreach email for {cand['full_name']}..."):
                                    email_text = generate_email(cand, "A premium opportunity matching their experience")
                                    st.session_state.history.append({
                                        "role": "assistant",
                                        "content": f"### 📧 Outreach Email for **{cand['full_name']}**\n\n```email\n{email_text}\n```"
                                    })
                                st.rerun()
                        with col_b4:
                            already_shortlisted = cand['full_name'] in st.session_state.selected_candidates
                            shortlist_btn_text = "✅ Selected" if already_shortlisted else "➕ Select Profile"
                            if st.button(shortlist_btn_text, key=f"chat_shortlist_{msg_idx}_{cand['full_name']}_{idx}"):
                                if cand['full_name'] not in st.session_state.selected_candidates:
                                    st.session_state.selected_candidates.append(cand['full_name'])
                                else:
                                    st.session_state.selected_candidates.remove(cand['full_name'])
                                st.rerun()

    # Chat input
    query = st.chat_input("Tell me what you need (e.g. 'Show me AI engineers' or 'Who has React experience?')...")
    
    if query:
        st.session_state.history.append({"role": "user", "content": query})
        with st.spinner("HRIQ Copilot is analyzing..."):
            response_text, matches = handle_ai_response(query, selected_context)
            # Store both text response and matching candidate cards in history!
            st.session_state.history.append({
                "role": "assistant", 
                "content": response_text,
                "candidates": matches if matches else None
            })
        st.rerun()

def handle_ai_response(q, context):
    """Refined AI Logic: Parses query intent and returns (response_text, matching_candidates)."""
    q_low = q.lower()
    
    # 1. DATA FILTERING
    data = st.session_state.processed_data
    if context != "Complete Hub":
        data = [c for c in data if c.get('tag') == context]

    # Quick Keyword Actions
    if len(q_low.split()) < 4:
        if "upload" in q_low and "resume" in q_low:
            st.session_state.uploader_visible = True
            return "Of course. I've activated the **Upload Center** for you.", []
        if "folder" in q_low and "scan" in q_low:
            st.session_state.folder_visible = True
            return "Folder processing mode enabled. Use the panel above.", []

    # Check if query is a candidate search query
    is_search = False
    search_keywords = ["need", "find", "show", "search", "who has", "experience", "years", "developer", "engineer", "specialist", "candidate", "resume", "cv"]
    if any(kw in q_low for kw in search_keywords) or len(q_low.split()) >= 3:
        is_search = True

    matches = []
    if is_search and data:
        # Extract search parameters semantically
        criteria = parse_natural_language_query(q)
        if criteria and (criteria.get("role_keyword") or criteria.get("skills") or criteria.get("min_experience")):
            # Apply criteria to find matches
            matches = data.copy()
            if criteria.get("role_keyword"):
                role_kw = criteria["role_keyword"].lower()
                matches = [c for c in matches if role_kw in c.get('working_role', '').lower() or role_kw in c.get('one_liner', '').lower() or role_kw in c.get('summary', '').lower()]
            if criteria.get("skills"):
                for skill in criteria["skills"]:
                    skill_kw = skill.lower()
                    matches = [c for c in matches if isinstance(c.get('technologies'), list) and any(skill_kw in str(t).lower() for t in c.get('technologies', []))]
            if criteria.get("min_experience") and criteria["min_experience"] > 0:
                matches = [c for c in matches if float(c.get('total_experience_years', 0)) >= criteria["min_experience"]]
            if criteria.get("domain") and criteria["domain"].lower() != "other" and criteria["domain"] != "":
                domain_kw = criteria["domain"].lower()
                matches = [c for c in matches if c.get('industry_domain', '').lower() == domain_kw]

    # Generate LLM response text
    if not data:
        return f"I am currently looking at the **{context}** view, but it's empty. Please ingest some resumes first!", []

    # Build context summary for the LLM
    talent_summary = ""
    # If we have matches, prioritize listing details of the matches for the LLM
    list_source = matches if matches else data
    for i, c in enumerate(list_source[:15]): # Limit to top 15
        talent_summary += f"- {c['full_name']} | Role: {c['working_role']} | Score: {c.get('resume_score', 0)}/100 | Exp: {c.get('total_experience_years', 0)} years | Skills: {', '.join(c.get('technologies', []))}\n"
    
    system_prompt = f"""
    You are 'HRIQ Brain', an elite AI recruitment copilot.
    Analyze the current talent context and candidate profiles below to write a concise, professional answer to the user's query.
    
    CONTEXT: {context}
    CANDIDATES DETAILS:
    {talent_summary}
    
    USER QUERY: {q}
    
    INSTRUCTIONS:
    1. If the user is asking to find/search candidates and we found matches, write a brief 2-sentence intro introducing the matches.
    2. If they are comparing or asking for senior profiles, analyze their experience and resume scores.
    3. Keep your response conversational, precise, and professional. Do NOT output raw JSON or code unless asked.
    4. Be brief. Maximum 150 words.
    """
    
    try:
        from config import get_ollama_client
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=system_prompt,
            options={"temperature": 0.2, "num_predict": 256}
        )
        response_text = response.get('response', "I'm sorry, I couldn't process that request.")
        return response_text, matches
    except Exception as e:
        logger.error(f"Assistant LLM Error: {e}")
        if matches:
            return f"Here are the matching candidates I found in your **{context}** talent pool:", matches
        return f"My reasoning engine is offline. I see {len(data)} candidates in your **{context}** view.", []

def process_single_file(path, tag, source_name=None, source_type="Individual"):
    """Worker function for parallel processing. Thread-safe: returns history metadata."""
    fname = source_name or os.path.basename(path)
    history_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "type": source_type,
        "file": fname,
        "path": os.path.dirname(path) if source_type == "Folder" else "Direct Upload",
        "status": "Started",
        "details": "Initializing..."
    }
    
    try:
        logger.info(f"--- Starting Analysis: {fname} ---")
        txt = extract_text(path)
        res = analyze_resume(txt, filename=fname)
        if res:
            res = process_experience(res)
            res = process_scoring(res)
            res["industry_domain"] = map_domain(res.get("industry_domain", ""))
            res["source_file"] = fname
            res["tag"] = tag
            res["raw_text"] = txt[:2000]
            
            history_entry["status"] = "Success"
            history_entry["details"] = f"Parsed as {res['full_name']}"
            return res, history_entry
        else:
            history_entry["status"] = "Failed"
            history_entry["details"] = "AI extraction returned no data."
            return None, history_entry
    except Exception as e:
        logger.error(f"Parallel Worker Error ({fname}): {e}")
        history_entry["status"] = "Error"
        history_entry["details"] = str(e)
        return None, history_entry

def run_folder_pipeline_parallel(file_paths, tag):
    """Wrapper to launch the background folder worker."""
    if st.session_state.jobs["active"]:
        st.warning("A processing job is already in progress.")
        return

    st.session_state.jobs["active"] = True
    st.session_state.jobs["progress"] = 0.0
    st.session_state.jobs["stop"] = False
    st.session_state.jobs["status"] = f"Turbo Scanning to '{tag}'..."
    
    # Launch background thread with context
    thread = threading.Thread(
        target=background_pipeline_worker, 
        args=(file_paths, tag, st.session_state.jobs, st.session_state.queue),
        daemon=True
    )
    add_script_run_ctx(thread) # CRITICAL: Allows thread to see Streamlit context
    thread.start()
    st.success("Background Engine started. Switch tabs or chat while I work.")

def background_pipeline_worker(file_paths, tag, job_ref, queue_ref):
    """Deep Background Worker - Independent of Session Context."""
    total = len(file_paths)
    results_added = 0
    
    # Stable Concurrency: Limit to 2 for background reliability
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_path = {executor.submit(process_single_file, path, tag, source_type="Folder"): path for path in file_paths}
        pending = set(future_to_path.keys())
        
        while pending:
            # Check for global stop signal AT START of each polling cycle
            if job_ref["stop"]:
                for f in pending: f.cancel()
                job_ref["status"] = "Process Terminated."
                job_ref["active"] = False
                return

            # Update current file display from pending set
            if pending:
                next_future = list(pending)[0]
                job_ref["current_file"] = os.path.basename(future_to_path[next_future])

            # Wait for any future to complete, but timeout every 1s to check stop signal
            done, pending = concurrent.futures.wait(pending, timeout=1.0, return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                path = future_to_path[future]
                try:
                    res, history = future.result(timeout=1.0) 
                    if history:
                        st.session_state.parsing_history.insert(0, history)
                    if res:
                        queue_ref.append(res)
                        results_added += 1
                        # Removed: redundant append to processed_data here to prevent duplication
                except Exception as e:
                    logger.error(f"File Error ({os.path.basename(path)}): {e}")
                
                # Update progress after each completion
                finished_count = total - len(pending)
                job_ref["progress"] = finished_count / total
                job_ref["status"] = f"Scanned {finished_count}/{total}"

    # Final Polish
    job_ref["active"] = False
    job_ref["current_file"] = ""
    job_ref["status"] = f"Completed: {results_added} integrated."

def run_pipeline_parallel(files, tag):
    """Direct Upload Worker."""
    if st.session_state.jobs["active"]:
        st.warning("System busy...")
        return

    st.session_state.jobs["active"] = True
    st.session_state.jobs["progress"] = 0.0
    st.session_state.jobs["stop"] = False
    st.session_state.jobs["status"] = f"Turbo Uploading to '{tag}'..."
    
    total = len(files)
    temp_files = []
    for f in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.name)[1]) as tmp:
            tmp.write(f.getvalue())
            temp_files.append((tmp.name, f.name))

    thread = threading.Thread(
        target=background_upload_worker,
        args=(temp_files, tag, st.session_state.jobs, st.session_state.queue),
        daemon=True
    )
    add_script_run_ctx(thread)
    thread.start()
    st.success(f"Background Upload Engine started for {total} files.")

def background_upload_worker(temp_files, tag, job_ref, queue_ref):
    total = len(temp_files)
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_file = {executor.submit(process_single_file, path, tag, name, source_type="Upload"): (path, name) for path, name in temp_files}
        pending = set(future_to_file.keys())
        
        while pending:
            if job_ref["stop"]:
                for f in pending: f.cancel()
                job_ref["status"] = "Upload Terminated."
                job_ref["active"] = False
                break

            done, pending = concurrent.futures.wait(pending, timeout=1.0, return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                try:
                    res, history = future.result(timeout=1.0)
                    if history:
                        st.session_state.parsing_history.insert(0, history)
                    if res:
                        queue_ref.append(res)
                        count += 1
                        # Removed: redundant append to processed_data here to prevent duplication
                except Exception as e:
                    logger.error(f"Upload Error: {e}")
                
                finished_count = total - len(pending)
                job_ref["progress"] = finished_count / total
                job_ref["status"] = f"Uploaded {finished_count}/{total}"

    # Final Polish
    job_ref["active"] = False
    job_ref["status"] = f"Completed: {count} added."

    # Cleanup
    for path, _ in temp_files:
        if os.path.exists(path): os.remove(path)
    
    # Synchronization
    job_ref["active"] = False
    job_ref["status"] = f"Upload Complete: {count} added."

def render_talent_hub_v4():
    st.markdown("<h2 style='font-weight: 700;'>Talent Hub</h2>", unsafe_allow_html=True)
    
    if not st.session_state.processed_data:
        st.info("No talent data available. Go to Intake Hub to start scanning!")
        return

    # Run duplicate detection ONLY if data has changed
    if st.session_state.data_changed:
        st.session_state.processed_data = detect_duplicates(st.session_state.processed_data)
        st.session_state.data_changed = False # Reset flag after processing
    
    df_all = pd.DataFrame(st.session_state.processed_data)
    
    # 🔍 Semantic Search Input
    st.markdown("### 🔍 Semantic Talent Search")
    c_search_1, c_search_2, c_search_3 = st.columns([8, 1.2, 1.2])
    with c_search_1:
        nl_query = st.text_input(
            "Search candidate database with natural language queries:",
            placeholder="e.g., 'React developer with 3+ years experience' or 'Senior Engineer'",
            label_visibility="collapsed",
            key="nl_search_query"
        )
    with c_search_2:
        run_search = st.button("Search", type="primary", use_container_width=True, key="nl_search_btn")
    with c_search_3:
        clear_search = st.button("Reset", use_container_width=True, key="nl_clear_btn")

    if clear_search:
        st.session_state.search_criteria = None
        st.rerun()

    if run_search and nl_query:
        with st.spinner("Analyzing search intent..."):
            st.session_state.search_criteria = parse_natural_language_query(nl_query)
        st.rerun()

    # Apply semantic search criteria if active
    df = df_all.copy()
    if 'search_criteria' in st.session_state and st.session_state.search_criteria:
        criteria = st.session_state.search_criteria
        st.info(f"Active search filter: {criteria}")
        
        # 1. Filter by role keyword
        if criteria.get("role_keyword"):
            role_kw = criteria["role_keyword"].lower()
            df = df[df['working_role'].str.lower().str.contains(role_kw, na=False) | 
                    df['one_liner'].str.lower().str.contains(role_kw, na=False) |
                    df['summary'].str.lower().str.contains(role_kw, na=False)]
            
        # 2. Filter by skills
        if criteria.get("skills"):
            for skill in criteria["skills"]:
                skill_kw = skill.lower()
                df = df[df['technologies'].apply(lambda techs: any(skill_kw in str(t).lower() for t in techs) if isinstance(techs, list) else False)]
                
        # 3. Filter by experience
        if criteria.get("min_experience") and criteria["min_experience"] > 0:
            df = df[df['total_experience_years'] >= criteria["min_experience"]]
            
        # 4. Filter by domain
        if criteria.get("domain") and criteria["domain"].lower() != "other" and criteria["domain"] != "":
            domain_kw = criteria["domain"].lower()
            df = df[df['industry_domain'].str.lower() == domain_kw]

    # Tag Filter & Management
    all_tags = sorted(df['tag'].unique().tolist()) if not df.empty else []
    c_filter, c_manage = st.columns([2, 1])
    with c_filter:
        selected_tag = st.selectbox("🎯 Filter by Tag:", ["All"] + all_tags)
    
    # Filter DF by tag
    if selected_tag != "All" and not df.empty:
        df = df[df['tag'] == selected_tag]

    with c_manage:
        if st.button("🗑️ Clear This Tag", type="secondary", use_container_width=True):
            if selected_tag != "All":
                st.session_state.processed_data = [c for c in st.session_state.processed_data if c['tag'] != selected_tag]
                save_talent_data(st.session_state.processed_data)
                st.rerun()
            else:
                st.warning("Select a specific tag to clear.")

    # Status Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Talent Matches", len(df))
    c2.metric("Duplicates", len(df[df['is_duplicate'] == 'Yes']) if 'is_duplicate' in df.columns else 0)
    c3.metric("Avg Score", f"{df['resume_score'].mean():.1f}" if not df.empty else "0.0")
    
    st.markdown("### 🧬 Elite Talent Matrix")
    
    # Create display dataframe
    display_df = df.copy()
    if not display_df.empty:
        display_df.insert(0, "S.No", range(1, len(display_df) + 1))
        expected_cols = ["S.No", "full_name", "email", "phone", "one_liner", "working_role", "total_experience_years", "resume_score", "is_duplicate"]
        for col in expected_cols:
            if col not in display_df.columns: display_df[col] = "N/A"
        st.dataframe(display_df[expected_cols], use_container_width=True, hide_index=True)
    else:
        st.write("No candidates match the current filters.")
    
    # Selection logic for Action Hub
    st.session_state.selected_candidates = st.multiselect(
        "Select Candidates for Action Hub:", 
        options=df['full_name'].tolist() if not df.empty else [],
        default=[s for s in st.session_state.selected_candidates if s in (df['full_name'].tolist() if not df.empty else [])]
    )
    
    # Actions Row
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if not df.empty:
            if st.button("📥 Download This View (Excel)", use_container_width=True):
                file_path = generate_excel(df.to_dict('records'))
                with open(file_path, "rb") as f:
                    st.download_button("Excel Ready! Click to Download", f, file_name=f"HRIQ_{selected_tag}_Report.xlsx")
    
    st.markdown("---")
    
    # Deep Dive & Manage
    if not df.empty:
        c_sel, c_del = st.columns([3, 1])
        with c_sel:
            focus_cand = st.selectbox("🔍 Deep Dive & Manage:", options=df['full_name'].tolist())
        with c_del:
            if st.button("❌ Delete Candidate", type="primary", use_container_width=True):
                st.session_state.processed_data = [c for c in st.session_state.processed_data if c['full_name'] != focus_cand]
                save_talent_data(st.session_state.processed_data)
                st.rerun()

        c_data = next((c for c in st.session_state.processed_data if c['full_name'] == focus_cand), None)
        if c_data:
            st.markdown(f"### 👤 Candidate Deep Dive: {c_data['full_name']}")
            with st.container(border=True):
                render_candidate_profile_card(c_data)
    


    # Analytics
    if not df.empty:
        st.markdown("### 📊 Talent Distribution")
        col1, col2 = st.columns(2)
        with col1:
            if 'industry_domain' in df.columns:
                fig = px.pie(df, names='industry_domain', hole=0.7, title="Domain Ecosystem", color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if 'experience_category' in df.columns:
                fig = px.bar(df['experience_category'].value_counts().reset_index(), x='count', y='experience_category', orientation='h', title="Seniority Distribution", color_discrete_sequence=['#4F46E5'])
                st.plotly_chart(fig, use_container_width=True)
    
    # Master Export
    st.markdown("---")
    st.markdown("### 📘 Master Database Export")
    if st.button("Download Elite Master Report (Excel)", use_container_width=True, key="btn_master_export"):
        xl = generate_excel(st.session_state.processed_data)
        with open(xl, "rb") as f:
            st.download_button("Master Report Ready!", f, file_name="Talent_Master_List.xlsx", use_container_width=True, key="btn_master_dl")

def render_bulk_actions():
    st.markdown("<h2 style='font-weight: 700;'>Bulk Action Hub</h2>", unsafe_allow_html=True)
    
    if not st.session_state.selected_candidates:
        st.warning("No candidates selected. Go to **Talent Hub** to select profiles.")
        return

    st.info(f"Active Selection: {len(st.session_state.selected_candidates)} candidates")
    
    active_action_tab = render_custom_tabs(["📧 Bulk Outreach", "🎯 Global JD Matcher & Sourcing", "⚔️ Candidate Comparison", "📄 Data Export"], "bulk")
    
    selected_data = [c for c in st.session_state.processed_data if c['full_name'] in st.session_state.selected_candidates]

    if active_action_tab == "📧 Bulk Outreach":
        st.markdown("### 📧 AI Bulk Outreach")
        if st.button("Generate Emails for All Selected", key="btn_bulk_email"):
            with st.spinner("Drafting elite communications..."):
                for cand in selected_data:
                    email = generate_email(cand, "A top-tier role at our premium client")
                    st.markdown(f"**To: {cand['full_name']}**")
                    st.text_area(f"Email for {cand['full_name']}", value=email, height=200, key=f"email_outreach_{cand['full_name']}")
                    st.markdown("---")

    elif active_action_tab == "🎯 Global JD Matcher & Sourcing":
        st.markdown("### 🎯 Interactive JD Matcher & Boolean Sourcing")
        jd_input = st.text_area("Paste Job Description here:", placeholder="Paste the requirements...", key="bulk_jd_input")
        
        c_match_btn, c_source_btn = st.columns(2)
        
        with c_match_btn:
            run_match = st.button("Calculate Match Scores", use_container_width=True, key="btn_bulk_match")
        with c_source_btn:
            run_sourcing = st.button("Build Boolean Sourcing Blueprint", use_container_width=True, key="btn_bulk_source")
            
        if run_match and jd_input:
            with st.spinner("Analyzing fit..."):
                for i, cand in enumerate(st.session_state.processed_data):
                    if cand['full_name'] in st.session_state.selected_candidates:
                        match_res = match_candidate_to_jd(cand, jd_input)
                        st.session_state.processed_data[i]['match_score'] = match_res.get('match_score', 0)
                st.success("Match scores updated! Check the list below.")
                
                # Update selected_data list to see updated match_scores
                selected_data = [c for c in st.session_state.processed_data if c['full_name'] in st.session_state.selected_candidates]
                match_df = pd.DataFrame(selected_data)
                if 'match_score' in match_df.columns:
                    st.dataframe(match_df[['full_name', 'working_role', 'match_score']].sort_values(by='match_score', ascending=False), use_container_width=True)
        
        if run_sourcing and jd_input:
            with st.spinner("Generating Boolean strings..."):
                sourcing_blueprint = generate_boolean_sourcing(jd_input)
                st.session_state.sourcing_blueprint = sourcing_blueprint
                st.rerun()
                
        if 'sourcing_blueprint' in st.session_state and st.session_state.sourcing_blueprint:
            st.markdown("---")
            st.markdown("### ⚡ Sourcing Blueprint & Boolean Search Strings")
            st.markdown(st.session_state.sourcing_blueprint)

    elif active_action_tab == "⚔️ Candidate Comparison":
        st.markdown("### ⚔️ Side-by-Side Candidate Comparison")
        st.caption("Compare selected candidates on tech stack, experience level, pros/cons, and get a hiring verdict.")
        
        if st.button("⚔️ Generate Comparison Battlecard", use_container_width=True, key="btn_generate_battlecard"):
            with st.spinner("Evaluating candidates side-by-side..."):
                battlecard = generate_candidate_comparison(selected_data)
                st.session_state.battlecard = battlecard
                st.rerun()
                
        if 'battlecard' in st.session_state and st.session_state.battlecard:
            st.markdown("---")
            st.markdown(st.session_state.battlecard)

    elif active_action_tab == "📄 Data Export":
        st.markdown("### 📄 Elite Data Export")
        if st.button("Generate Master Excel for Selection", key="btn_export_selection"):
            xl = generate_excel(selected_data)
            with open(xl, "rb") as f:
                st.download_button("📘 Download Selection Report", f, file_name="Selected_Talent.xlsx", use_container_width=True, key="btn_dl_selection")

def render_parsing_tracker_v4():
    st.markdown("<h2 style='font-weight: 700;'>Parsing Tracker</h2>", unsafe_allow_html=True)
    st.markdown("### 📜 Real-time Parsing Log")
    if not st.session_state.parsing_history:
        st.info("No parsing activity recorded yet.")
    else:
        hist_df = pd.DataFrame(st.session_state.parsing_history)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

def render_status_v4():
    st.markdown("<h2 style='font-weight: 700;'>System Diagnostics</h2>", unsafe_allow_html=True)
    
    status = st.session_state.sys_status
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.write("### AI Server")
            st.write(status['server']['message'])
    with c2:
        with st.container(border=True):
            st.write("### AI Model")
            st.write(status['model']['message'])

def render_web_sourcing():
    st.markdown("<h2 style='font-weight: 700;'>🌐 Web Sourcing Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280;'>Find active candidates directly from the web using GitHub's live developer directory.</p>", unsafe_allow_html=True)
    
    # Initialize state variables for search results
    if "sourcing_results" not in st.session_state:
        st.session_state.sourcing_results = []
    if "outreach_drafts" not in st.session_state:
        st.session_state.outreach_drafts = {}
        
    active_source_tab = render_custom_tabs(["⚡ AI Semantic Sourcing", "🔍 Manual Sourcing"], "sourcing")
    
    if active_source_tab == "⚡ AI Semantic Sourcing":
        with st.container(border=True):
            st.markdown("### ⚡ Job Description AI Sourcer")
            jd_text = st.text_area("Paste target Job Description:", placeholder="Paste JD requirements to extract keywords...", key="sourcing_jd_input")
            limit = st.slider("Max candidates to retrieve:", min_value=5, max_value=30, value=10, key="sourcing_limit_ai")
            
            if st.button("🚀 Auto-Extract & Source", type="primary", use_container_width=True, key="btn_sourcing_ai"):
                if not jd_text:
                    st.warning("Please paste a Job Description first.")
                else:
                    with st.spinner("LLM extracting search parameters..."):
                        criteria = parse_sourcing_criteria(jd_text)
                        st.info(f"AI Extracted Criteria - Language: **{criteria.get('primary_language')}** | Keywords: **{', '.join(criteria.get('keywords', []))}** | Location: **{criteria.get('suggested_location')}**")
                        
                    with st.spinner("Searching live GitHub directory..."):
                        results = search_github_candidates(
                            language=criteria.get('primary_language', ''),
                            location=criteria.get('suggested_location', ''),
                            keywords=criteria.get('keywords', []),
                            per_page=limit
                        )
                        st.session_state.sourcing_results = results
                        st.session_state.outreach_drafts = {}
                        
                    if results:
                        st.success(f"Retrieved {len(results)} matches!")
                    else:
                        st.warning("No matches found. Try refining search criteria or searching manually.")
        
    elif active_source_tab == "🔍 Manual Sourcing":
        with st.container(border=True):
            st.markdown("### 🔍 Manual Directory Sourcing")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                language_input = st.selectbox("Primary Language:", ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#", "Ruby", "PHP", "HTML"], key="sourcing_lang")
            with col_s2:
                location_input = st.text_input("Target Location:", placeholder="e.g., 'San Francisco' or 'London'", key="sourcing_loc")
            with col_s3:
                keywords_input = st.text_input("Keywords (comma-separated):", placeholder="e.g. 'React, Docker'", key="sourcing_kws")
                
            limit_manual = st.slider("Max candidates to retrieve:", min_value=5, max_value=30, value=10, key="sourcing_limit_manual")
            
            if st.button("🔍 Source Candidates", type="primary", use_container_width=True, key="btn_sourcing_manual"):
                kw_list = [k.strip() for k in keywords_input.split(",") if k.strip()] if keywords_input else []
                with st.spinner("Searching live GitHub directory..."):
                    results = search_github_candidates(
                        language=language_input,
                        location=location_input,
                        keywords=kw_list,
                        per_page=limit_manual
                    )
                    st.session_state.sourcing_results = results
                    st.session_state.outreach_drafts = {}
                if results:
                    st.success(f"Retrieved {len(results)} matches!")
                else:
                    st.warning("No matches found. Try adjusting keywords or location.")
        
    # Render results
    if st.session_state.sourcing_results:
        st.markdown("### 👥 Candidate Profiles Found")
        for idx, cand in enumerate(st.session_state.sourcing_results):
            with st.container(border=True):
                col_c1, col_c2 = st.columns([1, 4])
                with col_c1:
                    if cand.get("avatar_url"):
                        st.image(cand["avatar_url"], width=100)
                    st.markdown(f"**Score Heuristics**<br>⭐ Repos: {cand['public_repos']}<br>👥 Followers: {cand['followers']}", unsafe_allow_html=True)
                with col_c2:
                    st.markdown(f"### [{cand['full_name']}]({cand['profile_url']}) (@{cand['username']})")
                    st.markdown(f"📍 **Location:** {cand['location']} | 🏢 **Company:** {cand['company']} | ✉️ **Email:** `{cand['email']}`")
                    st.markdown(f"📖 **Bio:** {cand['bio']}")
                    if cand.get("blog") and cand["blog"] != "N/A":
                        st.markdown(f"🌐 **Website/Blog:** [{cand['blog']}]({cand['blog'] if cand['blog'].startswith('http') else 'https://' + cand['blog']})")
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"✨ Draft Personalized Sourcing Pitch", key=f"btn_outreach_{cand['username']}_{idx}"):
                            with st.spinner("Drafting campaign message..."):
                                st.session_state.outreach_drafts[cand['username']] = draft_github_outreach(cand, jd_text=jd_text if 'jd_text' in locals() else None)
                                st.rerun()
                    with btn_col2:
                        already_imported = any(c.get('email') == cand['email'] and cand['email'] != "N/A" for c in st.session_state.processed_data)
                        if already_imported:
                            st.info("✅ Imported to Talent Hub")
                        else:
                            if st.button(f"📥 Import to Talent Hub", key=f"btn_import_{cand['username']}_{idx}"):
                                new_candidate = {
                                    "full_name": cand["full_name"],
                                    "email": cand["email"],
                                    "phone": "N/A",
                                    "working_role": f"{language_input if 'language_input' in locals() else 'Developer'} Specialist",
                                    "one_liner": cand["bio"][:100] if cand["bio"] else "Sourced GitHub profile",
                                    "technologies": [language_input] if 'language_input' in locals() else [],
                                    "total_experience_years": 0.0,
                                    "industry_domain": "IT & Software",
                                    "technical_evaluation": f"Sourced profile. Bio: {cand['bio']}. Repos: {cand['public_repos']}. Followers: {cand['followers']}.",
                                    "summary": cand["bio"],
                                    "elevator_pitch": f"GitHub developer sourced with {cand['followers']} followers and {cand['public_repos']} repositories.",
                                    "tag": "Sourced Candidates",
                                    "is_duplicate": "No",
                                    "resume_score": min(100, max(20, 20 + int(cand['followers']/10) + cand['public_repos'])),
                                    "source_file": cand["profile_url"],
                                    "raw_text": f"Sourced from GitHub profile {cand['profile_url']}. Bio: {cand['bio']}"
                                }
                                st.session_state.processed_data.append(new_candidate)
                                save_talent_data(st.session_state.processed_data)
                                st.session_state.data_changed = True
                                st.success(f"Successfully imported {cand['full_name']}!")
                                st.rerun()
                                
                if cand['username'] in st.session_state.outreach_drafts:
                    st.markdown("---")
                    st.markdown("**Personalized Outreach Pitch:**")
                    st.text_area("Copy and send:", value=st.session_state.outreach_drafts[cand['username']], height=150, key=f"pitch_text_{cand['username']}_{idx}")

if __name__ == "__main__":
    main()
