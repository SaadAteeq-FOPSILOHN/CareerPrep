import os
import csv
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, date
import pandas as pd
import streamlit as st

# --- CONDITIONAL PDF IMPORT ---
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CareerPrep Agent Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS FOR PREMIUM LOOK ---
st.markdown("""
<style>
    /* Custom CSS to style elements */
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .skill-tag {
        display: inline-block;
        padding: 5px 12px;
        margin: 4px;
        font-size: 14px;
        font-weight: 500;
        border-radius: 20px;
        color: white;
    }
    .skill-matched {
        background-color: #2e7d32; /* Green */
        border: 1px solid #1b5e20;
    }
    .skill-missing {
        background-color: #c62828; /* Red */
        border: 1px solid #b71c1c;
    }
    .main-title {
        font-size: 40px;
        font-weight: 800;
        background: linear-gradient(90deg, #1f77b4, #aec7e8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 5px;
    }
    .app-status {
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
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

# --- HELPER FUNCTIONS ---
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
        # Clean empty dates/columns
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

# --- MAIN STREAMLIT APPLICATION FLOW ---

st.write('<div class="main-title">CareerPrep Job-Hunting Agent</div>', unsafe_allow_html=True)
st.write("An interactive AI-powered dashboard to analyze your resume match, bridge skill gaps, generate interview prep materials, and track job applications.")

# Initialize session state for analysis details and applications
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'job_text' not in st.session_state:
    st.session_state.job_text = ""
if 'kb_text' not in st.session_state:
    st.session_state.kb_text = ""
if 'applications' not in st.session_state:
    st.session_state.applications = load_applications()

# Sidebar Setup
st.sidebar.image("https://img.icons8.com/clouds/100/000000/find-matching-job.png", width=80)
st.sidebar.header("Navigation")
menu = st.sidebar.radio("Go to:", [
    "🔍 Resume Skill Matcher",
    "📝 Tailored Suggestion & Study Plan",
    "💡 Interactive Interview Prep",
    "📊 Application Status Tracker"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Actions")
if st.sidebar.button("📂 Load Sample/Default Files"):
    st.session_state.job_text = get_sample_job()
    st.session_state.resume_text = get_sample_resume()
    st.session_state.kb_text = get_sample_kb()
    st.sidebar.success("Sample files loaded successfully!")

if st.sidebar.button("🧹 Clear Input Areas"):
    st.session_state.job_text = ""
    st.session_state.resume_text = ""
    st.session_state.kb_text = ""
    st.sidebar.warning("All input fields cleared!")

# --- MENU: RESUME SKILL MATCHER ---
if menu == "🔍 Resume Skill Matcher":
    st.markdown('<div class="section-title">Resume & Job Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Add Resume")
        if PYPDF_AVAILABLE:
            resume_file = st.file_uploader("Upload Resume (.txt, .pdf, .docx, .md)", type=["txt", "pdf", "docx", "md"])
        else:
            resume_file = st.file_uploader("Upload Resume (.txt, .docx, .md)", type=["txt", "docx", "md"])
            st.info("💡 To enable PDF resume parsing, install `pypdf` in your environment: `pip install pypdf`")
        if resume_file is not None:
            st.session_state.resume_text = load_file_content(resume_file)
        
        resume_text_area = st.text_area(
            "Or Paste Resume Text Here:",
            value=st.session_state.resume_text,
            height=250,
            key="resume_text_area"
        )
        st.session_state.resume_text = resume_text_area

    with col2:
        st.subheader("2. Add Job Poster")
        if PYPDF_AVAILABLE:
            job_file = st.file_uploader("Upload Job poster (.txt, .pdf, .docx, .md)", type=["txt", "pdf", "docx", "md"])
        else:
            job_file = st.file_uploader("Upload Job poster (.txt, .docx, .md)", type=["txt", "docx", "md"])
            st.info("💡 To enable PDF job description parsing, install `pypdf` in your environment.")
        if job_file is not None:
            st.session_state.job_text = load_file_content(job_file)
        
        job_text_area = st.text_area(
            "Or Paste Job Poster Text Here:",
            value=st.session_state.job_text,
            height=250,
            key="job_text_area"
        )
        st.session_state.job_text = job_text_area

    st.markdown("---")
    
    if st.button("📊 Run Matching Analysis", type="primary"):
        if not st.session_state.resume_text.strip() or not st.session_state.job_text.strip():
            st.error("Please add/upload both your Resume and the Job Description before running the matching analysis.")
        else:
            # Extract skills
            job_skills = extract_keywords(st.session_state.job_text)
            resume_skills = extract_keywords(st.session_state.resume_text)
            matched, missing, score = compare_skills(job_skills, resume_skills)

            # Store in session state for other pages
            st.session_state.job_skills = job_skills
            st.session_state.resume_skills = resume_skills
            st.session_state.matched = matched
            st.session_state.missing = missing
            st.session_state.score = score
            st.session_state.analyzed = True
            
            st.success("Analysis Complete!")

    # Display Analysis Results
    if st.session_state.get('analyzed', False):
        score = st.session_state.score
        matched = st.session_state.matched
        missing = st.session_state.missing
        job_skills = st.session_state.job_skills
        
        st.markdown('<div class="section-title">Analysis Results</div>', unsafe_allow_html=True)
        
        # Display Score Card
        score_col, recommendation_col = st.columns([1, 2])
        with score_col:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Match Score</h3>
                <h1 style="color: {'#2e7d32' if score >= 70 else '#f57c00' if score >= 40 else '#c62828'}; font-size: 54px;">{score}%</h1>
            </div>
            """, unsafe_allow_html=True)
            
        with recommendation_col:
            st.subheader("Recommendation")
            if score >= 70:
                st.success("🌟 **Strong Match!** You have most of the skills required for this job. Apply with confidence.")
            elif score >= 40:
                st.warning("⚠️ **Moderate Match.** You have a solid base, but there are important missing skills. We recommend updating your resume or studying the missing areas first.")
            else:
                st.error("❌ **Weak Match.** There are significant skill gaps. Consider targeting a different role or taking time to develop the required skills.")
                
            st.write(f"**Skills required by job poster**: {len(job_skills)}")
            st.write(f"**Matched skills**: {len(matched)}")
            st.write(f"**Missing skills**: {len(missing)}")

        # Display skills side by side
        col_matched, col_missing = st.columns(2)
        with col_matched:
            st.subheader(f"Matched Skills ({len(matched)})")
            if matched:
                matched_html = "".join([f'<span class="skill-tag skill-matched">✓ {skill}</span>' for skill in matched])
                st.markdown(matched_html, unsafe_allow_html=True)
            else:
                st.info("No matching skills found in the resume.")
                
        with col_missing:
            st.subheader(f"Missing Skills ({len(missing)})")
            if missing:
                missing_html = "".join([f'<span class="skill-tag skill-missing">✗ {skill}</span>' for skill in missing])
                st.markdown(missing_html, unsafe_allow_html=True)
            else:
                st.success("Excellent! You match all extracted skills.")

# --- MENU: SUGGESTIONS & PREPARATION PLAN ---
elif menu == "📝 Tailored Suggestion & Study Plan":
    st.markdown('<div class="section-title">Resume Customization & Prep Plan</div>', unsafe_allow_html=True)
    
    if not st.session_state.get('analyzed', False):
        st.info("Please perform a matching analysis in the **🔍 Resume Skill Matcher** tab to generate suggestions and plans.")
    else:
        job_skills = st.session_state.job_skills
        missing = st.session_state.missing
        score = st.session_state.score
        
        tab_resume, tab_study = st.tabs(["📄 Resume Bullet Suggestions", "📅 Study & Prep Planner"])
        
        with tab_resume:
            st.subheader("Tailored Resume Suggestions")
            st.write("We recommend modifying your resume to highlight experience or knowledge in the required skills. Here are suggested bullet points you can customize and add:")
            
            suggestions = [
                ("Python", "Built Python-based ML project with data preprocessing and model evaluation."),
                ("GitHub/Git", "Used GitHub for version control with proper commit history and detailed README documentation."),
                ("API", "Developed a REST API integration project using Python requests library."),
                ("Prompt Engineering", "Applied prompt engineering to build a Streamlit AI demo application."),
                ("SQL/Database", "Queried and managed databases using SQL with complex JOIN operations.")
            ]
            
            for skill, suggestion in suggestions:
                # Highlight if skill is required
                is_req = any(s in skill.lower() for s in job_skills)
                is_missing = any(s in skill.lower() for s in missing)
                
                status_bullet = ""
                if is_req:
                    status_bullet = "⚠️ (Missing)" if is_missing else "✅ (Matched)"
                    
                st.markdown(f"**{skill}** {status_bullet}:")
                st.info(suggestion)
                
            if missing:
                st.markdown("### 🛠️ Skills to Develop before applying/interviewing:")
                for skill in missing:
                    st.markdown(f"- **{skill.title()}**: Practice concepts, build a mini-project, or complete short online tutorials.")

        with tab_study:
            st.subheader(f"Weekly Preparation Plan (Current Score: {score}%)")
            st.write("Follow this structured plan to address your skill gaps and prepare for the role:")
            
            col_plan_1, col_plan_2 = st.columns(2)
            with col_plan_1:
                st.markdown("#### 📅 Week 1: Target Skill Gaps")
                if missing:
                    for i, skill in enumerate(missing[:4], 1):
                        st.markdown(f"- **Day {i*2-1} to {i*2}**: Study and practice **{skill.upper()}**.")
                else:
                    st.markdown("- You have no major skill gaps! Use this week to review advanced concepts or review your project code.")
                    
            with col_plan_2:
                st.markdown("#### 📅 Week 2: Apply & Practice")
                st.markdown("- Work on a mini-project combining your top skills.")
                st.markdown("- Push your code to GitHub with a clear, readable README.")
                st.markdown("- Practice explaining your project architecture and choices out loud.")
                
            st.markdown("---")
            st.markdown("#### 📋 Final Checklist Before Interview")
            st.checkbox("Review technical questions generated in the 'Interview Prep' tab.", value=False)
            st.checkbox("Prepare behavioral answers using the STAR technique (Situation, Task, Action, Result).", value=False)
            st.checkbox("Research the company's background, core business, and culture.", value=False)

