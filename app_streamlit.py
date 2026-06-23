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
    page_title="CareerPrep Agent Dashboard",
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
    
    /* Premium card layout (Theme Adaptive) */
    .premium-card {
        background-color: var(--secondary-background-color, #ffffff);
        color: var(--text-color, #1f2937);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .premium-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }
    
    /* Circular Gauge Widget */
    .gauge-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px;
    }
    
    .radial-gauge {
        position: relative;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    .gauge-inner-circle {
        position: absolute;
        width: 130px;
        height: 130px;
        background: var(--background-color, #ffffff);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .gauge-percentage {
        font-size: 36px;
        font-weight: 800;
        color: var(--text-color, #4f46e5);
        margin: 0;
    }
    
    .gauge-label {
        font-size: 11px;
        color: var(--text-color, #6b7280);
        opacity: 0.7;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Tags and Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        margin: 6px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 9999px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }
    
    .badge-matched {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    
    .badge-missing {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    
    /* Header design */
    .banner-title {
        font-size: 44px;
        font-weight: 800;
        background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .banner-subtitle {
        color: var(--text-color, #4b5563);
        opacity: 0.85;
        font-size: 16px;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    /* Kanban visual board styles */
    .kanban-col {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 12px;
        padding: 12px;
        min-height: 400px;
    }
    
    .kanban-card {
        background: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
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
        opacity: 0.8;
        margin-bottom: 8px;
    }
    
    .kanban-card-action {
        font-size: 11px;
        color: #3b82f6;
        background: rgba(59, 130, 246, 0.1);
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 8px;
        font-weight: 500;
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
        
        # Combine text to analyze
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


# --- MAIN GUI FLOW ---

st.write('<div class="banner-title">CareerPrep AI Copilot</div>', unsafe_allow_html=True)
st.write('<div class="banner-subtitle">An elegant, visual dashboard to match resumes, bridge skill gaps, generate cover letters, and manage job applications.</div>', unsafe_allow_html=True)

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

# Sidebar Settings
st.sidebar.markdown("<h2 style='text-align: center; margin-top: -15px;'>💼 CareerPrep</h2>", unsafe_allow_html=True)
st.sidebar.header("Navigation")
menu = st.sidebar.radio("Go to:", [
    "🔍 Skill Matcher Hub",
    "📄 Cover Letter & Study Plan",
    "💡 Interactive Interview Prep",
    "📋 Kanban Applications Board",
    "💼 Job Recommender"
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
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("📂 Load Default Sample Data"):
    st.session_state.job_text = get_sample_job()
    st.session_state.resume_text = get_sample_resume()
    st.session_state.kb_text = get_sample_kb()
    st.sidebar.success("Sample data loaded successfully!")
    st.rerun()

if st.sidebar.button("🧹 Clear Workspace"):
    st.session_state.job_text = ""
    st.session_state.resume_text = ""
    st.session_state.kb_text = ""
    st.session_state.chat_history = []
    st.sidebar.warning("All workspace content cleared!")
    st.rerun()

# --- TAB 1: SKILL MATCHER HUB ---
if menu == "🔍 Skill Matcher Hub":
    st.write("### Document Inputs")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 📄 Candidate Resume")
        resume_file = st.file_uploader("Upload Resume:", type=["txt", "pdf", "docx", "md"], key="res_uploader")
        if resume_file is not None:
            st.session_state.resume_text = load_file_content(resume_file)
        
        resume_text_area = st.text_area(
            "Review/Edit Resume Content:",
            value=st.session_state.resume_text,
            height=200,
            key="res_area"
        )
        st.session_state.resume_text = resume_text_area

    with col2:
        st.write("#### 📢 Job Poster Description")
        job_file = st.file_uploader("Upload Job Description:", type=["txt", "pdf", "docx", "md"], key="job_uploader")
        if job_file is not None:
            st.session_state.job_text = load_file_content(job_file)
        
        job_text_area = st.text_area(
            "Review/Edit Job Requirements:",
            value=st.session_state.job_text,
            height=200,
            key="job_area"
        )
        st.session_state.job_text = job_text_area

    st.markdown("---")
    
    if st.button("✨ Run Smart Analysis", type="primary", use_container_width=True):
        if not st.session_state.resume_text.strip() or not st.session_state.job_text.strip():
            st.error("Please provide both Resume and Job Description texts.")
        else:
            with st.spinner("Analyzing matching score..."):
                if ai_enabled and st.session_state.api_key:
                    # Run AI Semantic match
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
                        st.success("AI Semantic Analysis completed successfully!")
                        st.rerun()
                
                # Local Keyword Matcher Fallback
                job_skills = extract_keywords(st.session_state.job_text)
                resume_skills = extract_keywords(st.session_state.resume_text)
                matched, missing, score = compare_skills(job_skills, resume_skills)
                st.session_state.score = score
                st.session_state.matched = matched
                st.session_state.missing = missing
                st.session_state.recommendation = "Offline matching based on keyword overlap."
                st.session_state.resume_suggestions = [{"skill": skill, "bullet": f"Describe python-based application involving {skill}."} for skill in missing]
                st.session_state.study_plan_week_1 = [f"Study fundamentals of {skill}." for skill in missing[:4]]
                st.session_state.study_plan_week_2 = ["Work on coding templates.", "Publish source files to GitHub."]
                st.session_state.analyzed = True
                st.session_state.ai_used = False
                st.success("Local Keyword Analysis completed successfully!")
                st.rerun()

    # RENDER ANALYSIS SCREEN
    if st.session_state.get('analyzed', False):
        score = st.session_state.score
        matched = st.session_state.matched
        missing = st.session_state.missing
        recommendation = st.session_state.recommendation
        
        st.write('<div class="section-title">Analysis Dashboard</div>', unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns([1, 2])
        
        with col_g1:
            st.markdown("#### Match Score")
            # Draw beautiful Conic Gradient Progress Circle
            gauge_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
            st.markdown(f"""
            <div class="gauge-wrapper">
                <div class="radial-gauge" style="background: conic-gradient({gauge_color} {score}%, #e5e7eb 0);">
                    <div class="gauge-inner-circle">
                        <p class="gauge-percentage">{int(score)}%</p>
                        <p class="gauge-label">Match</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_g2:
            st.markdown("#### Recruiter Insights")
            if score >= 70:
                st.success(f"🌟 **Excellent Compatibility!**\n{recommendation}")
            elif score >= 40:
                st.warning(f"⚠️ **Moderate Compatibility.**\n{recommendation}")
            else:
                st.error(f"❌ **Low Compatibility.**\n{recommendation}")
                
            st.write(f"**Analysis Method**: {'🧠 Gemini AI Semantic Parser' if st.session_state.get('ai_used', False) else '🔌 Local Keyword Scraper'}")

        st.markdown("---")
        
        col_tags1, col_tags2 = st.columns(2)
        with col_tags1:
            st.write(f"🟢 **Matched Competencies ({len(matched)})**")
            if matched:
                badges = "".join([f'<span class="badge badge-matched">✓ {skill}</span>' for skill in matched])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.info("No matching skills identified.")
        with col_tags2:
            st.write(f"🔴 **Skill Gaps ({len(missing)})**")
            if missing:
                badges = "".join([f'<span class="badge badge-missing">✗ {skill}</span>' for skill in missing])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.success("Perfect alignment! No skill gaps found.")

# --- TAB 2: COVER LETTER & STUDY PLAN ---
elif menu == "📄 Cover Letter & Study Plan":
    st.write('<div class="section-title">Resume Suggestions & AI Cover Letter</div>', unsafe_allow_html=True)
    
    if not st.session_state.get('analyzed', False):
        st.info("Run the **Skill Matcher Hub** analysis first to unlock study roadmaps and tailored cover letters.")
    else:
        tab_bullets, tab_letter, tab_schedule = st.tabs(["💡 Tailored Bullets", "✍️ AI Cover Letter", "📅 Study Calendar"])
        
        with tab_bullets:
            st.write("#### Recommended Resume Changes")
            st.write("Incorporate these tailored statements to target missing requirements:")
            for item in st.session_state.resume_suggestions:
                st.markdown(f"**{item.get('skill', 'Requirement')}**:")
                st.info(f"💡 *{item.get('bullet')}*")
                
        with tab_letter:
            st.write("#### Generated Cover Letter")
            if not ai_enabled or not st.session_state.api_key:
                st.warning("Cover letter generator requires **Gemini AI Copilot** to be enabled in the sidebar.")
            else:
                if st.button("📝 Draft Cover Letter", type="primary"):
                    with st.spinner("Drafting cover letter..."):
                        letter = generate_cover_letter_with_ai(st.session_state.api_key, st.session_state.resume_text, st.session_state.job_text)
                        st.session_state.cover_letter = letter
                        
                if 'cover_letter' in st.session_state:
                    st.text_area("Tailored Cover Letter Content:", value=st.session_state.cover_letter, height=350)
                    st.download_button("Download Cover Letter (.txt)", st.session_state.cover_letter, file_name="cover_letter.txt")

        with tab_schedule:
            st.write("#### Weekly Study Roadmaps")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown("##### 📅 Week 1: Core Gaps")
                for task in st.session_state.study_plan_week_1:
                    st.markdown(f"- {task}")
            with col_s2:
                st.markdown("##### 📅 Week 2: Build & Practice")
                for task in st.session_state.study_plan_week_2:
                    st.markdown(f"- {task}")

# --- TAB 3: INTERVIEW PREP ---
elif menu == "💡 Interactive Interview Prep":
    st.write('<div class="section-title">Interview Q&A Guide & Mock Simulation</div>', unsafe_allow_html=True)
    
    st.subheader("Knowledge Base Study Notes")
    kb_file = st.file_uploader("Upload Notes File:", type=["txt"], key="kb_uploader")
    if kb_file is not None:
        st.session_state.kb_text = load_file_content(kb_file)
        
    kb_input = st.text_area("Or Paste study notes:", value=st.session_state.kb_text, height=120)
    st.session_state.kb_text = kb_input
    
    st.markdown("---")
    
    if not st.session_state.get('analyzed', False):
        st.info("Perform the matching analysis in **Skill Matcher Hub** first.")
    else:
        mode = st.radio("Choose Mode:", ["📚 Q&A Study Guide", "💬 AI Mock Interviewer"])
        
        if mode == "📚 Q&A Study Guide":
            st.write("### Interview Cheat-sheet")
            if ai_enabled and st.session_state.api_key:
                if st.button("Generate AI Questions", type="primary"):
                    with st.spinner("Analyzing requirements..."):
                        q_json = generate_questions_with_ai(st.session_state.api_key, st.session_state.job_text, st.session_state.kb_text)
                        if q_json:
                            st.session_state.questions_technical = q_json.get("technical", [])
                            st.session_state.questions_behavioral = q_json.get("behavioral", [])
                            st.session_state.questions_kb = q_json.get("notes_based", [])
                            st.session_state.questions_generated = True
                            st.rerun()
            
            # Render fallback/static question lists
            if not st.session_state.get('questions_generated', False):
                # Setup basic static lists
                st.session_state.questions_technical = [{"question": f"How have you used {s} in a project?", "tip": f"Describe a project utilizing {s}."} for s in st.session_state.matched[:5]]
                st.session_state.questions_behavioral = [
                    {"question": "Tell me about yourself.", "tip": "Summarize degree, core strengths, and top 2 projects."},
                    {"question": "Why are you interested in this role?", "tip": "Align your career interest with their job specifications."}
                ]
                st.session_state.questions_kb = [{"question": "Summarize key points from notes.", "tip": "Use star method."}]
            
            tech_c, hr_c, kb_c = st.tabs(["Technical", "HR / Behavioral", "Notes-Based"])
            with tech_c:
                for item in st.session_state.questions_technical:
                    with st.expander(item.get("question")):
                        st.info(f"💡 *Answer Tip:* {item.get('tip')}")
            with hr_c:
                for item in st.session_state.questions_behavioral:
                    with st.expander(item.get("question")):
                        st.info(f"💡 *Answer Tip:* {item.get('tip')}")
            with kb_c:
                if not st.session_state.kb_text.strip():
                    st.info("Paste Study Notes above to generate notes-based questions.")
                else:
                    for item in st.session_state.questions_kb:
                        with st.expander(item.get("question")):
                            st.info(f"💡 *Answer Tip:* {item.get('tip')}")

        elif mode == "💬 AI Mock Interviewer":
            st.write("### AI Chat Simulation")
            if not ai_enabled or not st.session_state.api_key:
                st.warning("Chat simulation requires **Gemini AI Copilot** to be enabled.")
            else:
                st.write("Interact with the AI Recruiter. It will ask questions and score your answers.")
                
                # Render Chat Log
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        
                user_msg = st.chat_input("Type your response here:")
                if user_msg:
                    # Append user message
                    st.session_state.chat_history.append({"role": "user", "content": user_msg})
                    with st.chat_message("user"):
                        st.markdown(user_msg)
                        
                    # Create AI context prompt
                    system_prompt = f"""
                    You are a friendly technical recruiter conducting a mock interview.
                    Here is the job description:
                    {st.session_state.job_text}
                    Here is the user's resume:
                    {st.session_state.resume_text}
                    
                    Conduct the interview. Ask one concise question at a time.
                    Evaluate the candidate's last answer, give brief feedback (with a score out of 10), and then ask the next question.
                    Keep responses under 100 words.
                    
                    Chat History:
                    {st.session_state.chat_history}
                    """
                    with st.spinner("AI is thinking..."):
                        reply = call_gemini(st.session_state.api_key, system_prompt)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        st.rerun()

# --- TAB 4: KANBAN APPLICATIONS BOARD ---
elif menu == "📋 Kanban Applications Board":
    st.write('<div class="section-title">Interactive Kanban Board</div>', unsafe_allow_html=True)
    
    df_apps = st.session_state.applications
    
    # Kanban Columns Setup
    stages = ["Not Applied", "Applied", "Interview Scheduled", "Offer Received", "Closed"]
    
    # Render Columns side by side
    cols = st.columns(len(stages))
    
    for idx, stage in enumerate(stages):
        with cols[idx]:
            # CSS colored header
            header_color = "#6b7280" if stage == "Closed" else "#10b981" if stage == "Offer Received" else "#ef4444" if stage == "Not Applied" else "#3b82f6"
            st.markdown(f"""
            <div style="background: {header_color}; padding: 8px; border-radius: 8px 8px 0 0; text-align: center;">
                <p style="color: white; margin: 0; font-weight: 700; font-size: 13px; text-transform: uppercase;">{stage}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Kanban Column Box
            st.markdown('<div class="kanban-col">', unsafe_allow_html=True)
            
            # Filter rows
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
                    
                    # Navigation arrow buttons
                    btn_prev, btn_next = st.columns(2)
                    with btn_prev:
                        if idx > 0:
                            if st.button(f"◀ Move", key=f"prev_{app_id}_{idx}", use_container_width=True):
                                # Update status
                                df_apps.loc[df_apps['application_id'] == app_id, 'status'] = stages[idx-1]
                                save_applications(df_apps)
                                st.session_state.applications = df_apps
                                st.rerun()
                    with btn_next:
                        if idx < len(stages) - 1:
                            if st.button(f"Move ▶", key=f"next_{app_id}_{idx}", use_container_width=True):
                                # Update status
                                df_apps.loc[df_apps['application_id'] == app_id, 'status'] = stages[idx+1]
                                save_applications(df_apps)
                                st.session_state.applications = df_apps
                                st.rerun()
                                
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("---")
    
    # Form to add new application
    st.subheader("➕ Create Application Card")
    with st.form("kanban_new_form", clear_on_submit=True):
        col_kf1, col_kf2 = st.columns(2)
        with col_kf1:
            company_k = st.text_input("Company Name")
            role_k = st.text_input("Job Role")
            source_k = st.text_input("Source (e.g. LinkedIn)")
            status_k = st.selectbox("Status", stages)
        with col_kf2:
            applied_k = st.date_input("Applied Date", value=None)
            interview_k = st.date_input("Interview Date", value=None)
            followup_k = st.date_input("Follow-up Date", value=None)
            action_k = st.text_input("Next Action Item")
        notes_k = st.text_area("Notes")
        
        submit_k = st.form_submit_button("Add Application Card")
        if submit_k:
            if not company_k or not role_k:
                st.error("Company Name and Job Role are required.")
            else:
                # Generate APP-ID
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
                    "company": company_k,
                    "role": role_k,
                    "source": source_k,
                    "status": status_k,
                    "applied_date": applied_k.strftime("%Y-%m-%d") if applied_k else "",
                    "interview_date": interview_k.strftime("%Y-%m-%d") if interview_k else "",
                    "follow_up_date": followup_k.strftime("%Y-%m-%d") if followup_k else "",
                    "next_action": action_k,
                    "notes": notes_k
                }
                
                df_apps = pd.concat([df_apps, pd.DataFrame([new_row])], ignore_index=True)
                if save_applications(df_apps):
                    st.session_state.applications = df_apps
                    st.success(f"Added application card {new_id} successfully!")
                    st.rerun()

    # Log editor & Export panel
    st.markdown("---")
    st.subheader("📥 Export Application Log")
    csv_data = df_apps.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download applications.csv",
        data=csv_data,
        file_name="applications.csv",
        mime="text/csv"
    )

# --- MENU: JOB RECOMMENDER ---
elif menu == "💼 Job Recommender":
    st.write('<div class="section-title">AI Job Search & Recommendations</div>', unsafe_allow_html=True)
    
    if not st.session_state.resume_text.strip():
        st.info("Please add/upload your Resume in the **🔍 Skill Matcher Hub** first so we can recommend matching jobs.")
    else:
        resume_skills = extract_keywords(st.session_state.resume_text)
        default_query = resume_skills[0] if resume_skills else "Python"
        
        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            search_query = st.text_input("Job Role / Tech Stack (e.g. Python, Django, React):", value=default_query)
        with col_q2:
            st.markdown("<br/>", unsafe_allow_html=True)
            search_btn = st.button("Search Jobs", type="primary", use_container_width=True)
            
        if 'last_query' not in st.session_state:
            st.session_state.last_query = ""
        if 'recommended_jobs' not in st.session_state:
            st.session_state.recommended_jobs = []
            
        if search_btn or (search_query and st.session_state.last_query != search_query):
            with st.spinner("Fetching matching jobs from Remotive API..."):
                raw_jobs = fetch_jobs_from_api(search_query)
                st.session_state.recommended_jobs = get_job_recommendations(
                    st.session_state.resume_text, raw_jobs
                )
                st.session_state.last_query = search_query
                st.success(f"Found {len(st.session_state.recommended_jobs)} job listings!")
                
        # Display recommendations
        if st.session_state.recommended_jobs:
            st.write(f"Showing results for **{st.session_state.last_query}** sorted by compatibility:")
            
            for index, job in enumerate(st.session_state.recommended_jobs):
                score = job["match_score"]
                score_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
                
                # Custom job card container
                st.markdown(f"""
                <div class="premium-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div>
                            <h3 style="margin: 0; font-size: 18px; color: var(--text-color, #1f2937);">{job['title']}</h3>
                            <p style="margin: 2px 0 0 0; font-size: 14px; font-weight: 600; color: #4f46e5;">{job['company_name']}</p>
                        </div>
                        <div style="background-color: {score_color}15; color: {score_color}; border: 1px solid {score_color}30; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 700;">
                            {int(score)}% Match
                        </div>
                    </div>
                    <div style="font-size: 13px; color: var(--text-color, #6b7280); margin-bottom: 12px; opacity: 0.85;">
                        📍 Location: <strong>{job['candidate_required_location']}</strong> &nbsp;&nbsp;|&nbsp;&nbsp; 💰 Salary: <strong>{job['salary']}</strong>
                    </div>
                """, unsafe_allow_html=True)
                
                # Display matched/missing tags
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    if job["matched_skills"]:
                        badges = "".join([f'<span class="badge badge-matched">✓ {s}</span>' for s in job["matched_skills"][:5]])
                        st.markdown(f"Matched: {badges}", unsafe_allow_html=True)
                with col_m2:
                    if job["missing_skills"]:
                        badges = "".join([f'<span class="badge badge-missing">✗ {s}</span>' for s in job["missing_skills"][:5]])
                        st.markdown(f"Missing: {badges}", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Buttons for actions
                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    st.link_button("🔗 Apply on Remotive", job["url"], use_container_width=True)
                with col_b2:
                    df_apps = st.session_state.applications
                    is_added = not df_apps[(df_apps['company'] == job['company_name']) & (df_apps['role'] == job['title'])].empty
                    
                    if is_added:
                        st.button("✅ Already Added", key=f"added_{job['id']}_{index}", disabled=True, use_container_width=True)
                    else:
                        add_btn = st.button("➕ Add to Kanban", key=f"add_{job['id']}_{index}", use_container_width=True)
                        if add_btn:
                            # Generate APP-ID
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
                                st.success(f"Added {job['title']} at {job['company_name']} to your Kanban Board!")
                                st.rerun()
                st.markdown("<br/>", unsafe_allow_html=True)
        else:
            st.info("Enter a role or skill query above and click 'Search Jobs' to fetch live remote job openings.")

