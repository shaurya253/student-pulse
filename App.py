import io
import os
from flask import Flask, redirect, render_template_string, request, url_for
import pandas as pd

app = Flask(__name__)

# ====================================
# BUILT-IN DEMO DATA
# ====================================
DEMO_CSV_DATA = """Student_ID,Name,Attendance,Participation,Activities,Interaction,Mood,Parent_Phone
S001,Ashmit Gupta,65,20,10,15,3,918910563292
S002,Devyansh Nawalgaria,90,85,75,80,5,919147370929
S003,Siva Khawas,72,50,40,45,4,919911860299
S004,Shaurya Sen,40,10,0,5,1,919930992075"""

LIVE_DF = None

# ====================================
# ENGINE FUNCTIONS
# ====================================
def calculate_risk(student):
    score = (
        (100 - student["Attendance"]) * 0.20 +
        (100 - student["Participation"]) * 0.25 +
        (100 - student["Activities"]) * 0.20 +
        (100 - student["Interaction"]) * 0.25 +
        ((5 - student["Mood"]) * 20) * 0.10
    )
    if score < 30:
        return "Low"
    elif score < 60:
        return "Moderate"
    else:
        return "High"

def calculate_engagement(student):
    score = (
        student["Attendance"] * 0.30 +
        student["Participation"] * 0.25 +
        student["Activities"] * 0.15 +
        student["Interaction"] * 0.20 +
        (student["Mood"] * 20) * 0.10
    )
    return round(score)

def generate_root_cause_analysis(student):
    name = student['Name']
    attendance = student['Attendance']
    participation = student['Participation']
    activities = student['Activities']
    interaction = student['Interaction']
    mood = student['Mood']

    causes = []
    if attendance < 70:
        causes.append("Chronically low attendance disrupting consistent learning retention.")
    if participation < 40 or interaction < 30:
        causes.append("Severe classroom disengagement and social withdrawal from peers.")
    if mood <= 2:
        causes.append("Significant emotional distress or burnout affecting daily academic energy.")
    if activities < 20:
        causes.append("Lack of institutional integration via extracurricular involvement.")

    if not causes:
        return f"Diagnostic Summary: {name} demonstrates stable behavioral and academic patterns across all tracked indicators."

    primary_cause = causes[0]
    full_narrative = f"Root Cause Analysis: {name}'s academic vulnerability is primarily driven by {primary_cause.lower()}"
    if len(causes) > 1:
        full_narrative += f" Secondary compounding factors include: {' '.join(causes[1:])}"
    return full_narrative

def generate_teacher_action_plan(student):
    actions = []
    if student["Attendance"] < 75:
        actions.append("Schedule a 10-minute check-in to discuss attendance barriers.")
    if student["Participation"] < 40:
        actions.append("Incorporate low-pressure, structured group tasks to rebuild confidence.")
    if student["Mood"] <= 2:
        actions.append("Refer student for a confidential school counselor consultation.")
    if student["Activities"] < 20:
        actions.append("Recommend school clubs aligned with student interests.")
    if not actions:
        actions.append("Maintain positive reinforcement and monitor bi-weekly progress.")
    return actions

def generate_parent_message(student):
    name = student['Name']
    risk = calculate_risk(student)
    if risk == "Low":
        return f"Subject: Positive Term Update Regarding {name}\n\nDear Parent/Guardian,\n\nWe are writing to share a positive progress report regarding {name}. They are maintaining healthy engagement levels and attendance this term. Thank you for your continued support."
    return f"Subject: Academic & Wellbeing Update for {name}\n\nDear Parent/Guardian,\n\nWe are reaching out to discuss {name}'s current progress and collaborate on supportive action strategies. Please let us know your availability for a brief consultation."

def generate_weekly_tracker(student):
    risk = calculate_risk(student)
    if risk == "High":
        return {"status": "Weekly Intensive Monitoring", "frequency": "Mandatory bi-weekly check-ins", "border": "border-red-200 bg-red-50 text-red-900"}
    elif risk == "Moderate":
        return {"status": "Bi-Weekly Progress Review", "frequency": "Monthly advisor review", "border": "border-amber-200 bg-amber-50 text-amber-900"}
    else:
        return {"status": "Standard Routine Tracking", "frequency": "Term-end evaluation", "border": "border-stone-200 bg-stone-50 text-stone-800"}

def find_best_match(student, original_df):
    best_match = None
    best_score = -1
    for _, other in original_df.iterrows():
        if other["Student_ID"] == student["Student_ID"]:
            continue
        difference = abs(student["Participation"] - other["Participation"]) + abs(student["Interaction"] - other["Interaction"]) + abs(student["Mood"] - other["Mood"])
        compatibility = max(0, 100 - difference)
        if compatibility > best_score:
            best_score = compatibility
            best_match = {"name": other["Name"], "score": round(compatibility)}
    return best_match


# ====================================
# ROUTE 1: LANDING PAGE WITH LOADER
# ====================================
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-50 text-stone-900 font-sans antialiased flex flex-col justify-between min-h-screen relative">
        
        <!-- Loading Overlay -->
        <div id="loadingOverlay" class="fixed inset-0 bg-white/80 backdrop-blur-xs z-50 flex flex-col items-center justify-center hidden">
            <div class="w-8 h-8 border-2 border-stone-300 border-t-stone-900 rounded-full animate-spin mb-3"></div>
            <p class="text-xs font-medium text-stone-700 tracking-wide">Initializing Demo Workspace...</p>
        </div>

        <header class="border-b border-stone-200 px-8 py-4 flex justify-between items-center bg-white shadow-2xs">
            <span class="font-bold text-sm tracking-tight text-stone-800">STUDENT PULSE</span>
            <nav class="flex gap-6 text-xs font-medium text-stone-600">
                <a href="/" class="text-stone-900 font-semibold">Home</a>
                <a href="/about" class="hover:text-stone-900 transition">About Us</a>
                <a href="/faq" class="hover:text-stone-900 transition">FAQs</a>
                <a href="/contact" class="hover:text-stone-900 transition">Contact Us</a>
            </nav>
        </header>
        
        <main class="max-w-5xl mx-auto px-6 w-full py-12">
            <div class="bg-white p-10 rounded-2xl border border-stone-200 shadow-2xs mb-8">
                <div class="max-w-2xl">
                    <span class="inline-block px-2.5 py-1 mb-3 rounded text-[10px] font-bold uppercase tracking-wider bg-stone-100 text-stone-700 border border-stone-200">Student Pulse AI - Capstone Project</span>
                    <h1 class="text-3xl font-extrabold tracking-tight text-stone-900 mb-4">Institutional Student Analytics & Early Warning System</h1>
                    <p class="text-sm text-stone-600 mb-8 leading-relaxed">
                        A comprehensive administrative dashboard empowering faculty to track engagement metrics, execute risk diagnostics, form peer-support networks, and streamline parent communication.
                    </p>
                    <div class="flex gap-3">
                        <a href="/demo" onclick="triggerLoader(event)" class="px-6 py-3 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded-lg transition shadow-xs text-center">
                            Launch Demo Workspace
                        </a>
                        <a href="/upload-page" class="px-6 py-3 bg-white hover:bg-stone-50 text-stone-700 text-xs font-semibold rounded-lg border border-stone-300 transition shadow-xs text-center">
                            Upload Custom CSV
                        </a>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white p-6 rounded-xl border border-stone-200 shadow-2xs">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-2">01 / Diagnostics</h3>
                    <h4 class="text-sm font-bold text-stone-900 mb-1">Root-Cause Analysis</h4>
                    <p class="text-xs text-stone-600 leading-relaxed">Automatically identifies underlying risk factors across attendance, participation, and mood indicators.</p>
                </div>
                <div class="bg-white p-6 rounded-xl border border-stone-200 shadow-2xs">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-2">02 / Intervention</h3>
                    <h4 class="text-sm font-bold text-stone-900 mb-1">Peer-Buddy Matching</h4>
                    <p class="text-xs text-stone-600 leading-relaxed">Calculates peer compatibility scores to pair vulnerable students with engaged student buddies.</p>
                </div>
                <div class="bg-white p-6 rounded-xl border border-stone-200 shadow-2xs">
                    <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-2">03 / Communication</h3>
                    <h4 class="text-sm font-bold text-stone-900 mb-1">WhatsApp Integration</h4>
                    <p class="text-xs text-stone-600 leading-relaxed">Dispatches pre-drafted progress updates and intervention notices directly to parents instantly.</p>
                </div>
            </div>
        </main>

        <footer class="border-t border-stone-200 px-8 py-4 flex justify-between items-center text-xs text-stone-400 bg-white">
            <span>Academic Performance & Retention Engine</span>
            <div class="flex gap-4">
                <a href="/about" class="hover:underline">About</a>
                <a href="/faq" class="hover:underline">FAQs</a>
                <a href="/contact" class="hover:underline">Contact</a>
            </div>
        </footer>

        <script>
        function triggerLoader(event) {
            event.preventDefault();
            document.getElementById('loadingOverlay').classList.remove('hidden');
            setTimeout(function() {
                window.location.href = "/demo";
            }, 500);
        }
        </script>
    </body>
    </html>
    """


# ====================================
# ROUTE 2: ABOUT US PAGE
# ====================================
@app.route("/about")
def about():
    return """
    <html>
    <head>
        <title>About Us - Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-50 text-stone-900 font-sans antialiased flex flex-col justify-between min-h-screen">
        <header class="border-b border-stone-200 px-8 py-4 flex justify-between items-center bg-white shadow-2xs">
            <span class="font-bold text-sm tracking-tight text-stone-800">STUDENT PULSE</span>
            <nav class="flex gap-6 text-xs font-medium text-stone-600">
                <a href="/" class="hover:text-stone-900 transition">Home</a>
                <a href="/about" class="text-stone-900 font-semibold">About Us</a>
                <a href="/faq" class="hover:text-stone-900 transition">FAQs</a>
                <a href="/contact" class="hover:text-stone-900 transition">Contact Us</a>
            </nav>
        </header>

        <main class="max-w-2xl mx-auto px-6 w-full py-16">
            <div class="bg-white p-8 rounded-xl shadow-2xs border border-stone-200 space-y-6">
                <h1 class="text-2xl font-bold tracking-tight text-stone-900">About the Project</h1>
                <p class="text-xs text-stone-600 leading-relaxed">
                    Student Pulse is built as a capstone project to bridge the gap between institutional data and timely student intervention. By aggregating indicators such as attendance, participation metrics, extracurricular activities, and emotional well-being scores, our diagnostic engine highlights vulnerable student profiles before academic setbacks compound.
                </p>
                <h2 class="text-sm font-bold text-stone-900 pt-2">Core Architecture</h2>
                <ul class="list-disc pl-4 text-xs text-stone-600 space-y-2">
                    <li>Multi-factor risk weighting algorithm.</li>
                    <li>Automated peer-buddy pairing based on behavioral compatibility.</li>
                    <li>Pre-drafted administrative communication protocols for faculty efficiency.</li>
                </ul>
                <div class="pt-4">
                    <a href="/" class="text-xs font-medium text-stone-900 underline">← Return to Portal Home</a>
                </div>
            </div>
        </main>
        
        <footer class="border-t border-stone-200 px-8 py-4 text-center text-xs text-stone-400 bg-white">
            Academic Performance & Retention Engine
        </footer>
    </body>
    </html>
    """


# ====================================
# ROUTE 3: FAQ PAGE
# ====================================
@app.route("/faq")
def faq():
    return """
    <html>
    <head>
        <title>FAQs - Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-50 text-stone-900 font-sans antialiased flex flex-col justify-between min-h-screen">
        <header class="border-b border-stone-200 px-8 py-4 flex justify-between items-center bg-white shadow-2xs">
            <span class="font-bold text-sm tracking-tight text-stone-800">STUDENT PULSE</span>
            <nav class="flex gap-6 text-xs font-medium text-stone-600">
                <a href="/" class="hover:text-stone-900 transition">Home</a>
                <a href="/about" class="hover:text-stone-900 transition">About Us</a>
                <a href="/faq" class="text-stone-900 font-semibold">FAQs</a>
                <a href="/contact" class="hover:text-stone-900 transition">Contact Us</a>
            </nav>
        </header>

        <main class="max-w-2xl mx-auto px-6 w-full py-16">
            <div class="bg-white p-8 rounded-xl shadow-2xs border border-stone-200 space-y-6">
                <h1 class="text-2xl font-bold tracking-tight text-stone-900">Frequently Asked Questions</h1>
                
                <div class="space-y-4 text-xs text-stone-700">
                    <div class="border-b border-stone-100 pb-3">
                        <strong class="block font-bold text-stone-900 mb-1">How is the student risk level calculated?</strong>
                        <p class="text-stone-600 leading-relaxed">Risk levels (Low, Moderate, High) are computed dynamically using a weighted formula factoring in attendance, class participation, extracurricular activities, interaction scores, and student mood indexes.</p>
                    </div>
                    <div class="border-b border-stone-100 pb-3">
                        <strong class="block font-bold text-stone-900 mb-1">Can I upload my own custom CSV file?</strong>
                        <p class="text-stone-600 leading-relaxed">Yes! Simply select "Upload Custom CSV" from the home screen to evaluate any school dataset instantly in Live Mode.</p>
                    </div>
                    <div class="border-b border-stone-100 pb-3">
                        <strong class="block font-bold text-stone-900 mb-1">How does the WhatsApp notification feature work?</strong>
                        <p class="text-stone-600 leading-relaxed">Clicking the notification button on any student card automatically generates a pre-drafted progress or support message and opens WhatsApp Web/App addressed to the parent's registered contact number.</p>
                    </div>
                    <div>
                        <strong class="block font-bold text-stone-900 mb-1">Do I need an internet connection to run the demo?</strong>
                        <p class="text-stone-600 leading-relaxed">No. The demo mode uses embedded records and Tailwind CSS via CDN, running locally on your machine or USB drive without external server dependencies.</p>
                    </div>
                </div>

                <div class="pt-4">
                    <a href="/" class="text-xs font-medium text-stone-900 underline">← Return to Portal Home</a>
                </div>
            </div>
        </main>
        
        <footer class="border-t border-stone-200 px-8 py-4 text-center text-xs text-stone-400 bg-white">
            Academic Performance & Retention Engine
        </footer>
    </body>
    </html>
    """


# ====================================
# ROUTE 4: CONTACT US PAGE
# ====================================
@app.route("/contact")
def contact():
    return """
    <html>
    <head>
        <title>Contact Us - Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-50 text-stone-900 font-sans antialiased flex flex-col justify-between min-h-screen">
        <header class="border-b border-stone-200 px-8 py-4 flex justify-between items-center bg-white shadow-2xs">
            <span class="font-bold text-sm tracking-tight text-stone-800">STUDENT PULSE</span>
            <nav class="flex gap-6 text-xs font-medium text-stone-600">
                <a href="/" class="hover:text-stone-900 transition">Home</a>
                <a href="/about" class="hover:text-stone-900 transition">About Us</a>
                <a href="/faq" class="hover:text-stone-900 transition">FAQs</a>
                <a href="/contact" class="text-stone-900 font-semibold">Contact Us</a>
            </nav>
        </header>

        <main class="max-w-2xl mx-auto px-6 w-full py-16">
            <div class="bg-white p-8 rounded-xl shadow-2xs border border-stone-200 space-y-6">
                <h1 class="text-2xl font-bold tracking-tight text-stone-900">Project Development Team</h1>
                <p class="text-xs text-stone-600 leading-relaxed">
                    For technical inquiries, system evaluation, or administrative support, please reach out directly to the project development team below.
                </p>
                
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div class="p-4 bg-stone-50 rounded border border-stone-200 text-xs">
                        <strong class="block text-stone-900 font-semibold mb-1">Ashmit Gupta</strong>
                        <span class="text-stone-600 font-mono">+91 89105 63292</span>
                    </div>
                    <div class="p-4 bg-stone-50 rounded border border-stone-200 text-xs">
                        <strong class="block text-stone-900 font-semibold mb-1">Devyansh Nawalgaria</strong>
                        <span class="text-stone-600 font-mono">+91 91473 70929</span>
                    </div>
                    <div class="p-4 bg-stone-50 rounded border border-stone-200 text-xs">
                        <strong class="block text-stone-900 font-semibold mb-1">Siva Khawas</strong>
                        <span class="text-stone-600 font-mono">+91 99118 60299</span>
                    </div>
                    <div class="p-4 bg-stone-50 rounded border border-stone-200 text-xs">
                        <strong class="block text-stone-900 font-semibold mb-1">Shaurya Sen</strong>
                        <span class="text-stone-600 font-mono">+91 99309 92075</span>
                    </div>
                </div>

                <div class="pt-4">
                    <a href="/" class="text-xs font-medium text-stone-900 underline">← Return to Portal Home</a>
                </div>
            </div>
        </main>
        
        <footer class="border-t border-stone-200 px-8 py-4 text-center text-xs text-stone-400 bg-white">
            Academic Performance & Retention Engine
        </footer>
    </body>
    </html>
    """


# ====================================
# ROUTE 5: UPLOAD PAGE
# ====================================
@app.route("/upload-page")
def upload_page():
    return """
    <html>
    <head>
        <title>Upload Dataset - Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-50 text-stone-900 font-sans antialiased flex flex-col justify-between min-h-screen">
        <header class="border-b border-stone-200 px-8 py-4 flex justify-between items-center bg-white shadow-2xs">
            <span class="font-bold text-sm tracking-tight text-stone-800">STUDENT PULSE</span>
            <a href="/" class="text-xs font-medium text-stone-500 hover:text-stone-900 transition">Back</a>
        </header>

        <main class="max-w-md mx-auto px-6 w-full py-16">
            <div class="bg-white p-8 rounded-xl shadow-sm border border-stone-200">
                <h1 class="text-xl font-bold tracking-tight text-stone-900 mb-1">Dataset Ingestion</h1>
                <p class="text-xs text-stone-500 mb-6">Upload your district CSV file containing student records.</p>
                
                <form action="/upload" method="POST" enctype="multipart/form-data" class="space-y-4">
                    <input type="file" name="file" accept=".csv" required class="block w-full text-xs text-stone-500 file:mr-4 file:py-2 file:px-3 file:rounded file:border file:border-stone-300 file:text-xs file:font-medium file:bg-stone-50 file:text-stone-700 hover:file:bg-stone-100 cursor-pointer"/>
                    <button type="submit" class="w-full py-2.5 bg-stone-900 hover:bg-stone-800 text-white text-xs font-semibold rounded transition shadow-xs">
                        Process Dataset
                    </button>
                </form>
            </div>
        </main>
        
        <footer class="border-t border-stone-200 px-8 py-4 text-center text-xs text-stone-400 bg-white">
            Academic Performance & Retention Engine
        </footer>
    </body>
    </html>
    """

@app.route("/upload", methods=["POST"])
def upload_file():
    global LIVE_DF
    file = request.files['file']
    if file:
        LIVE_DF = pd.read_csv(file, dtype={'Parent_Phone': str})
    return redirect(url_for('dashboard', mode='live'))


# ====================================
# ROUTE 6: MAIN DASHBOARD (2 Columns per Row)
# ====================================
@app.route("/dashboard/<mode>")
@app.route("/demo", defaults={'mode': 'demo'})
def dashboard(mode):
    global LIVE_DF
    if mode == 'demo':
        df = pd.read_csv(io.StringIO(DEMO_CSV_DATA), dtype={'Parent_Phone': str})
    else:
        if LIVE_DF is not None:
            df = LIVE_DF.copy()
        else:
            df = pd.read_csv(io.StringIO(DEMO_CSV_DATA), dtype={'Parent_Phone': str})

    original_df = df.copy()
    search = request.args.get("search")
    if search:
        df = df[df["Name"].str.contains(search, case=False, na=False)]

    total_students = len(df)
    high = sum(1 for _, s in df.iterrows() if calculate_risk(s) == "High")
    moderate = sum(1 for _, s in df.iterrows() if calculate_risk(s) == "Moderate")
    low = sum(1 for _, s in df.iterrows() if calculate_risk(s) == "Low")

    high_pct = round((high / total_students) * 100) if total_students > 0 else 0
    mod_pct = round((moderate / total_students) * 100) if total_students > 0 else 0
    low_pct = round((low / total_students) * 100) if total_students > 0 else 0

    avg_attendance = round(df["Attendance"].mean()) if total_students > 0 else 0
    avg_participation = round(df["Participation"].mean()) if total_students > 0 else 0
    avg_mood = round(df["Mood"].mean(), 1) if total_students > 0 else 0

    html = f"""
    <html>
    <head>
        <title>Dashboard - Student Pulse</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-stone-100 text-stone-900 font-sans antialiased min-h-screen">
    
    <!-- Top Nav -->
    <header class="bg-white border-b border-stone-200 px-8 py-3.5 flex justify-between items-center sticky top-0 z-50 shadow-xs">
        <div class="flex items-center gap-3">
            <span class="font-bold text-sm tracking-tight text-stone-900">STUDENT PULSE</span>
            <span class="text-[10px] px-2 py-0.5 rounded font-medium uppercase bg-stone-100 text-stone-600 border border-stone-200">Mode: {mode}</span>
        </div>
        <div>
            <a href="/" class="text-xs font-medium text-stone-600 hover:text-stone-900 transition">Exit Session</a>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-8 py-8">
        <!-- Overview Metrics -->
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
            <div class="bg-white p-4 rounded-lg border border-stone-200 shadow-2xs">
                <p class="text-xs font-medium text-stone-500 uppercase tracking-wider">Total Enrolled</p>
                <p class="text-2xl font-bold text-stone-900 mt-1">{total_students}</p>
            </div>
            <div class="bg-white p-4 rounded-lg border border-stone-200 shadow-2xs">
                <p class="text-xs font-medium text-red-600 uppercase tracking-wider">High Risk</p>
                <p class="text-2xl font-bold text-red-600 mt-1">{high}</p>
            </div>
            <div class="bg-white p-4 rounded-lg border border-stone-200 shadow-2xs">
                <p class="text-xs font-medium text-amber-600 uppercase tracking-wider">Moderate Risk</p>
                <p class="text-2xl font-bold text-amber-600 mt-1">{moderate}</p>
            </div>
            <div class="bg-white p-4 rounded-lg border border-stone-200 shadow-2xs">
                <p class="text-xs font-medium text-emerald-600 uppercase tracking-wider">Low Risk / Stable</p>
                <p class="text-2xl font-bold text-emerald-600 mt-1">{low}</p>
            </div>
        </div>

        <!-- Analytics & Trend Analysis Section -->
        <div class="bg-white p-6 rounded-lg border border-stone-200 shadow-2xs mb-8">
            <h2 class="text-sm font-bold text-stone-900 mb-4 tracking-tight">Institutional Trend & Risk Distribution Analysis</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                <div>
                    <div class="flex justify-between text-xs font-medium text-stone-600 mb-1.5">
                        <span>Risk Stratification Ratio</span>
                        <span class="font-mono text-stone-900">{total_students} Total Records</span>
                    </div>
                    <div class="h-3 w-full bg-stone-100 rounded-full overflow-hidden flex border border-stone-200">
                        <div style="width: {high_pct}%" class="bg-red-500 h-full" title="High Risk: {high_pct}%"></div>
                        <div style="width: {mod_pct}%" class="bg-amber-500 h-full" title="Moderate Risk: {mod_pct}%"></div>
                        <div style="width: {low_pct}%" class="bg-emerald-500 h-full" title="Low Risk: {low_pct}%"></div>
                    </div>
                    <div class="flex gap-4 mt-2 text-[11px] text-stone-500 font-mono">
                        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-500"></span> High ({high_pct}%)</span>
                        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-amber-500"></span> Moderate ({mod_pct}%)</span>
                        <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> Stable ({low_pct}%)</span>
                    </div>
                </div>

                <div class="grid grid-cols-3 gap-3 border-t md:border-t-0 md:border-l border-stone-200 pt-4 md:pt-0 md:pl-6">
                    <div class="bg-stone-50 p-3 rounded border border-stone-200">
                        <span class="block text-[10px] uppercase font-semibold text-stone-400">Avg Attendance</span>
                        <span class="text-lg font-bold font-mono text-stone-800">{avg_attendance}%</span>
                    </div>
                    <div class="bg-stone-50 p-3 rounded border border-stone-200">
                        <span class="block text-[10px] uppercase font-semibold text-stone-400">Avg Participation</span>
                        <span class="text-lg font-bold font-mono text-stone-800">{avg_participation}%</span>
                    </div>
                    <div class="bg-stone-50 p-3 rounded border border-stone-200">
                        <span class="block text-[10px] uppercase font-semibold text-stone-400">Avg Mood Index</span>
                        <span class="text-lg font-bold font-mono text-stone-800">{avg_mood}/5</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search Filter -->
        <div class="mb-6">
            <form method="GET" class="flex gap-2 max-w-sm">
                <input type="text" name="search" placeholder="Search by student name..." class="px-3 py-2 text-xs rounded border border-stone-300 bg-white text-stone-900 w-full focus:outline-none focus:ring-1 focus:ring-stone-900">
                <button type="submit" class="px-4 py-2 bg-stone-900 hover:bg-stone-800 text-white text-xs font-medium rounded transition">Filter</button>
            </form>
        </div>

        <!-- Grid of Student Cards (2 Columns per Row) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    """

    for i, (_, row) in enumerate(df.iterrows()):
        risk = calculate_risk(row)
        root_cause = generate_root_cause_analysis(row)
        engagement_score = calculate_engagement(row)
        action_plan = generate_teacher_action_plan(row)
        parent_msg = generate_parent_message(row)
        weekly_tracker = generate_weekly_tracker(row)
        match = find_best_match(row, original_df)

        phone = str(row.get('Parent_Phone', '918910563292'))
        encoded_message = parent_msg.replace('\n', '%0A').replace(' ', '%20')

        risk_badge = "bg-emerald-50 text-emerald-700 border-emerald-200"
        if risk == "High":
            risk_badge = "bg-red-50 text-red-700 border-red-200"
        elif risk == "Moderate":
            risk_badge = "bg-amber-50 text-amber-700 border-amber-200"

        html += f"""
        <div class="bg-white p-6 rounded-lg border border-stone-200 shadow-2xs flex flex-col justify-between">
            <div>
                <div class="flex justify-between items-center mb-3">
                    <h2 class="text-base font-bold text-stone-900">{row['Name']}</h2>
                    <span class="px-2.5 py-0.5 rounded text-[10px] font-semibold border {risk_badge}">{risk} Risk</span>
                </div>
                
                <div class="space-y-1.5 text-xs text-stone-600 mb-5 font-mono">
                    <div class="flex justify-between border-b border-stone-100 pb-1"><span>Attendance:</span> <span class="text-stone-900 font-medium">{row['Attendance']}%</span></div>
                    <div class="flex justify-between border-b border-stone-100 pb-1"><span>Participation:</span> <span class="text-stone-900 font-medium">{row['Participation']}%</span></div>
                    <div class="flex justify-between border-b border-stone-100 pb-1"><span>Activities:</span> <span class="text-stone-900 font-medium">{row['Activities']}%</span></div>
                    <div class="flex justify-between border-b border-stone-100 pb-1"><span>Interaction:</span> <span class="text-stone-900 font-medium">{row['Interaction']}%</span></div>
                    <div class="flex justify-between border-b border-stone-100 pb-1"><span>Mood Index:</span> <span class="text-stone-900 font-medium">{row['Mood']}/5</span></div>
                    <div class="flex justify-between pt-1 font-semibold text-stone-900"><span>Engagement Score:</span> <span class="text-blue-600">{engagement_score}/100</span></div>
                </div>
        """

        if match:
            html += f"""
                <div class="text-[11px] text-stone-600 mb-4 bg-stone-50 p-2.5 rounded border border-stone-200 font-mono">
                    Suggested Peer Buddy: <span class="text-stone-900 font-medium">{match['name']}</span> ({match['score']}%)
                </div>
            """

        html += f"""
                <div class="mb-4 p-3 rounded border text-xs {weekly_tracker['border']}">
                    <span class="block font-semibold">Monitoring Schedule</span>
                    <span class="text-[11px] opacity-90">{weekly_tracker['status']} — {weekly_tracker['frequency']}</span>
                </div>
            </div>

            <div class="space-y-2 pt-3 border-t border-stone-100">
                <button class="w-full py-2.5 px-3 bg-stone-100 hover:bg-stone-200 text-stone-800 font-medium rounded text-xs transition cursor-pointer border border-stone-300" onclick="toggleSection('analysis{i}')">
                    Toggle Root Cause Diagnostics
                </button>
                <div id="analysis{i}" class="hidden p-3 bg-stone-50 border border-stone-200 rounded text-xs text-stone-700 space-y-2">
                    <p class="font-semibold text-stone-900">Diagnostic Summary:</p>
                    <p class="italic leading-relaxed text-[11px]">{root_cause}</p>
                    <p class="font-semibold text-stone-900 mt-2">Action Plan:</p>
                    <ul class="list-disc pl-4 space-y-1 text-[11px]">
        """
        for action in action_plan:
            html += f"<li>{action}</li>"

        html += f"""
                    </ul>
                </div>

                <a href="https://wa.me/{phone}?text={encoded_message}" target="_blank" class="flex items-center justify-center gap-2 w-full py-2.5 px-3 bg-emerald-700 hover:bg-emerald-800 text-white font-medium rounded text-xs transition shadow-2xs">
                    <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.096 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>
                    Dispatch Parent Notification via WhatsApp
                </a>
            </div>
        </div>
        """

    html += """
        </div>
    </main>

    <script>
    function toggleSection(id){
        var x = document.getElementById(id);
        if (x) {
            if(x.classList.contains('hidden')){ x.classList.remove('hidden'); }
            else { x.classList.add('hidden'); }
        }
    }
    </script>
    </body>
    </html>
    """
    return html


# ====================================
# CLOUD RUN BLOCK (Step 2 Integration)
# ====================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)