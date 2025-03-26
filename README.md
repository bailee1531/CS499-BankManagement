# CS499 - 03 Group 3b

## Python Packages in Virtual Environment

### Installed via Flask (directly or as dependencies)

- blinker  
- click  
- itsdangerous  
- Jinja2  
- MarkupSafe  
- Werkzeug  

### Installed via Other Packages

- dnspython *(via email_validator)*  
- WTForms *(via Flask-WTF)*  
- python-dateutil *(via pandas)*  
- pytz *(via pandas)*  
- numpy *(via pandas)*
- six *(via python-dateutil)*  
- tzdata *(via pytz)*  
- idna *(via dnspython)*  

### Manually Installed (likely)

- email_validator  
- Flask-WTF  
- pandas  
- pycryptodome  

---

## Setting Up a Virtual Environment and Installing Flask

### macOS

#### Create a virtual environment

\`\`\`bash
python3 -m venv .venv
\`\`\`

#### Activate the environment

\`\`\`bash
. .venv/bin/activate
\`\`\`

#### Install Flask

\`\`\`bash
pip install Flask
\`\`\`

---

### Windows

#### Create a virtual environment

\`\`\`powershell
py -3 -m venv .venv
\`\`\`

#### Activate the environment

\`\`\`powershell
.venv\Scripts\activate
\`\`\`

#### Install Flask

\`\`\`bash
pip install Flask
\`\`\`

---

## Running the App

Once the virtual environment is activated, run:

\`\`\`bash
python3 run.py
\`\`\`