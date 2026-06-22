# Reflection

## What I Built

I built a file-driven Job-Hunting Agent in Python called CareerPrep. The agent reads job posters, resumes, and knowledge base notes from organized folders. It extracts keywords, compares them, calculates a match score, and generates multiple output reports to help with job applications.

## How It Works

The agent uses the GAME framework:
- **Goal**: Help a student manage job applications from start to interview
- **Actions**: Read files, extract skills, match, generate reports, track applications
- **Memory**: Tracks application status in a CSV file across runs
- **Environment**: Local folders and text files

## What I Tested

- Ran the agent with one job poster, one resume, and one KB file
- Verified all 5 output files were generated in outputs/
- Verified applications.csv and reminders.txt were created in tracker/
- Confirmed match score calculation worked correctly

## Challenges

- Understanding how to read multiple files from folders dynamically
- Structuring the output reports to be clear and readable
- Making the reminder logic work with different application statuses

## What I Would Improve

- Add PDF reading support using PyMuPDF
- Add a Streamlit interface for a better user experience
- Integrate an LLM API for smarter keyword extraction
- Add urgency levels to reminders (today, this week, overdue)

After creating all files, run these git commands:

git add .
git commit -m "Complete job-hunting agent submission"
git push origin main