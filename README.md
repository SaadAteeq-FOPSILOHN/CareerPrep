# CareerPrep Job-Hunting Agent

An interactive web dashboard and file-driven job-hunting agent.

## How to Run

### Option 1: Streamlit Web Dashboard (Recommended)

1. Make sure Python 3.7+ is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app_streamlit.py
   ```
4. Access the dashboard in your browser (typically at http://localhost:8501) to:
   - Upload PDF/TXT Resumes and Job postings.
   - Run interactive matching reports and weekly study plans.
   - Manage job applications via a dynamic tracker table.
   - Generate study note Q&A guides.

### Option 2: CLI Agent (Original Version)

1. Add your own files (optional):
   - Paste a job poster into `input_jobs/`
   - Paste your resume into `input_resumes/`
   - Paste course notes into `input_kb/`
2. Run the agent:
   ```bash
   python app.py
   ```
3. Check generated files in `outputs/` and `tracker/`


## Output Files

| File | Description |
|------|-------------|
| outputs/job_analysis_report.txt | Skills extracted from job poster |
| outputs/skill_gap_report.txt | Match score and missing skills |
| outputs/tailored_resume_suggestions.txt | Resume improvement tips |
| outputs/interview_questions.txt | Technical and HR questions |
| outputs/preparation_plan.txt | Weekly study plan |
| outputs/final_agent_report.txt | Full combined report |
| tracker/applications.csv | Application status tracker |
| tracker/reminders.txt | Interview and follow-up reminders |

## Folder Structure
job-hunting-agent/
├── app.py
├── requirements.txt
├── README.md
├── reflection.md
├── input_jobs/
├── input_resumes/
├── input_kb/
├── outputs/
├── tracker/
└── samples/