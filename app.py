import os
import csv
from datetime import datetime, date

JOB_DIR = "input_jobs"
RESUME_DIR = "input_resumes"
KB_DIR = "input_kb"
OUTPUT_DIR = "outputs"
TRACKER_DIR = "tracker"

KEYWORDS = [
    "python", "machine learning", "data preprocessing", "github", "git",
    "api", "prompt engineering", "sql", "communication", "problem solving",
    "oop", "database", "jupyter", "pandas", "numpy", "deep learning",
    "html", "css", "flask", "streamlit", "resume", "interview"
]

def ensure_folders():
    for folder in [JOB_DIR, RESUME_DIR, KB_DIR, OUTPUT_DIR, TRACKER_DIR]:
        os.makedirs(folder, exist_ok=True)

def read_text_files(folder):
    combined_text = ""
    file_count = 0
    for filename in os.listdir(folder):
        if filename.lower().endswith(".txt"):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as file:
                combined_text += f"\n\n--- FILE: {filename} ---\n"
                combined_text += file.read()
                file_count += 1
    return combined_text, file_count

def save_text(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

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

def generate_job_analysis(job_text, job_skills):
    report = "JOB ANALYSIS REPORT\n"
    report += "=" * 40 + "\n\n"
    report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report += "Skills and keywords found in job poster:\n"
    for skill in job_skills:
        report += f"  - {skill}\n"
    report += f"\nTotal skills required: {len(job_skills)}\n"
    return report

def generate_skill_gap_report(job_skills, resume_skills, matched, missing, score):
    report = "SKILL GAP REPORT\n"
    report += "=" * 40 + "\n\n"
    report += f"Match Score: {score}%\n\n"
    report += f"Matched Skills ({len(matched)}):\n"
    for skill in matched:
        report += f"  [OK] {skill}\n"
    report += f"\nMissing Skills ({len(missing)}):\n"
    for skill in missing:
        report += f"  [MISSING] {skill}\n"
    report += "\nRecommendation:\n"
    if score >= 70:
        report += "  Strong match. Apply with confidence.\n"
    elif score >= 40:
        report += "  Moderate match. Work on missing skills before applying.\n"
    else:
        report += "  Weak match. Significant skill development needed.\n"
    return report

def generate_resume_suggestions(job_skills, missing):
    output = "TAILORED RESUME SUGGESTIONS\n"
    output += "=" * 40 + "\n\n"
    output += "Improvements based on job requirements:\n\n"
    for skill in job_skills:
        output += f"  - Add clear evidence of {skill} in your resume.\n"
    output += "\nSuggested resume bullet points:\n"
    output += "  - Built Python-based ML project with data preprocessing and model evaluation.\n"
    output += "  - Used GitHub for version control with proper commit history and README.\n"
    output += "  - Developed a REST API integration project using Python requests library.\n"
    output += "  - Applied prompt engineering to build a Streamlit AI demo application.\n"
    output += "  - Queried and managed databases using SQL with complex JOIN operations.\n"
    if missing:
        output += "\nSkills to develop before interview:\n"
        for skill in missing:
            output += f"  - Study and practice: {skill}\n"
    return output

def generate_interview_questions(job_skills, kb_text):
    questions = "INTERVIEW QUESTIONS\n"
    questions += "=" * 40 + "\n\n"
    questions += "Technical Questions (from job requirements):\n"
    for skill in job_skills:
        questions += f"  Q: Explain your understanding of {skill}.\n"
        questions += f"  Q: How have you used {skill} in a project?\n\n"
    questions += "\nHR and Behavioral Questions:\n"
    questions += "  Q: Tell me about yourself.\n"
    questions += "  Q: Why are you interested in this role?\n"
    questions += "  Q: Describe your best project.\n"
    questions += "  Q: What are your strengths and weaknesses?\n"
    questions += "  Q: Where do you see yourself in 3 years?\n"
    questions += "  Q: Why should we select you over other candidates?\n"
    questions += "\nQuestions from Knowledge Base:\n"
    kb_lines = [line.strip() for line in kb_text.splitlines() if line.strip() and len(line.strip()) > 20]
    for line in kb_lines[:8]:
        questions += f"  Q: How would you explain this in an interview: '{line[:80]}'\n"
    return questions

def generate_preparation_plan(missing, score):
    plan = "PREPARATION PLAN\n"
    plan += "=" * 40 + "\n\n"
    plan += f"Current match score: {score}%\n\n"
    plan += "Week 1 - Focus Areas:\n"
    for i, skill in enumerate(missing[:4], 1):
        plan += f"  Day {i*2-1}-{i*2}: Study and practice {skill}\n"
    plan += "\nWeek 2 - Practice:\n"
    plan += "  - Work on a mini project combining your top skills\n"
    plan += "  - Push the project to GitHub with a clear README\n"
    plan += "  - Practice explaining your projects out loud\n"
    plan += "\nBefore Interview:\n"
    plan += "  - Review all technical questions in interview_questions.txt\n"
    plan += "  - Prepare STAR format answers for behavioral questions\n"
    plan += "  - Research the company and role thoroughly\n"
    return plan

def create_or_update_tracker():
    path = os.path.join(TRACKER_DIR, "applications.csv")
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as file:
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
    return path

def generate_reminders():
    tracker_path = os.path.join(TRACKER_DIR, "applications.csv")
    reminders = "APPLICATION REMINDERS\n"
    reminders += "=" * 40 + "\n\n"
    reminders += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    if not os.path.exists(tracker_path):
        return reminders + "No tracker file found.\n"
    today = date.today()
    with open(tracker_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            app_id = row.get("application_id", "")
            company = row.get("company", "")
            role = row.get("role", "")
            status = row.get("status", "").lower()
            interview_date = row.get("interview_date", "")
            follow_up_date = row.get("follow_up_date", "")
            next_action = row.get("next_action", "")
            reminders += f"[{app_id}] {role} at {company}\n"
            reminders += f"  Status: {status.title()}\n"
            if status == "interview scheduled" and interview_date:
                reminders += f"  *** INTERVIEW on {interview_date} ***\n"
                reminders += f"  Action: {next_action}\n"
            elif status == "not applied":
                reminders += f"  TODO: Tailor resume and apply soon.\n"
            elif status == "applied":
                reminders += f"  Follow up on: {follow_up_date}\n"
            reminders += "\n"
    return reminders

def run_agent():
    print("\n" + "="*50)
    print("   CareerPrep Job-Hunting Agent")
    print("="*50)
    ensure_folders()
    print("\n[1] Reading input files...")
    job_text, job_count = read_text_files(JOB_DIR)
    resume_text, resume_count = read_text_files(RESUME_DIR)
    kb_text, kb_count = read_text_files(KB_DIR)
    if job_count == 0 or resume_count == 0 or kb_count == 0:
        print("ERROR: Please add .txt files in input_jobs, input_resumes, and input_kb folders.")
        return
    print(f"   Job files: {job_count} | Resume files: {resume_count} | KB files: {kb_count}")
    print("\n[2] Analyzing skills...")
    job_skills = extract_keywords(job_text)
    resume_skills = extract_keywords(resume_text)
    matched, missing, score = compare_skills(job_skills, resume_skills)
    print(f"   Match Score: {score}%")
    print(f"   Matched: {len(matched)} skills | Missing: {len(missing)} skills")
    print("\n[3] Generating reports...")
    job_report = generate_job_analysis(job_text, job_skills)
    gap_report = generate_skill_gap_report(job_skills, resume_skills, matched, missing, score)
    resume_suggestions = generate_resume_suggestions(job_skills, missing)
    interview_questions = generate_interview_questions(job_skills, kb_text)
    prep_plan = generate_preparation_plan(missing, score)
    print("\n[4] Updating application tracker...")
    create_or_update_tracker()
    reminders = generate_reminders()
    print("\n[5] Saving all outputs...")
    save_text(os.path.join(OUTPUT_DIR, "job_analysis_report.txt"), job_report)
    save_text(os.path.join(OUTPUT_DIR, "skill_gap_report.txt"), gap_report)
    save_text(os.path.join(OUTPUT_DIR, "tailored_resume_suggestions.txt"), resume_suggestions)
    save_text(os.path.join(OUTPUT_DIR, "interview_questions.txt"), interview_questions)
    save_text(os.path.join(OUTPUT_DIR, "preparation_plan.txt"), prep_plan)
    final_report = "CAREERPREP JOB-HUNTING AGENT - FINAL REPORT\n"
    final_report += "=" * 50 + "\n"
    final_report += f"Generated: {datetime.now()}\n\n"
    final_report += job_report + "\n" + gap_report + "\n"
    final_report += resume_suggestions + "\n" + interview_questions + "\n"
    final_report += prep_plan + "\n" + reminders
    save_text(os.path.join(OUTPUT_DIR, "final_agent_report.txt"), final_report)
    save_text(os.path.join(TRACKER_DIR, "reminders.txt"), reminders)
    print("\n" + "="*50)
    print("   AGENT COMPLETED SUCCESSFULLY")
    print("="*50)
    print(f"   Match Score : {score}%")
    print(f"   Outputs saved in: outputs/")
    print(f"   Tracker saved in: tracker/")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_agent()