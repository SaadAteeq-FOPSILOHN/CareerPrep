import os
import csv
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, date
import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CareerPrep AI Copilot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- HELPER: LOAD LOCAL ENV KEY ---
def load_env_key():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1]
    return ""

# --- CSS FOR PREMIUM THEME-AWARE LOOK ---
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide Streamlit default menus, headers, and footers for privacy */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    /* Clean Premium Card Container */
    .premium-card {
        background-color: var(--secondary-background-color, #ffffff);
        color: var(--text-color, #1f2937);
        border: 1px solid rgba(128, 128, 128, 0.15);
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        transition: all 0.25s ease;
    }
    
    .premium-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
        border-color: rgba(79, 70, 229, 0.3);
    }
    
    /* Center Gauge Styles */
    .gauge-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 15px;
    }
    
    /* Custom Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        margin: 4px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .badge-matched {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }
    
    .badge-missing {
        background-color: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }
    
    /* Headers & Subtitles */
    .banner-title {
        font-size: 40px;
        font-weight: 800;
        background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
    }
    
    .banner-subtitle {
        color: var(--text-color, #4b5563);
        opacity: 0.8;
        font-size: 15px;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 15px;
        color: var(--text-color, #1f2937);
    }
    
    /* Kanban visual board styles */
    .kanban-col {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.12);
        border-radius: 12px;
        padding: 10px;
        min-height: 450px;
    }
    
    .kanban-card {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .kanban-card-title {
        font-weight: 700;
        font-size: 14px;
        color: var(--text-color, #1f2937);
        margin-bottom: 2px;
    }
    
    .kanban-card-sub {
        font-size: 12px;
        color: var(--text-color, #6b7280);
        opacity: 0.75;
        margin-bottom: 8px;
    }
    
    .kanban-card-action {
        font-size: 11px;
        color: #3b82f6;
        background: rgba(59, 130, 246, 0.08);
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS & DIRECTORIES ---
JOB_DIR = "input_jobs"
RESUME_DIR = "input_resumes"
KB_DIR = "input_kb"
TRACKER_DIR = "tracker"
TRACKER_PATH = os.path.join(TRACKER_DIR, "applications.csv")

KEYWORDS = [
    "python", "machine learning", "data preprocessing", "github", "git",
    "api", "prompt engineering", "sql", "communication", "problem solving",
    "oop", "database", "jupyter", "pandas", "numpy", "deep learning",
    "html", "css", "flask", "streamlit", "resume", "interview"
]

# Ensure tracking folders exist
os.makedirs(TRACKER_DIR, exist_ok=True)

# --- CONDITIONAL PDF IMPORT ---
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# --- FILE PARSERS ---
def extract_text_from_pdf(file):
    if not PYPDF_AVAILABLE:
        st.error("PDF text extraction is currently unavailable because the 'pypdf' package is not installed in this environment. Run `pip install pypdf` or `conda install -c conda-forge pypdf` and restart the application.")
        return ""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error parsing PDF file: {e}")
        return ""

def extract_text_from_docx(file):
    try:
        with zipfile.ZipFile(file) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            paragraphs = []
            for p_node in root.findall('.//w:p', namespaces):
                text_runs = []
                for t_node in p_node.findall('.//w:t', namespaces):
                    if t_node.text:
                        text_runs.append(t_node.text)
                if text_runs:
                    paragraphs.append("".join(text_runs))
            return "\n".join(paragraphs)
    except Exception as e:
        st.error(f"Error parsing DOCX file: {e}")
        return ""

def load_file_content(uploaded_file):
    if uploaded_file is None:
        return ""
    name_lower = uploaded_file.name.lower()
    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif name_lower.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")

def extract_keywords(text):
    text_lower = text.lower()
    found = []
    for keyword in KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)
    return found

def compare_skills(job_skills, resume_skills):
    matched = [skill for skill in job_skills if skill in resume_skills]
    missing = [skill for skill in job_skills if skill not in resume_skills]
    score = 0 if not job_skills else round((len(matched) / len(job_skills)) * 100, 2)
    return matched, missing, score

# --- APPLICATION TRACKER SYNC ---
def init_tracker_csv():
    if not os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "application_id", "company", "role", "source", "status",
                "applied_date", "interview_date", "follow_up_date", "next_action", "notes"
            ])
            writer.writerow([
                "APP-001", "ABC Tech Solutions", "Junior AI Engineer Intern", "LinkedIn",
                "Interview Scheduled", "2026-04-28", "2026-05-03", "2026-05-06",
                "Revise Python, ML basics, and prepare project explanations",
                "Resume tailored and submitted. Strong match on Python and GitHub."
            ])
            writer.writerow([
                "APP-002", "DataSoft Pakistan", "AI Research Intern", "Rozee.pk",
                "Applied", "2026-04-27", "", "2026-05-04",
                "Follow up if no response by May 4",
                "Applied with original resume. Follow up needed."
            ])
            writer.writerow([
                "APP-003", "TechVentures", "ML Intern", "WhatsApp Poster",
                "Not Applied", "", "", "",
                "Tailor resume for ML role and apply",
                "Job requires deep learning. Gap exists."
            ])

def load_applications():
    init_tracker_csv()
    try:
        df = pd.read_csv(TRACKER_PATH)
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"Error loading applications tracker: {e}")
        return pd.DataFrame()

def save_applications(df):
    try:
        df.to_csv(TRACKER_PATH, index=False, encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Error saving applications tracker: {e}")
        return False

# --- SAMPLE DATA LOADERS ---
def get_sample_job():
    path = os.path.join(JOB_DIR, "job_poster_01.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_sample_resume():
    path = os.path.join(RESUME_DIR, "my_resume.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_sample_kb():
    path = os.path.join(KB_DIR, "interview_notes.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# --- GEMINI AI CONNECTOR ---
def call_gemini(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: API returned status {response.status_code}\n{response.text}"
    except Exception as e:
        return f"Error connecting to Gemini API: {e}"

def clean_json_response(raw_text):
    text_clean = raw_text.strip()
    if text_clean.startswith("```json"):
        text_clean = text_clean[7:]
    if text_clean.endswith("```"):
        text_clean = text_clean[:-3]
    return text_clean.strip()

def analyze_skills_with_ai(api_key, resume_text, job_text):
    prompt = f"""
    You are an expert technical recruiter. Analyze the following Job Description and candidate Resume.
    Extract the list of required skills from the Job Description, determine which of those skills are matched in the candidate's Resume, and which are missing.
    Also, calculate a match score from 0 to 100 based on how well the candidate's skills cover the job's required skills.
    
    Job Description:
    {job_text}
    
    Candidate Resume:
    {resume_text}
    
    You MUST respond with a raw JSON object ONLY, matching this schema:
    {{
        "match_score": 75,
        "matched_skills": ["Python", "Git", "SQL"],
        "missing_skills": ["Machine Learning", "Streamlit"],
        "recommendation": "Short recommendation string...",
        "resume_suggestions": [
            {{"skill": "Machine Learning", "bullet": "Suggested resume bullet point showing ML experience..."}}
        ],
        "study_plan_week_1": ["Day 1-2 study task", "Day 3-4 study task"],
        "study_plan_week_2": ["Mini project using X", "Practice Y"]
    }}
    Do not include any markdown formatting like ```json or anything else. Just the raw JSON content.
    """
    res = call_gemini(api_key, prompt)
    try:
        cleaned = clean_json_response(res)
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"Error parsing AI analysis: {e}")
        return None

def generate_questions_with_ai(api_key, job_text, kb_text):
    prompt = f"""
    You are a technical interviewer. Based on the following Job Description and the candidate's Study Notes (Knowledge Base), generate a list of standard interview questions.
    Provide 5 technical questions based on the job requirements, 3 behavioral/HR questions, and 3 specific questions based on the concepts mentioned in their Study Notes.
    For each question, provide a brief tip or keywords for a good answer.
    
    Job Description:
    {job_text}
    
    Study Notes (Knowledge Base):
    {kb_text}
    
    Respond with a raw JSON object ONLY matching this schema:
    {{
        "technical": [
            {{"question": "Question text...", "tip": "Tip for answering..."}}
        ],
        "behavioral": [
            {{"question": "Question text...", "tip": "Tip for answering..."}}
        ],
        "notes_based": [
            {{"question": "Question text...", "tip": "Tip for answering..."}}
        ]
    }}
    Do not include markdown wrappers. Just raw JSON.
    """
    res = call_gemini(api_key, prompt)
    try:
        cleaned = clean_json_response(res)
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"Error parsing AI questions: {e}")
        return None

def generate_cover_letter_with_ai(api_key, resume_text, job_text):
    prompt = f"""
    Write a professional and compelling Cover Letter (around 300 words) from the candidate's perspective matching their resume to the job description.
    Make it feel personalized, highlighting their matching strengths and enthusiasm.
    
    Job Description:
    {job_text}
    
    Candidate Resume:
    {resume_text}
    
    Return the cover letter text directly. No extra remarks.
    """
    return call_gemini(api_key, prompt)

def fetch_jobs_from_api(query):
    url = f"https://remotive.com/api/remote-jobs?search={query}&limit=15"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get("jobs", [])
    except Exception as e:
        st.error(f"Error fetching jobs from Remotive: {e}")
    return []

def get_job_recommendations(resume_text, jobs):
    resume_skills = extract_keywords(resume_text)
    
    scored_jobs = []
    for job in jobs:
        title = job.get("title", "")
        tags = job.get("tags", [])
        desc = job.get("description", "")
        
        combined_job_text = f"{title} {' '.join(tags)} {desc}"
        job_skills = extract_keywords(combined_job_text)
        
        matched, missing, score = compare_skills(job_skills, resume_skills)
        
        scored_jobs.append({
            "id": job.get("id"),
            "title": title,
            "company_name": job.get("company_name"),
            "url": job.get("url"),
            "candidate_required_location": job.get("candidate_required_location", "Remote"),
            "salary": job.get("salary", "Not disclosed"),
            "tags": tags,
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing
        })
        
    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_jobs

def optimize_resume_with_ai(api_key, resume_text, job_text, user_info):
    prompt = f"""
    You are a professional resume writer. Optimize the candidate's resume to match the target job description.
    Naturally integrate the job's required skills into their professional summary, project descriptions, and experience bullet points.
    Do not fabricate degrees or fake credentials, but rewrite existing descriptions to make them sound highly compatible with the target job.
    
    Candidate Details:
    - Name: {user_info['name']}
    - Email: {user_info['email']}
    - Phone: {user_info['phone']}
    - LinkedIn: {user_info['linkedin']}
    
    Original Resume:
    {resume_text}
    
    Target Job Description:
    {job_text}
    
    Respond with a raw JSON object ONLY matching this schema:
    {{
        "name": "...",
        "contact": "...",
        "summary": "Professional summary paragraph...",
        "experience": [
            {{"title": "Job Title/Project Name", "details": "Description of work including optimized bullet points..."}}
        ],
        "skills": ["Skill 1", "Skill 2"]
    }}
    Do not wrap in markdown or add extra headers. Raw JSON only.
    """
    res = call_gemini(api_key, prompt)
    try:
        cleaned = clean_json_response(res)
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"Error parsing optimized resume: {e}")
        return None

def generate_html_resume(opt_res):
    html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{opt_res.get('name', 'Resume')}</title>
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: #333;
            margin: 40px;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #4f46e5;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .name {{
            font-size: 28px;
            font-weight: bold;
            margin: 0;
            color: #1e3a8a;
        }}
        .contact {{
            font-size: 13px;
            color: #555;
            margin-top: 5px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            text-transform: uppercase;
            color: #4f46e5;
            border-bottom: 1px solid #ddd;
            margin-top: 25px;
            margin-bottom: 10px;
            padding-bottom: 3px;
        }}
        .item {{
            margin-bottom: 15px;
        }}
        .item-title {{
            font-weight: bold;
            font-size: 14px;
        }}
        .skills-list {{
            font-weight: 500;
        }}
    </style>
    </head>
    <body>
        <div class="header">
            <div class="name">{opt_res.get('name', '')}</div>
            <div class="contact">{opt_res.get('contact', '')}</div>
        </div>
        
        <div class="section-title">Professional Summary</div>
        <p>{opt_res.get('summary', '')}</p>
        
        <div class="section-title">Experience & Projects</div>
    """
    for exp in opt_res.get('experience', []):
        html += f"""
        <div class="item">
            <div class="item-title">{exp.get('title', '')}</div>
            <p style="margin: 5px 0 0 0; white-space: pre-line;">{exp.get('details', '')}</p>
        </div>
        """
    
    skills_str = ", ".join(opt_res.get('skills', []))
    html += f"""
        <div class="section-title">Technical Skills</div>
        <p class="skills-list">{skills_str}</p>
    </body>
    </html>
    """
    return html

def generate_networking_message(api_key, company, role, target, msg_type, resume_text):
    prompt = f"""
    You are a professional career coach. Write a networking message on behalf of a candidate applying for the role of '{role}' at '{company}'.
    The target recipient is a '{target}', and the message type is '{msg_type}'.
    Use the candidate's skills and highlights from their resume to draft a compelling, highly personalized message.
    
    Candidate Resume:
    {resume_text}
    
    Important Constraints:
    - If the message type is 'LinkedIn Connection Request (<300 chars)', it MUST be strictly under 300 characters (including spaces).
    - Keep emails and other messages concise, professional, and clear.
    - Do not use placeholders (like [Name] or [Company]) if you can infer the company or role; otherwise use standard square brackets.
    
    Return the message text directly. No intro or outro text.
    """
    return call_gemini(api_key, prompt)

# --- MAIN GUI FLOW ---

st.write('<div class="banner-title">CareerPrep AI Copilot</div>', unsafe_allow_html=True)
st.write('<div class="banner-subtitle">The Handcrafted Professional Agent Suite for job seekers and candidates.</div>', unsafe_allow_html=True)

# Initialize Session State
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'job_text' not in st.session_state:
    st.session_state.job_text = ""
if 'kb_text' not in st.session_state:
    st.session_state.kb_text = ""
if 'applications' not in st.session_state:
    st.session_state.applications = load_applications()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = load_env_key()

# Sidebar Navigation (4 Clean Core Views)
st.sidebar.markdown("<h2 style='text-align: center; margin-top: -15px;'>💼 CareerPrep</h2>", unsafe_allow_html=True)
st.sidebar.header("Core Manager")
menu = st.sidebar.radio("Navigate to:", [
    "🔍 Skill Analysis & AI Builder",
    "💡 Interview Coach",
    "📋 Applications Manager",
    "💼 Search Jobs & Outreach"
])

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Settings")
ai_enabled = st.sidebar.checkbox("Enable Gemini AI Copilot", value=True)
if ai_enabled:
    api_key_input = st.sidebar.text_input("Gemini API Key:", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key_input
    if not api_key_input:
        st.sidebar.info("💡 Generate a free key from Google AI Studio and enter it above.")
    st.sidebar.markdown("""
    <div style="font-size: 11px; color: #858b9c; border-top: 1px solid rgba(128,128,128,0.2); padding-top: 8px; margin-top: 10px;">
        <strong>Why provide this key?</strong><br/>
        This API key connects the dashboard to the Gemini AI model to enable:
        <ul>
            <li>🧠 <strong>Semantic Skill Matching</strong> (intelligent resume-to-job analysis)</li>
            <li>✍️ <strong>AI Cover Letter Writer</strong> (personalized drafts)</li>
            <li>💬 <strong>AI Mock Interview Chat</strong> (simulated recruiter feedback)</li>
        </ul>
        <em>Your key is stored strictly in browser session memory and is never shared.</em>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.warning("Running in Offline Keyword Matcher Mode.")

st.sidebar.markdown("---")
st.sidebar.subheader("Workspace Controls")
if st.sidebar.button("📂 Load Sample Data"):
    st.session_state.job_text = get_sample_job()
    st.session_state.resume_text = get_sample_resume()
    st.session_state.kb_text = get_sample_kb()
    st.sidebar.success("Sample data loaded!")
    st.rerun()

if st.sidebar.button("🧹 Clear Workspace"):
    st.session_state.job_text = ""
    st.session_state.resume_text = ""
    st.session_state.kb_text = ""
    st.session_state.chat_history = []
    st.session_state.opt_resume = None
    st.sidebar.warning("Workspace cleared!")
    st.rerun()

# --- 1. CORE MENU: SKILL ANALYSIS & AI BUILDER ---
if menu == "🔍 Skill Analysis & AI Builder":
    sub_tab_match, sub_tab_optimizer, sub_tab_roadmap = st.tabs([
        "🔍 Matcher Hub", "✍️ AI Resume Builder", "📄 Cover Letter & Study Plan"
    ])
    
    # SUB-TAB 1: MATCHER HUB
    with sub_tab_match:
        st.write("### Document Inputs")
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.write("#### 📄 Candidate Resume")
            resume_file = st.file_uploader("Upload Resume:", type=["txt", "pdf", "docx", "md"], key="hub_res_uploader")
            if resume_file is not None:
                st.session_state.resume_text = load_file_content(resume_file)
            resume_text_area = st.text_area("Review/Edit Resume Content:", value=st.session_state.resume_text, height=200, key="hub_res_area")
            st.session_state.resume_text = resume_text_area
            
        with col_in2:
            st.write("#### 📢 Job Poster Description")
            job_file = st.file_uploader("Upload Job Description:", type=["txt", "pdf", "docx", "md"], key="hub_job_uploader")
            if job_file is not None:
                st.session_state.job_text = load_file_content(job_file)
            job_text_area = st.text_area("Review/Edit Job Requirements:", value=st.session_state.job_text, height=200, key="hub_job_area")
            st.session_state.job_text = job_text_area
            
        st.markdown("---")
        run_analysis = st.button("✨ Run Smart Analysis", type="primary", use_container_width=True)
        
        if run_analysis:
            if not st.session_state.resume_text.strip() or not st.session_state.job_text.strip():
                st.error("Please add/upload both your Resume and the Job Description first.")
            else:
                with st.spinner("Analyzing matching details..."):
                    if ai_enabled and st.session_state.api_key:
                        res_json = analyze_skills_with_ai(st.session_state.api_key, st.session_state.resume_text, st.session_state.job_text)
                        if res_json:
                            st.session_state.score = res_json.get("match_score", 0)
                            st.session_state.matched = res_json.get("matched_skills", [])
                            st.session_state.missing = res_json.get("missing_skills", [])
                            st.session_state.recommendation = res_json.get("recommendation", "")
                            st.session_state.resume_suggestions = res_json.get("resume_suggestions", [])
                            st.session_state.study_plan_week_1 = res_json.get("study_plan_week_1", [])
                            st.session_state.study_plan_week_2 = res_json.get("study_plan_week_2", [])
                            st.session_state.analyzed = True
                            st.session_state.ai_used = True
                            st.success("AI Analysis Complete!")
                            st.rerun()
                            
                    # Offline Fallback
                    job_skills = extract_keywords(st.session_state.job_text)
                    resume_skills = extract_keywords(st.session_state.resume_text)
                    matched, missing, score = compare_skills(job_skills, resume_skills)
                    st.session_state.score = score
                    st.session_state.matched = matched
                    st.session_state.missing = missing
                    st.session_state.recommendation = "Offline matching based on local keyword overlap."
                    st.session_state.resume_suggestions = [{"skill": s, "bullet": f"Incorporate python projects showing experience in {s}."} for s in missing]
                    st.session_state.study_plan_week_1 = [f"Practice and study {s} fundamentals." for s in missing[:4]]
                    st.session_state.study_plan_week_2 = ["Review clean coding standards.", "Push project code to GitHub."]
                    st.session_state.analyzed = True
                    st.session_state.ai_used = False
                    st.success("Local Analysis Complete!")
                    st.rerun()

        if st.session_state.get('analyzed', False):
            score = st.session_state.score
            matched = st.session_state.matched
            missing = st.session_state.missing
            recommendation = st.session_state.recommendation
            
            st.markdown('<div class="section-title">Analysis Dashboard</div>', unsafe_allow_html=True)
            col_d1, col_d2 = st.columns([1, 2])
            
            with col_d1:
                st.markdown("<h4 style='text-align: center; margin-bottom: 10px;'>Match Score</h4>", unsafe_allow_html=True)
                gauge_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
                
                # SVG Radial Progress Gauge (Perfect Browser & Contrast Rendering)
                st.markdown(f"""
                <div class="gauge-container">
                    <svg viewBox="0 0 36 36" style="width: 150px; height: 150px;">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(128,128,128,0.12)" stroke-width="2.5" />
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="{gauge_color}" stroke-dasharray="{score}, 100" stroke-width="3" stroke-linecap="round" />
                        <text x="18" y="20.5" font-family="'Outfit', sans-serif" font-weight="800" font-size="8" fill="var(--text-color, #1f2937)" text-anchor="middle">{int(score)}%</text>
                        <text x="18" y="26.5" font-family="'Outfit', sans-serif" font-weight="600" font-size="2.5" fill="#6b7280" text-anchor="middle">MATCH</text>
                    </svg>
                </div>
                """, unsafe_allow_html=True)
                
            with col_d2:
                st.markdown("#### Recruiter Feedback")
                if score >= 70:
                    st.success(f"🌟 **Strong Candidate!**\n{recommendation}")
                elif score >= 40:
                    st.warning(f"⚠️ **Moderate Match.**\n{recommendation}")
                else:
                    st.error(f"❌ **Weak Alignment.**\n{recommendation}")
                st.write(f"**Method**: {'🧠 Semantic AI Engine' if st.session_state.get('ai_used', False) else '🔌 Keyword Comparator'}")
                
            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(f"🟢 **Matched Skills ({len(matched)})**")
                if matched:
                    st.markdown("".join([f'<span class="badge badge-matched">✓ {s}</span>' for s in matched]), unsafe_allow_html=True)
                else:
                    st.info("No matching skills found.")
            with col_b2:
                st.write(f"🔴 **Missing Skills / Gaps ({len(missing)})**")
                if missing:
                    st.markdown("".join([f'<span class="badge badge-missing">✗ {s}</span>' for s in missing]), unsafe_allow_html=True)
                else:
                    st.success("You match all job criteria!")

    # SUB-TAB 2: AI RESUME OPTIMIZER
    with sub_tab_optimizer:
        st.write("### AI Resume Optimization Sandbox")
        if not st.session_state.resume_text.strip():
            st.info("Upload your resume in the Matcher Hub first.")
        else:
            col_opt1, col_opt2 = st.columns([1, 2])
            with col_opt1:
                st.write("#### Profile Settings")
                name_val = st.text_input("Name:", value="Saad Ateeq", key="opt_name_in")
                email_val = st.text_input("Email:", value="saadateeq8090@gmail.com", key="opt_email_in")
                phone_val = st.text_input("Phone:", value="+92 300 1234567", key="opt_phone_in")
                linkedin_val = st.text_input("LinkedIn Link:", value="linkedin.com/in/saadateeq", key="opt_li_in")
                
                st.markdown("---")
                target_reqs = st.text_area("Optimize for Job specifications:", value=st.session_state.job_text, height=120, key="opt_target_specs")
                
                run_opt = st.button("🧠 Build Optimized Resume", type="primary", use_container_width=True)
                
            with col_opt2:
                st.write("#### Resume Editor")
                if 'opt_resume' not in st.session_state:
                    st.session_state.opt_resume = None
                    
                if run_opt:
                    if not ai_enabled or not st.session_state.api_key:
                        st.error("AI Builder requires **Gemini AI Copilot** to be enabled.")
                    else:
                        with st.spinner("AI is rewriting resume bullets..."):
                            opt_data = optimize_resume_with_ai(
                                st.session_state.api_key, st.session_state.resume_text, target_reqs,
                                {"name": name_val, "email": email_val, "phone": phone_val, "linkedin": linkedin_val}
                            )
                            if opt_data:
                                st.session_state.opt_resume = opt_data
                                st.success("Optimization succeeded!")
                                
                if st.session_state.opt_resume:
                    opt = st.session_state.opt_resume
                    
                    e_name = st.text_input("Full Name:", value=opt.get("name", name_val), key="edit_name")
                    e_contact = st.text_input("Contact Header:", value=opt.get("contact", f"{email_val} | {phone_val}"), key="edit_contact")
                    e_summary = st.text_area("Professional Summary:", value=opt.get("summary", ""), height=100, key="edit_summary")
                    
                    st.write("##### Projects & Work Experience")
                    e_exp = []
                    for idx, exp in enumerate(opt.get("experience", [])):
                        t_title = st.text_input(f"Item {idx+1} Title:", value=exp.get("title", ""), key=f"edit_t_{idx}")
                        t_details = st.text_area(f"Item {idx+1} Experience:", value=exp.get("details", ""), key=f"edit_d_{idx}", height=120)
                        e_exp.append({"title": t_title, "details": t_details})
                        
                    e_skills_str = st.text_input("Technical Skills (comma-separated):", value=", ".join(opt.get("skills", [])), key="edit_skills")
                    e_skills = [s.strip() for s in e_skills_str.split(",") if s.strip()]
                    
                    # Update session state with modifications
                    st.session_state.opt_resume = {
                        "name": e_name,
                        "contact": e_contact,
                        "summary": e_summary,
                        "experience": e_exp,
                        "skills": e_skills
                    }
                    
                    st.markdown("---")
                    html_resume_data = generate_html_resume(st.session_state.opt_resume)
                    st.download_button(
                        label="⬇️ Download Premium Printable HTML Resume",
                        data=html_resume_data,
                        file_name="optimized_resume.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    st.info("💡 Tip: Open the downloaded file in your browser and print (Save as PDF) to get your tailored resume.")
                else:
                    st.info("Input contact details and click 'Build Optimized Resume' to generate a tailored copy.")

    # SUB-TAB 3: COVER LETTER & ROADMAP
    with sub_tab_roadmap:
        st.write("### AI Suggestions & Prep Strategy")
        if not st.session_state.get('analyzed', False):
            st.info("Analyze your resume in the Matcher Hub first.")
        else:
            col_road1, col_road2 = st.columns(2)
            with col_road1:
                st.write("#### 📝 Tailored Bullet Suggestion")
                for item in st.session_state.resume_suggestions:
                    st.markdown(f"**{item.get('skill', 'Requirement')}**:")
                    st.info(f"💡 *{item.get('bullet')}*")
                    
                st.markdown("---")
                st.write("#### ✍️ Cover Letter Drafter")
                if not ai_enabled or not st.session_state.api_key:
                    st.warning("Cover letter generator requires **Gemini AI Copilot**.")
                else:
                    if st.button("Generate Cover Letter Draft", type="primary", use_container_width=True):
                        with st.spinner("Writing cover letter..."):
                            letter = generate_cover_letter_with_ai(st.session_state.api_key, st.session_state.resume_text, st.session_state.job_text)
                            st.session_state.cover_letter = letter
                    if 'cover_letter' in st.session_state:
                        st.text_area("Outbox Cover Letter Draft:", value=st.session_state.cover_letter, height=200)
                        st.download_button("Download Cover Letter (.txt)", st.session_state.cover_letter, file_name="cover_letter.txt")
                        
            with col_road2:
                st.write("#### 📅 Study Schedule & Strategy")
                st.markdown("##### Week 1: Study missing requirements")
                for task in st.session_state.study_plan_week_1:
                    st.markdown(f"- {task}")
                    
                st.markdown("##### Week 2: Apply & Mock Practice")
                for task in st.session_state.study_plan_week_2:
                    st.markdown(f"- {task}")
                    
                st.markdown("---")
                st.write("##### Prep Checklist")
                st.checkbox("Generate study notes based interview questions", value=False, key="check_qa")
                st.checkbox("Practice behavioral stories in STAR format", value=False, key="check_star")
                st.checkbox("Submit customized resume and tailored cover letter", value=False, key="check_submit")

# --- 2. CORE MENU: INTERVIEW COACH ---
elif menu == "💡 Interview Coach":
    sub_tab_qa, sub_tab_chat = st.tabs(["📚 Study Cheat-sheet", "💬 Recruiter Chat Simulator"])
    
    # SUB-TAB 1: Q&A STUDY GUIDE
    with sub_tab_qa:
        st.write("### Custom Study Q&A Guide")
        if PYPDF_AVAILABLE:
            kb_file = st.file_uploader("Upload Study Notes (.txt, .pdf, .docx, .md):", type=["txt", "pdf", "docx", "md"], key="coach_kb_file")
        else:
            kb_file = st.file_uploader("Upload Study Notes (.txt, .docx, .md):", type=["txt", "docx", "md"], key="coach_kb_file")
            st.info("💡 To enable PDF notes parsing, install `pypdf` in your environment: `pip install pypdf`")
        if kb_file is not None:
            st.session_state.kb_text = load_file_content(kb_file)
        kb_text_area = st.text_area("Review/Edit Study Notes:", value=st.session_state.kb_text, height=120, key="coach_kb_area")
        st.session_state.kb_text = kb_text_area
        
        st.markdown("---")
        if not st.session_state.get('analyzed', False):
            st.info("Run the skill matcher analysis first to generate standard technical questions.")
        else:
            if ai_enabled and st.session_state.api_key:
                if st.button("Generate Smart AI Questions", type="primary", use_container_width=True):
                    with st.spinner("AI is generating custom interview questions..."):
                        q_data = generate_questions_with_ai(st.session_state.api_key, st.session_state.job_text, st.session_state.kb_text)
                        if q_data:
                            st.session_state.questions_technical = q_data.get("technical", [])
                            st.session_state.questions_behavioral = q_data.get("behavioral", [])
                            st.session_state.questions_kb = q_data.get("notes_based", [])
                            st.session_state.questions_generated = True
                            st.rerun()
            
            if not st.session_state.get('questions_generated', False):
                # Fallback static lists
                st.session_state.questions_technical = [{"question": f"Explain your experience and projects using {s}.", "tip": f"Describe a project utilizing {s}."} for s in st.session_state.matched[:5]]
                st.session_state.questions_behavioral = [
                    {"question": "Tell me about yourself.", "tip": "Mention name, university/degree, core skills, and best projects."},
                    {"question": "Why this role?", "tip": "Explain how your skills align with the job responsibilities."}
                ]
                st.session_state.questions_kb = [{"question": "Review notes and practice explaining concepts in detail.", "tip": "Explain concepts in your own words."}]
                
            q_tech_t, q_hr_t, q_kb_t = st.tabs(["💻 Technical", "👥 HR / Behavioral", "📚 Notes-Based"])
            with q_tech_t:
                for item in st.session_state.questions_technical:
                    with st.expander(item.get("question")):
                        st.info(f"💡 *Tip:* {item.get('tip')}")
            with q_hr_t:
                for item in st.session_state.questions_behavioral:
                    with st.expander(item.get("question")):
                        st.info(f"💡 *Tip:* {item.get('tip')}")
            with q_kb_t:
                if not st.session_state.kb_text.strip():
                    st.info("Upload study notes above to generate questions.")
                else:
                    for item in st.session_state.questions_kb:
                        with st.expander(item.get("question")):
                            st.info(f"💡 *Tip:* {item.get('tip')}")

    # SUB-TAB 2: CHAT MOCK INTERVIEWER
    with sub_tab_chat:
        st.write("### AI Interviewer Chat Simulator")
        if not ai_enabled or not st.session_state.api_key:
            st.warning("Chat simulator requires **Gemini AI Copilot** to be enabled in the sidebar.")
        elif not st.session_state.get('analyzed', False):
            st.info("Run the skill matcher analysis first so the AI knows which role you are preparing for.")
        else:
            st.write("Start conversation. The AI recruiter will ask technical and HR questions, grade your response, and ask the next question.")
            
            # Print chat history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            user_input = st.chat_input("Type your answer:")
            if user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)
                    
                # Call AI
                system_context = f"""
                You are a senior technical interviewer. Conduct a realistic mock interview.
                Target Job description:
                {st.session_state.job_text}
                Candidate Resume:
                {st.session_state.resume_text}
                
                Process:
                - Review the user's latest response.
                - Provide short feedback and a score out of 10 for their response.
                - Ask the next contextual interview question.
                - Ask one question at a time. Keep messages concise, friendly and under 100 words.
                
                Chat History:
                {st.session_state.chat_history}
                """
                with st.spinner("Recruiter is formulating next question..."):
                    reply = call_gemini(st.session_state.api_key, system_context)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.rerun()

# --- 3. CORE MENU: APPLICATIONS MANAGER ---
elif menu == "📋 Applications Manager":
    sub_tab_kanban, sub_tab_charts = st.tabs(["🗺️ Kanban Board", "📈 Tracker Analytics"])
    
    # SUB-TAB 1: KANBAN BOARD
    with sub_tab_kanban:
        st.write("### Kanban Board Board")
        df_apps = st.session_state.applications
        
        stages = ["Not Applied", "Applied", "Interview Scheduled", "Offer Received", "Closed"]
        cols = st.columns(len(stages))
        
        for idx, stage in enumerate(stages):
            with cols[idx]:
                header_color = "#6b7280" if stage == "Closed" else "#10b981" if stage == "Offer Received" else "#ef4444" if stage == "Not Applied" else "#3b82f6"
                st.markdown(f"""
                <div style="background: {header_color}; padding: 8px; border-radius: 8px 8px 0 0; text-align: center;">
                    <p style="color: white; margin: 0; font-weight: 700; font-size: 13px; text-transform: uppercase;">{stage}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="kanban-col">', unsafe_allow_html=True)
                stage_apps = df_apps[df_apps['status'] == stage]
                
                if len(stage_apps) == 0:
                    st.markdown("<p style='font-size:12px; color:#9ca3af; text-align:center; padding-top:20px;'>Empty</p>", unsafe_allow_html=True)
                else:
                    for _, row in stage_apps.iterrows():
                        app_id = row['application_id']
                        company = row['company']
                        role = row['role']
                        next_act = row.get('next_action', '')
                        
                        st.markdown(f"""
                        <div class="kanban-card">
                            <div class="kanban-card-title">{role}</div>
                            <div class="kanban-card-sub">{company}</div>
                            {f'<div class="kanban-card-action">Action: {next_act}</div>' if next_act else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Arrows
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if idx > 0:
                                if st.button(f"◀", key=f"prev_{app_id}_{idx}", use_container_width=True):
                                    df_apps.loc[df_apps['application_id'] == app_id, 'status'] = stages[idx-1]
                                    save_applications(df_apps)
                                    st.session_state.applications = df_apps
                                    st.rerun()
                        with btn_c2:
                            if idx < len(stages) - 1:
                                if st.button(f"▶", key=f"next_{app_id}_{idx}", use_container_width=True):
                                    df_apps.loc[df_apps['application_id'] == app_id, 'status'] = stages[idx+1]
                                    save_applications(df_apps)
                                    st.session_state.applications = df_apps
                                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
        st.markdown("---")
        st.subheader("➕ Create Application Card")
        with st.form("board_new_form", clear_on_submit=True):
            col_bf1, col_bf2 = st.columns(2)
            with col_bf1:
                company_b = st.text_input("Company Name")
                role_b = st.text_input("Job Role")
                source_b = st.text_input("Source (e.g. LinkedIn)")
                status_b = st.selectbox("Status", stages)
            with col_bf2:
                applied_b = st.date_input("Applied Date", value=None)
                interview_b = st.date_input("Interview Date", value=None)
                followup_b = st.date_input("Follow-up Date", value=None)
                action_b = st.text_input("Next Action Item")
            notes_b = st.text_area("Notes")
            
            submit_b = st.form_submit_button("Add Application Card")
            if submit_b:
                if not company_b or not role_b:
                    st.error("Company Name and Job Role are required.")
                else:
                    if len(df_apps) > 0:
                        try:
                            last_id = max(df_apps['application_id'].apply(lambda x: int(x.split('-')[1]) if '-' in str(x) else 0))
                            new_id = f"APP-{str(last_id + 1).zfill(3)}"
                        except:
                            new_id = f"APP-{str(len(df_apps) + 1).zfill(3)}"
                    else:
                        new_id = "APP-001"
                        
                    new_row = {
                        "application_id": new_id,
                        "company": company_b,
                        "role": role_b,
                        "source": source_b,
                        "status": status_b,
                        "applied_date": applied_b.strftime("%Y-%m-%d") if applied_b else "",
                        "interview_date": interview_b.strftime("%Y-%m-%d") if interview_b else "",
                        "follow_up_date": followup_b.strftime("%Y-%m-%d") if followup_k else "",
                        "next_action": action_b,
                        "notes": notes_b
                    }
                    
                    df_apps = pd.concat([df_apps, pd.DataFrame([new_row])], ignore_index=True)
                    if save_applications(df_apps):
                        st.session_state.applications = df_apps
                        st.success(f"Added application card {new_id} successfully!")
                        st.rerun()
                        
        st.markdown("---")
        st.subheader("📥 Export Application Log")
        csv_data = df_apps.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download applications.csv",
            data=csv_data,
            file_name="applications.csv",
            mime="text/csv"
        )

    # SUB-TAB 2: TRACKER ANALYTICS
    with sub_tab_charts:
        st.write("### Application Funnel & Velocity Analytics")
        df_apps = st.session_state.applications
        
        if len(df_apps) == 0:
            st.info("No applications to analyze.")
        else:
            total_apps = len(df_apps)
            df_apps['status_clean'] = df_apps['status'].str.lower().str.strip()
            
            interviews = len(df_apps[df_apps['status_clean'] == 'interview scheduled'])
            offers = len(df_apps[df_apps['status_clean'] == 'offer received'])
            
            interview_rate = 0 if total_apps == 0 else round((interviews / total_apps) * 100, 1)
            offer_rate = 0 if total_apps == 0 else round((offers / total_apps) * 100, 1)
            
            col_an1, col_an2, col_an3, col_an4 = st.columns(4)
            with col_an1:
                st.metric("Total Logged", total_apps)
            with col_an2:
                st.metric("Interviews Scheduled", interviews)
            with col_an3:
                st.metric("Offers Received", offers)
            with col_an4:
                st.metric("Offer Conversion Rate", f"{offer_rate}%")
                
            st.markdown("---")
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.write("#### 📊 Funnel Breakdown (Status)")
                status_counts = df_apps['status'].value_counts()
                st.bar_chart(status_counts)
            with col_ch2:
                st.write("#### 🎯 Distribution by Source")
                source_counts = df_apps['source'].value_counts()
                if len(source_counts) > 0:
                    st.bar_chart(source_counts)
                else:
                    st.info("No sources logged.")
                    
            st.markdown("---")
            st.write("#### 📈 Weekly Application Velocity")
            df_dates = df_apps[df_apps['applied_date'].str.strip() != ''].copy()
            if len(df_dates) > 0:
                try:
                    df_dates['applied_date'] = pd.to_datetime(df_dates['applied_date'])
                    df_dates = df_dates.sort_values('applied_date')
                    timeline = df_dates.groupby(df_dates['applied_date'].dt.to_period('W')).size().reset_index(name='count')
                    timeline['applied_date'] = timeline['applied_date'].dt.to_timestamp()
                    timeline = timeline.set_index('applied_date')
                    st.line_chart(timeline)
                except Exception as e:
                    st.write("Fill dates in tracker cards to view weekly timelines.")
            else:
                st.info("Add applied dates in your tracking cards to visualize submission timelines.")

# --- 4. CORE MENU: SEARCH JOBS & OUTREACH ---
elif menu == "💼 Search Jobs & Outreach":
    sub_tab_search, sub_tab_networking = st.tabs(["🔍 Live Job Search", "✉️ AI Networking Hub"])
    
    # SUB-TAB 1: LIVE JOB SEARCH
    with sub_tab_search:
        st.write("### Fetch Live Remote Openings")
        if not st.session_state.resume_text.strip():
            st.info("Please add your Resume in the Skill Matcher Hub first.")
        else:
            resume_skills = extract_keywords(st.session_state.resume_text)
            default_query = resume_skills[0] if resume_skills else "Python"
            
            col_sq1, col_sq2 = st.columns([3, 1])
            with col_sq1:
                search_query = st.text_input("Target Tech/Keywords:", value=default_query, key="live_search_query")
            with col_sq2:
                st.markdown("<br/>", unsafe_allow_html=True)
                search_btn = st.button("Search Jobs", type="primary", use_container_width=True, key="live_search_btn")
                
            if 'last_query' not in st.session_state:
                st.session_state.last_query = ""
            if 'recommended_jobs' not in st.session_state:
                st.session_state.recommended_jobs = []
                
            if search_btn or (search_query and st.session_state.last_query != search_query):
                with st.spinner("Scanning Remotive job board..."):
                    raw_jobs = fetch_jobs_from_api(search_query)
                    st.session_state.recommended_jobs = get_job_recommendations(
                        st.session_state.resume_text, raw_jobs
                    )
                    st.session_state.last_query = search_query
                    st.success(f"Fetched {len(st.session_state.recommended_jobs)} job listings!")
                    
            if st.session_state.recommended_jobs:
                st.write(f"Showing results for **{st.session_state.last_query}** sorted by Match Score:")
                
                for index, job in enumerate(st.session_state.recommended_jobs):
                    score = job["match_score"]
                    score_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
                    
                    st.markdown(f"""
                    <div class="premium-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div>
                                <h3 style="margin: 0; font-size: 17px; color: var(--text-color, #1f2937);">{job['title']}</h3>
                                <p style="margin: 2px 0 0 0; font-size: 14px; font-weight: 600; color: #4f46e5;">{job['company_name']}</p>
                            </div>
                            <div style="background-color: {score_color}12; color: {score_color}; border: 1px solid {score_color}25; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700;">
                                {int(score)}% Match
                            </div>
                        </div>
                        <div style="font-size: 12px; color: var(--text-color, #6b7280); margin-bottom: 12px; opacity: 0.85;">
                            📍 {job['candidate_required_location']} &nbsp;&nbsp;|&nbsp;&nbsp; 💰 {job['salary']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if job["matched_skills"]:
                            st.markdown("Matched: " + "".join([f'<span class="badge badge-matched">{s}</span>' for s in job["matched_skills"][:4]]), unsafe_allow_html=True)
                    with col_b2:
                        if job["missing_skills"]:
                            st.markdown("Missing: " + "".join([f'<span class="badge badge-missing">{s}</span>' for s in job["missing_skills"][:4]]), unsafe_allow_html=True)
                            
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        st.link_button("🔗 Apply on Remotive", job["url"], use_container_width=True, key=f"apply_{job['id']}_{index}")
                    with col_act2:
                        df_apps = st.session_state.applications
                        is_added = not df_apps[(df_apps['company'] == job['company_name']) & (df_apps['role'] == job['title'])].empty
                        
                        if is_added:
                            st.button("✅ Already Added", key=f"added_{job['id']}_{index}", disabled=True, use_container_width=True)
                        else:
                            add_btn = st.button("➕ Add to Kanban", key=f"add_{job['id']}_{index}", use_container_width=True)
                            if add_btn:
                                if len(df_apps) > 0:
                                    try:
                                        last_id = max(df_apps['application_id'].apply(lambda x: int(x.split('-')[1]) if '-' in str(x) else 0))
                                        new_id = f"APP-{str(last_id + 1).zfill(3)}"
                                    except:
                                        new_id = f"APP-{str(len(df_apps) + 1).zfill(3)}"
                                else:
                                    new_id = "APP-001"
                                    
                                new_row = {
                                    "application_id": new_id,
                                    "company": job['company_name'],
                                    "role": job['title'],
                                    "source": "Remotive Remote Jobs",
                                    "status": "Not Applied",
                                    "applied_date": "",
                                    "interview_date": "",
                                    "follow_up_date": "",
                                    "next_action": "Apply through Remotive link",
                                    "notes": f"Salary: {job['salary']}. Match Score: {int(score)}%. URL: {job['url']}"
                                }
                                
                                updated_df = pd.concat([df_apps, pd.DataFrame([new_row])], ignore_index=True)
                                if save_applications(updated_df):
                                    st.session_state.applications = updated_df
                                    st.success(f"Added {job['title']} card to Kanban!")
                                    st.rerun()
                    st.markdown("<br/>", unsafe_allow_html=True)
            else:
                st.info("Enter keywords and click 'Search Jobs' to query listings.")

    # SUB-TAB 2: AI NETWORKING HUB
    with sub_tab_networking:
        st.write("### AI Networking & Outreach Copywriter")
        if not st.session_state.resume_text.strip():
            st.info("Please upload your resume in the Skill Matcher Hub first.")
        else:
            df_apps = st.session_state.applications
            col_nt1, col_nt2 = st.columns([1, 2])
            
            with col_nt1:
                st.write("#### Select Target Profile")
                if len(df_apps) == 0:
                    t_company = st.text_input("Company Name:")
                    t_role = st.text_input("Job Role Name:")
                else:
                    options = [f"{row['role']} at {row['company']}" for _, row in df_apps.iterrows()]
                    selected_idx = st.selectbox("Select job application:", range(len(options)), format_func=lambda x: options[x])
                    t_company = df_apps.iloc[selected_idx]['company']
                    t_role = df_apps.iloc[selected_idx]['role']
                    
                st.markdown("---")
                st.write("#### Outreach Config")
                recipient = st.selectbox("Recipient Type:", ["Recruiter / HR Representative", "Hiring Manager", "Team Lead / Engineer", "Alumni / Professional Peer"])
                m_type = st.selectbox("Message Type:", [
                    "LinkedIn Connection Request (<300 chars)",
                    "Cold Outreach Email / Cover Message",
                    "Ghosted Application Follow-up",
                    "Post-Interview Thank You Note"
                ])
                
                draft_btn = st.button("✉️ Draft Outreach Message", type="primary", use_container_width=True, key="net_draft_btn")
                
            with col_nt2:
                st.write("#### Message Draft Preview")
                if 'networking_draft' not in st.session_state:
                    st.session_state.networking_draft = ""
                    
                if draft_btn:
                    if not ai_enabled or not st.session_state.api_key:
                        st.error("Outreach drafts require **Gemini AI Copilot** to be enabled.")
                    else:
                        with st.spinner("AI is crafting networking message..."):
                            message_draft = generate_networking_message(
                                st.session_state.api_key, t_company, t_role, recipient, m_type, st.session_state.resume_text
                            )
                            st.session_state.networking_draft = message_draft
                            st.success("Draft Generated!")
                            
                if st.session_state.networking_draft:
                    st.text_area("Review Outreach draft:", value=st.session_state.networking_draft, height=250, key="net_draft_area")
                    st.download_button("Download Message Draft (.txt)", st.session_state.networking_draft, file_name="outreach_message.txt", key="net_download_btn")
                else:
                    st.info("Configure variables and click 'Draft Outreach Message' to generate outreach copies.")
