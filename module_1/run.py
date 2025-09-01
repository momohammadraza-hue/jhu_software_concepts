from flask import Flask, render_template

# Module 1 Personal Website (3 routes). Each route sets `active`
# so base.html can color the navbar + background for that page.
app = Flask(__name__)

# / — Home: bio card (left) + profile image (right)
@app.route("/")
def home():
    return render_template("home.html", active="home")

# /projects — Projects: green cards + GitHub link
@app.route("/projects")
def projects():
    projects_data = [
        {
            "title": "Module 1: Personal Website",
            "description": (
                "A personal website created for JHU Modern Software Concepts — "
                "built to share background, contact info, and future projects "
                "in a simple, accessible way."
            ),
            "github_url": "https://github.com/momohammadraza-hue/jhu_software_concepts/tree/main/module_1",
        }
    ]
    return render_template("projects.html", active="projects", projects=projects_data)

# /contact — Contact: bark-themed card with email + LinkedIn
@app.route("/contact")
def contact():
    return render_template("contact.html", active="contact")

# Runs on 0.0.0.0:8080 (per assignment). Start with: python3 run.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)