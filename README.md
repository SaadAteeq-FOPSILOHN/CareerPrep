# 🚀 CareerPrep AI Copilot

[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://careerprep-gzhuxexeisesjizkdfpdo9.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)

## 📌 Overview

CareerPrep is a comprehensive, production-deployed 
AI-powered Career Copilot that automates the entire 
job search and preparation lifecycle. Built with 
Python, Streamlit, and Google Gemini 2.5 Flash API, 
it combines intelligent resume optimization, semantic 
job matching, live interview coaching, automated 
outreach drafting, and an analytics-powered 
application tracker — all in one platform.

## 🌐 Live Demo

🔗 https://careerprep-gzhuxexeisesjizkdfpdo9.streamlit.app/

## ✨ Features

### 📄 CV / Resume Optimization
- Gemini AI contextually rewrites resume experience 
  sections to match target job descriptions
- Export optimized resume as print-ready HTML/PDF

### 🎯 Semantic Job Matching
- Dynamic AI-powered match score calculation
- Compares your resume directly to any job description
- Highlights matched skills and identifies skill gaps

### 🎤 Interview Coaching
- Generates technical, HR, and study-note-based 
  interview questions
- Live AI recruiter chatbot conducts full mock interviews
- Evaluates your responses and scores them out of 10

### 🔍 Job Search & Outreach
- Queries live remote jobs based on your skill set
- Add jobs directly to your tracking board
- Auto-drafts tailored LinkedIn connection notes 
  and cold emails

### 📊 Application Tracker
- Interactive Kanban board for application management
- Analytics dashboard with conversion rates, source 
  statistics, and application velocity charts

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend / UI | Python + Streamlit |
| Custom Styling | HTML/CSS injection, SVG animations, Light/Dark mode |
| AI Engine | Google Gemini 2.5 Flash API (Google AI Studio) |
| Data Storage | Pandas + CSV (dynamic sync) |
| PDF Parser | PyPDF |
| DOCX Parser | Custom XML unpacker (dependency-free) |
| Deployment | Streamlit Cloud |

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/SaadAteeq-FOPSILOHN/CareerPrep.git

# Navigate to project directory
cd CareerPrep

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key to secrets
# Create .streamlit/secrets.toml and add:
# GEMINI_API_KEY = "your_key_here"

# Run the app
streamlit run app.py
```

## 🔑 Environment Variables

Create a `.streamlit/secrets.toml` file:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

## 👨‍💻 Development

This project was built as a product collaboration:
- **Product Lead & Developer:** Saad Khan — feature 
  specifications, visual architecture design, 
  security configuration, and end-to-end user testing
- **AI Co-Developer:** Antigravity — layout 
  implementation, Python processing pipelines, 
  custom CSS, and Git deployment pipeline

## 📄 License

This project is open source and available for 
personal and educational use.
