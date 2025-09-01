JHU Modern Software Concepts — Module 1: Personal Website
Author: Mohammad Raza  

What this is  
- A Flask app for my personal site (Module 1).  
- Three pages: Home, Projects, Contact.  
- Each page has its own theme (blue, green, bark brown) with hover + active nav states.  
- Content shown in cards for clarity and consistent design.  

What you need  
- Python 3.10+  
- Flask (install from requirements.txt — pinned version included)  
- Virtual environment recommended  

How to run it  
1) cd module_1  
2) python3 -m venv .venv  
3) source .venv/bin/activate   (Windows: .\.venv\Scripts\Activate.ps1)  
4) pip install -r requirements.txt  
5) python3 run.py  

Where it runs  
- http://localhost:8080  
- Bound to 0.0.0.0:8080 (per assignment)  

Pages  
- `/` → Home (bio card left, photo right)  
- `/projects` → Project card + GitHub link  
- `/contact` → Bark card with email + LinkedIn  

Structure  
- run.py → app entry point  
- /templates → HTML templates (base, home, projects, contact)  
- /static/css → style.css (per-page themes, cards, nav hover/active)  
- /static/img → profile.jpg  

Deliverables  
- requirements.txt → pinned dependencies  
- README.txt → run instructions + notes (this file)  
- screenshots.pdf → full-page screenshots of Home, Projects, Contact  

Challenges & Learnings  
- Fixed architecture mismatch on Mac by reinstalling Apple Command Line Tools.  
- Learned Git tracks only non-empty folders (used .gitkeep initially).  
- Resolved "flask not found" by activating venv before running.  
- Tweaked CSS until nav hover/active and page themes matched requirements.  

That’s it — clean, themed, and ready to run.  