# --- MENU: INTERVIEW PREP ---
elif menu == "💡 Interactive Interview Prep":
    st.markdown('<div class="section-title">Interview Preparation & Q&A</div>', unsafe_allow_html=True)
    
    st.subheader("Knowledge Base Study Notes")
    kb_uploader = st.file_uploader("Upload Study Notes / Knowledge Base (.txt)", type=["txt"])
    if kb_uploader is not None:
        st.session_state.kb_text = load_file_content(kb_uploader)
        
    kb_input = st.text_area("Or Paste Study/Interview Notes here:", value=st.session_state.kb_text, height=150)
    st.session_state.kb_text = kb_input
    
    st.markdown("---")
    
    if not st.session_state.get('analyzed', False):
        st.info("Run the **🔍 Resume Skill Matcher** analysis first to generate technical questions for the required job skills.")
    else:
        job_skills = st.session_state.job_skills
        kb_text = st.session_state.kb_text
        
        tech_tab, hr_tab, kb_tab = st.tabs(["💻 Technical Questions", "👥 HR & Behavioral", "📚 Notes-Based Questions"])
        
        with tech_tab:
            st.subheader("Technical Questions")
            st.write("These questions are automatically generated based on the skills extracted from the job poster:")
            
            for skill in job_skills:
                with st.expander(f"Skill: {skill.upper()}", expanded=False):
                    st.write(f"**Q1:** Explain your understanding and core concepts of **{skill}**.")
                    st.write(f"**Q2:** Describe a project or instance where you utilized **{skill}** and how it solved a problem.")
                    
        with hr_tab:
            st.subheader("HR and Behavioral Questions")
            hr_questions = [
                "Tell me about yourself.",
                "Why are you interested in this role and company?",
                "Describe your best project. What went well, and what were the challenges?",
                "What are your key strengths and weaknesses?",
                "Where do you see yourself in 3 years?",
                "Why should we select you over other candidates?"
            ]
            for i, q in enumerate(hr_questions, 1):
                with st.expander(f"Question {i}: {q}", expanded=False):
                    st.write("💡 *Tip: Answer in the STAR structure (Situation, Task, Action, Result). Highlight your ability to learn quickly and adapt.*")
                    
        with kb_tab:
            st.subheader("Knowledge Base Generated Questions")
            if not kb_text.strip():
                st.info("Paste or upload study notes above to extract custom questions from your knowledge base.")
            else:
                kb_lines = [line.strip() for line in kb_text.splitlines() if line.strip() and len(line.strip()) > 20]
                if not kb_lines:
                    st.write("Your notes are too short. Please add more descriptive content.")
                else:
                    st.write("We extracted the following questions based on key points in your study notes:")
                    for i, line in enumerate(kb_lines[:8], 1):
                        with st.expander(f"Question {i} (from notes): How would you explain this concept?", expanded=False):
                            st.markdown(f"*'{line}'*")
                            st.write("💡 *Review this note and practice explaining it in your own words.*")

# --- MENU: APPLICATION TRACKER ---
elif menu == "📊 Application Status Tracker":
    st.markdown('<div class="section-title">Application Status Tracker & Reminders</div>', unsafe_allow_html=True)
    
    df_apps = st.session_state.applications
    
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t2:
        st.subheader("🔔 Reminders & Action Items")
        today_date = date.today()
        
        reminders_found = False
        for idx, row in df_apps.iterrows():
            status = str(row.get("status", "")).lower()
            company = row.get("company", "")
            role = row.get("role", "")
            
            if status == "interview scheduled" and row.get("interview_date"):
                st.error(f"🚨 **Interview scheduled** at **{company}** for **{role}** on **{row.get('interview_date')}**!\nAction: {row.get('next_action', 'Prepare!')}")
                reminders_found = True
            elif status == "applied" and row.get("follow_up_date"):
                st.warning(f"📅 Follow up with **{company}** (**{role}**) on **{row.get('follow_up_date')}**.")
                reminders_found = True
            elif status == "not applied":
                st.info(f"✍️ Tailor resume and apply for **{role}** at **{company}**.")
                reminders_found = True
                
        if not reminders_found:
            st.success("All caught up! No critical upcoming interview or follow-up reminders.")
            
    with col_t1:
        st.subheader("Job Applications Log")
        st.write("Directly edit the tracker table below or use the form to append a new application. Changes are saved back to your files.")
        
        # Display editable data editor
        edited_df = st.data_editor(
            df_apps, 
            num_rows="dynamic",
            key="tracker_editor",
            height=300
        )
        
        # Save modifications
        if st.button("💾 Save Tracker Changes"):
            if save_applications(edited_df):
                st.session_state.applications = edited_df
                st.success("Tracker updated and saved successfully!")
                st.rerun()

    st.markdown("---")
    
    # Form to add new application
    st.subheader("➕ Add New Application")
    with st.form("new_app_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            company = st.text_input("Company Name")
            role = st.text_input("Job Role / Position")
            source = st.text_input("Source (e.g. LinkedIn, Rozee.pk, Website)")
            status = st.selectbox("Status", ["Not Applied", "Applied", "Interview Scheduled", "Offer Received", "Rejected"])
            
        with col_f2:
            applied_date = st.date_input("Applied Date", value=None)
            interview_date = st.date_input("Interview Date", value=None)
            follow_up_date = st.date_input("Follow-up Date", value=None)
            next_action = st.text_input("Next Action Item")
            
        notes = st.text_area("Notes")
        
        submit_btn = st.form_submit_button("Add Application")
        if submit_btn:
            if not company or not role:
                st.error("Company Name and Job Role are required.")
            else:
                # Generate new ID
                if len(df_apps) > 0:
                    try:
                        last_id_num = max(df_apps['application_id'].apply(lambda x: int(x.split('-')[1]) if '-' in str(x) else 0))
                        new_id = f"APP-{str(last_id_num + 1).zfill(3)}"
                    except:
                        new_id = f"APP-{str(len(df_apps) + 1).zfill(3)}"
                else:
                    new_id = "APP-001"
                    
                new_row = {
                    "application_id": new_id,
                    "company": company,
                    "role": role,
                    "source": source,
                    "status": status,
                    "applied_date": applied_date.strftime("%Y-%m-%d") if applied_date else "",
                    "interview_date": interview_date.strftime("%Y-%m-%d") if interview_date else "",
                    "follow_up_date": follow_up_date.strftime("%Y-%m-%d") if follow_up_date else "",
                    "next_action": next_action,
                    "notes": notes
                }
                
                updated_df = pd.concat([df_apps, pd.DataFrame([new_row])], ignore_index=True)
                if save_applications(updated_df):
                    st.session_state.applications = updated_df
                    st.success(f"Added new application {new_id} successfully!")
                    st.rerun()

    # Import / Export panel
    st.markdown("---")
    st.subheader("📥 Import / Export Tracker Data")
    col_csv1, col_csv2 = st.columns(2)
    with col_csv1:
        st.write("Export your active tracker file to CSV:")
        csv_data = df_apps.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download applications.csv",
            data=csv_data,
            file_name="applications.csv",
            mime="text/csv"
        )
    with col_csv2:
        st.write("Upload a different tracker CSV to restore progress:")
        uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_csv is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_csv)
                if save_applications(uploaded_df):
                    st.session_state.applications = uploaded_df
                    st.success("Uploaded CSV applied successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing uploaded CSV: {e}")
