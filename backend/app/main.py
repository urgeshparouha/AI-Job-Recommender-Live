from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
import io
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(
    title="AI Job Recommender API",
    description="AI-powered resume analysis and job recommendation system",
    version="1.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# MYSQL DATABASE CONNECTION
# =========================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "ai_job_recommender")
    )


# =========================
# BASIC ROUTES
# =========================

@app.get("/")
def home():
    return {
        "message": "AI Job Recommender Backend is Running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================
# DATABASE TEST
# =========================

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


# =========================
# SKILLS LIST
# =========================

SKILLS = [
    "python",
    "java",
    "c++",
    "javascript",
    "html",
    "css",
    "react",
    "node.js",
    "fastapi",
    "django",
    "flask",

    "sql",
    "mysql",
    "postgresql",
    "mongodb",

    "git",
    "github",

    "dsa",
    "algorithms",
    "data structures",
    "oops",
    "oop",
    "dbms",
    "operating systems",
    "computer networks",

    "pandas",
    "numpy",
    "matplotlib",
    "scikit-learn",

    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",

    "excel",
    "power bi",
    "tableau",

    "aws",
    "azure",
    "docker"
]


# =========================
# SKILL DETECTION
# =========================

def detect_skills(text):

    text = text.lower()

    detected = []

    for skill in SKILLS:

        if skill.lower() in text:

            detected.append(skill)

    return detected


# =========================
# RESUME SCORE
# =========================

def calculate_resume_score(text, detected_skills):

    score = 0

    skill_score = min(len(detected_skills) * 5, 50)

    score += skill_score

    experience_keywords = [
        "project",
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


# =========================
# RESUME TEXT EXTRACTION
# =========================

def extract_resume_text(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".pdf"):

        reader = PdfReader(io.BytesIO(file_bytes))

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        return text


    elif filename.endswith(".docx"):

        document = Document(io.BytesIO(file_bytes))

        text = ""

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

        return text


    else:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )


# =========================
# UPLOAD RESUME
# =========================

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

        return {
            "filename": file.filename,
            "detected_skills": detected_skills,
            "skill_count": len(detected_skills),
            "resume_score": resume_score,
            "message": "Resume analyzed successfully"
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# GET JOBS FROM MYSQL
# =========================

def get_jobs_from_database():

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            job_title,
            company,
            location,
            experience,
            required_skills,
            apply_url
        FROM jobs
    """)

    jobs = cursor.fetchall()

    cursor.close()
    db.close()

    return jobs


# =========================
# GET ALL JOBS
# =========================

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


# =========================
# LEARNING MAP
# =========================

LEARNING_MAP = {

    "python": "Learn Python fundamentals, functions, OOP and problem solving.",

    "sql": "Learn SQL queries, joins, subqueries, group by and database concepts.",

    "dsa": "Learn arrays, strings, linked lists, stacks, queues, trees and graphs.",

    "oops": "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "oop": "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "dbms": "Learn normalization, keys, transactions, indexing and SQL.",

    "git": "Learn Git commands, GitHub repositories, branching and version control.",

    "fastapi": "Learn FastAPI routes, APIs, request handling and database integration.",

    "mysql": "Learn MySQL databases, tables, queries, joins and relationships.",

    "pandas": "Learn DataFrame operations, filtering, grouping and data cleaning.",

    "numpy": "Learn arrays, mathematical operations and numerical computing.",

    "machine learning": "Learn regression, classification, clustering and model evaluation.",

    "data science": "Learn Python, statistics, SQL, pandas, visualization and machine learning.",

    "javascript": "Learn JavaScript fundamentals, DOM, events and modern ES6.",

    "html": "Learn HTML structure, forms, semantic tags and accessibility.",

    "css": "Learn CSS layouts, Flexbox, Grid, responsive design and animations.",

    "react": "Learn React components, props, state, hooks and API integration."

}


# =========================
# LEARNING SUGGESTIONS
# =========================

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
                "suggestion": f"Learn {skill} and practice it through projects."
            })

    return suggestions


# =========================
# JOB MATCHING
# =========================

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

        detected_skills = detect_skills(text)

        resume_score = calculate_resume_score(
            text,
            detected_skills
        )

        jobs = get_jobs_from_database()

        matched_jobs = []

        for job in jobs:

            required_skills = [
                skill.strip().lower()
                for skill in job["required_skills"].split(",")
            ]

            user_skills = [
                skill.lower()
                for skill in detected_skills
            ]

            matched_skills = []

            missing_skills = []

            for skill in required_skills:

                if skill in user_skills:

                    matched_skills.append(skill)

                else:

                    missing_skills.append(skill)

            if len(required_skills) > 0:

                match_percentage = round(
                    (len(matched_skills) / len(required_skills)) * 100
                )

            else:

                match_percentage = 0

            matched_jobs.append({

                "job_id": job["id"],

                "job_title": job["job_title"],

                "company": job["company"],

                "location": job["location"],

                "experience": job["experience"],

                "required_skills": required_skills,

                "matched_skills": matched_skills,

                "missing_skills": missing_skills,

                "match_percentage": match_percentage,

                "apply_url": job["apply_url"],

                "what_to_learn": get_learning_suggestions(
                    missing_skills
                )

            })


        matched_jobs.sort(
            key=lambda x: x["match_percentage"],
            reverse=True
        )


        return {

            "success": True,

            "filename": file.filename,

            "resume_score": resume_score,

            "detected_skills": detected_skills,

            "total_jobs_checked": len(jobs),

            "recommendations": matched_jobs

        }


    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )