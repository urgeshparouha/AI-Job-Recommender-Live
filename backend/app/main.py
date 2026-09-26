from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
import io
import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="AI Job Recommender API",
    description="AI-powered resume analysis and intelligent job recommendation system",
    version="3.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MYSQL DATABASE
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv(
            "DB_NAME",
            "ai_job_recommender"
        ),
        ssl_disabled=False
    )


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def home():

    return {
        "message": "AI Job Recommender Backend is Running!",
        "version": "3.0.0"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================================================
# DATABASE TEST
# =========================================================

@app.get("/db-test")
def db_test():

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        cursor.close()
        db.close()

        return {
            "success": True,
            "database": result[0]
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================================================
# DOMAIN SKILLS
# =========================================================

DOMAIN_SKILLS = {

    "Software Development": [
        "python", "java", "c++", "c", "c#", "javascript",
        "typescript", "go", "rust", "kotlin", "swift",
        "oop", "oops", "dsa", "algorithms", "data structures",
        "dbms", "operating systems", "computer networks",
        "git", "github", "rest api", "api"
    ],

    "Backend Development": [
        "python", "java", "node.js", "nodejs", "fastapi",
        "django", "flask", "spring", "spring boot", "express",
        "rest api", "api", "sql", "mysql", "postgresql",
        "mongodb", "redis", "docker", "git", "github"
    ],

    "Frontend Development": [
        "html", "css", "javascript", "typescript", "react",
        "angular", "vue", "next.js", "bootstrap", "tailwind",
        "redux", "responsive design"
    ],

    "Data Science": [
        "python", "sql", "pandas", "numpy", "matplotlib",
        "seaborn", "scikit-learn", "statistics", "data science",
        "data analysis", "data visualization", "jupyter"
    ],

    "AI / Machine Learning": [
        "python", "machine learning", "deep learning",
        "artificial intelligence", "scikit-learn", "tensorflow",
        "pytorch", "keras", "nlp", "natural language processing",
        "computer vision", "opencv", "transformers", "llm",
        "generative ai"
    ],

    "Data Analytics": [
        "python", "sql", "excel", "power bi", "tableau",
        "pandas", "numpy", "statistics", "data analysis",
        "data visualization"
    ],

    "Cloud / DevOps": [
        "aws", "azure", "gcp", "google cloud", "docker",
        "kubernetes", "linux", "jenkins", "ci/cd",
        "terraform", "ansible", "git", "github"
    ],

    "Cybersecurity": [
        "cybersecurity", "network security", "ethical hacking",
        "penetration testing", "cryptography", "linux",
        "computer networks", "owasp", "firewall", "siem"
    ],

    "Database": [
        "sql", "mysql", "postgresql", "mongodb", "oracle",
        "redis", "dbms", "database design", "normalization"
    ]
}


# =========================================================
# COMBINED SKILLS
# =========================================================

SKILLS = sorted(
    set(
        skill
        for skills in DOMAIN_SKILLS.values()
        for skill in skills
    ),
    key=lambda x: (-len(x), x)
)


# =========================================================
# SKILL ALIASES
# =========================================================

SKILL_ALIASES = {

    "object oriented programming": "oop",
    "object-oriented programming": "oop",
    "object oriented": "oop",

    "data structures and algorithms": "dsa",

    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "artificial-intelligence": "artificial intelligence",

    "powerbi": "power bi",
    "scikit learn": "scikit-learn",
    "node js": "nodejs",
    "springboot": "spring boot",
    "computer networking": "computer networks"
}


# =========================================================
# SKILL DETECTION
# =========================================================

def detect_skills(text):

    text = text.lower()
    detected = set()

    for alias, actual_skill in SKILL_ALIASES.items():

        if alias in text:
            detected.add(actual_skill)

    for skill in SKILLS:

        skill_lower = skill.lower()

        if len(skill_lower) <= 2:

            pattern = r"\b" + re.escape(skill_lower) + r"\b"

            if re.search(pattern, text):
                detected.add(skill)

        else:

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(skill_lower)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, text):
                detected.add(skill)

    return sorted(detected)


# =========================================================
# DOMAIN DETECTION
# =========================================================

def detect_domains(text, detected_skills):

    detected_set = set(detected_skills)
    domains = []

    for domain, domain_skills in DOMAIN_SKILLS.items():

        matched = sorted(
            detected_set.intersection(
                set(domain_skills)
            )
        )

        if matched:

            domains.append({
                "domain": domain,
                "matched_skills": matched,
                "skill_count": len(matched)
            })

    domains.sort(
        key=lambda x: x["skill_count"],
        reverse=True
    )

    return domains


# =========================================================
# RESUME SCORE
# =========================================================

def calculate_resume_score(text, detected_skills):

    score = 0

    skill_score = min(
        len(detected_skills) * 5,
        50
    )

    score += skill_score

    experience_keywords = [
        "project",
        "projects",
        "internship",
        "experience",
        "developer",
        "engineer"
    ]

    for keyword in experience_keywords:

        if keyword in text.lower():
            score += 10

    education_keywords = [
        "btech",
        "b.tech",
        "computer science",
        "engineering",
        "bachelor"
    ]

    for keyword in education_keywords:

        if keyword in text.lower():
            score += 5

    return min(score, 100)


# =========================================================
# RESUME TEXT EXTRACTION
# =========================================================

def extract_resume_text(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".pdf"):

        reader = PdfReader(
            io.BytesIO(file_bytes)
        )

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    elif filename.endswith(".docx"):

        document = Document(
            io.BytesIO(file_bytes)
        )

        text = ""

        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

        return text

    else:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )


# =========================================================
# UPLOAD RESUME
# =========================================================

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...)
):

    try:

        file_bytes = await file.read()

        text = extract_resume_text(
            file_bytes,
            file.filename
        )

        detected_skills = detect_skills(text)

        resume_score = calculate_resume_score(
            text,
            detected_skills
        )

        detected_domains = detect_domains(
            text,
            detected_skills
        )

        return {
            "success": True,
            "filename": file.filename,
            "detected_skills": detected_skills,
            "skill_count": len(detected_skills),
            "resume_score": resume_score,
            "detected_domains": detected_domains,
            "message": "Resume analyzed successfully"
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# GET JOBS FROM MYSQL
# =========================================================

def get_jobs_from_database():

    db = get_db_connection()

    cursor = db.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            id,
            job_title,
            company,
            location,
            experience,
            required_skills,
            apply_url
        FROM jobs
        """
    )

    jobs = cursor.fetchall()

    cursor.close()
    db.close()

    return jobs


# =========================================================
# GET ALL JOBS
# =========================================================

@app.get("/jobs")
def get_jobs():

    try:

        jobs = get_jobs_from_database()

        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# LEARNING MAP
# =========================================================

LEARNING_MAP = {

    "python":
        "Learn Python fundamentals, functions, OOP and problem solving.",

    "java":
        "Learn Java fundamentals, OOP, collections and exception handling.",

    "c++":
        "Learn C++ fundamentals, STL, OOP and problem solving.",

    "javascript":
        "Learn JavaScript fundamentals, DOM, events and modern ES6.",

    "typescript":
        "Learn TypeScript types, interfaces, classes and modern JavaScript.",

    "html":
        "Learn HTML structure, forms, semantic tags and accessibility.",

    "css":
        "Learn CSS layouts, Flexbox, Grid, responsive design and animations.",

    "react":
        "Learn React components, props, state, hooks and API integration.",

    "angular":
        "Learn Angular components, services, routing and forms.",

    "vue":
        "Learn Vue components, directives, state and routing.",

    "node.js":
        "Learn Node.js, Express, REST APIs and backend development.",

    "nodejs":
        "Learn Node.js, Express, REST APIs and backend development.",

    "fastapi":
        "Learn FastAPI routes, APIs, request handling and database integration.",

    "django":
        "Learn Django models, views, URLs, templates and REST APIs.",

    "flask":
        "Learn Flask routes, APIs, templates and database integration.",

    "sql":
        "Learn SQL queries, joins, subqueries, GROUP BY and database concepts.",

    "mysql":
        "Learn MySQL databases, tables, queries, joins and relationships.",

    "postgresql":
        "Learn PostgreSQL queries, indexing, relationships and database design.",

    "mongodb":
        "Learn MongoDB collections, documents, queries and aggregation.",

    "dsa":
        "Learn arrays, strings, linked lists, stacks, queues, trees and graphs.",

    "algorithms":
        "Learn searching, sorting, recursion, greedy algorithms and dynamic programming.",

    "data structures":
        "Learn arrays, linked lists, stacks, queues, trees, graphs and hash tables.",

    "oops":
        "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "oop":
        "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "dbms":
        "Learn normalization, keys, transactions, indexing and SQL.",

    "operating systems":
        "Learn processes, threads, memory management, scheduling and file systems.",

    "computer networks":
        "Learn OSI, TCP/IP, HTTP, DNS, routing and networking fundamentals.",

    "git":
        "Learn Git commands, GitHub repositories, branching and version control.",

    "github":
        "Learn repositories, branches, pull requests and collaborative GitHub workflows.",

    "pandas":
        "Learn DataFrame operations, filtering, grouping and data cleaning.",

    "numpy":
        "Learn arrays, mathematical operations and numerical computing.",

    "matplotlib":
        "Learn charts, plots and data visualization with Matplotlib.",

    "seaborn":
        "Learn statistical visualization and advanced charts with Seaborn.",

    "scikit-learn":
        "Learn preprocessing, machine learning models and model evaluation.",

    "machine learning":
        "Learn regression, classification, clustering and model evaluation.",

    "deep learning":
        "Learn neural networks, CNNs, training and deep learning fundamentals.",

    "artificial intelligence":
        "Learn AI fundamentals, machine learning, neural networks and intelligent systems.",

    "data science":
        "Learn Python, statistics, SQL, pandas, visualization and machine learning.",

    "data analysis":
        "Learn data cleaning, SQL, pandas, statistics and visualization.",

    "statistics":
        "Learn probability, distributions, hypothesis testing and statistical analysis.",

    "excel":
        "Learn formulas, pivot tables, charts, lookup functions and data analysis.",

    "power bi":
        "Learn dashboards, Power Query, data modeling and DAX.",

    "tableau":
        "Learn dashboards, charts, filters and data visualization.",

    "aws":
        "Learn AWS fundamentals, EC2, S3, IAM and cloud deployment.",

    "azure":
        "Learn Azure fundamentals, virtual machines, storage and cloud services.",

    "docker":
        "Learn Docker images, containers, Dockerfiles and deployment.",

    "kubernetes":
        "Learn pods, deployments, services and Kubernetes fundamentals.",

    "linux":
        "Learn Linux commands, file systems, permissions and process management.",

    "cybersecurity":
        "Learn security fundamentals, threats, vulnerabilities and defensive techniques.",

    "network security":
        "Learn network security fundamentals, firewalls and secure communication.",

    "ethical hacking":
        "Learn cybersecurity fundamentals, security testing concepts and defensive practices.",

    "penetration testing":
        "Learn security assessment methodology and penetration testing fundamentals.",

    "cryptography":
        "Learn encryption, hashing, keys and cryptographic fundamentals.",

    "owasp":
        "Learn common web security risks and secure application development."
}


# =========================================================
# LEARNING SUGGESTIONS
# =========================================================

def get_learning_suggestions(missing_skills):

    suggestions = []

    for skill in missing_skills:

        skill_lower = skill.lower()

        if skill_lower in LEARNING_MAP:

            suggestions.append({
                "skill": skill,
                "suggestion": LEARNING_MAP[skill_lower]
            })

        else:

            suggestions.append({
                "skill": skill,
                "suggestion":
                    f"Learn {skill} and practice it through projects."
            })

    return suggestions


# =========================================================
# JOB DOMAIN DETECTION
# =========================================================

def detect_job_domains(required_skills):

    required_set = set(
        skill.lower().strip()
        for skill in required_skills
    )

    domains = []

    for domain, skills in DOMAIN_SKILLS.items():

        overlap = required_set.intersection(
            set(skills)
        )

        if overlap:
            domains.append(domain)

    return domains


# =========================================================
# INTELLIGENT JOB MATCHING
# =========================================================

def calculate_intelligent_match(
    detected_skills,
    required_skills
):

    detected = set(
        skill.lower().strip()
        for skill in detected_skills
    )

    required = set(
        skill.lower().strip()
        for skill in required_skills
    )

    if not required:

        return {
            "match_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "skill_score": 0,
            "core_skill_score": 0,
            "domain_score": 0
        }

    matched = sorted(
        detected.intersection(required)
    )

    missing = sorted(
        required - detected
    )

    skill_score = (
        len(matched) /
        len(required)
    ) * 100

    core_skills = {
        "python",
        "java",
        "c++",
        "javascript",
        "typescript",
        "sql",
        "machine learning",
        "artificial intelligence",
        "react",
        "fastapi",
        "django",
        "aws",
        "docker"
    }

    core_required = required.intersection(
        core_skills
    )

    if core_required:

        core_matched = detected.intersection(
            core_required
        )

        core_skill_score = (
            len(core_matched) /
            len(core_required)
        ) * 100

    else:

        core_skill_score = skill_score

    detected_domains = []

    for domain, domain_skills in DOMAIN_SKILLS.items():

        overlap = detected.intersection(
            set(domain_skills)
        )

        if overlap:
            detected_domains.append(domain)

    job_domains = detect_job_domains(
        required_skills
    )

    if job_domains:

        matching_domains = set(
            detected_domains
        ).intersection(
            set(job_domains)
        )

        domain_score = (
            len(matching_domains) /
            len(job_domains)
        ) * 100

    else:

        domain_score = 0

    final_score = (
        skill_score * 0.70
        +
        core_skill_score * 0.20
        +
        domain_score * 0.10
    )

    final_score = round(
        min(final_score, 100)
    )

    return {

        "match_percentage":
            final_score,

        "matched_skills":
            matched,

        "missing_skills":
            missing,

        "skill_score":
            round(skill_score),

        "core_skill_score":
            round(core_skill_score),

        "domain_score":
            round(domain_score)
    }


# =========================================================
# MATCH JOBS
# =========================================================

@app.post("/match-jobs")
async def match_jobs(
    file: UploadFile = File(...)
):

    try:

        file_bytes = await file.read()

        text = extract_resume_text(
            file_bytes,
            file.filename
        )

        detected_skills = detect_skills(
            text
        )

        resume_score = calculate_resume_score(
            text,
            detected_skills
        )

        detected_domains = detect_domains(
            text,
            detected_skills
        )

        jobs = get_jobs_from_database()

        matched_jobs = []

        for job in jobs:

            required_skills = [
                skill.strip().lower()
                for skill in job["required_skills"].split(",")
                if skill.strip()
            ]

            match_result = calculate_intelligent_match(
                detected_skills,
                required_skills
            )

            missing_skills = match_result[
                "missing_skills"
            ]

            job_domains = detect_job_domains(
                required_skills
            )

            matched_jobs.append({

                "job_id":
                    job["id"],

                "job_title":
                    job["job_title"],

                "company":
                    job["company"],

                "location":
                    job["location"],

                "experience":
                    job["experience"],

                "job_domains":
                    job_domains,

                "required_skills":
                    required_skills,

                "matched_skills":
                    match_result[
                        "matched_skills"
                    ],

                "missing_skills":
                    missing_skills,

                "match_percentage":
                    match_result[
                        "match_percentage"
                    ],

                "match_breakdown": {

                    "skill_score":
                        match_result[
                            "skill_score"
                        ],

                    "core_skill_score":
                        match_result[
                            "core_skill_score"
                        ],

                    "domain_score":
                        match_result[
                            "domain_score"
                        ]
                },

                "apply_url":
                    job["apply_url"],

                "what_to_learn":
                    get_learning_suggestions(
                        missing_skills
                    )
            })

        matched_jobs.sort(
            key=lambda x:
                x["match_percentage"],
            reverse=True
        )

        return {

            "success":
                True,

            "filename":
                file.filename,

            "resume_score":
                resume_score,

            "detected_skills":
                detected_skills,

            "skill_count":
                len(detected_skills),

            "detected_domains":
                detected_domains,

            "total_jobs_checked":
                len(jobs),

            "recommendations":
                matched_jobs
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )