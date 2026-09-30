from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
import io
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Job Recommender API",
    description="AI-powered resume analysis and job recommendation system",
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
# MYSQL DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "ai_job_recommender")
    )


# =========================================================
# BASIC ROUTES
# =========================================================

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
# SKILLS LIST
# =========================================================

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


# =========================================================
# SKILL DETECTION
# =========================================================

def detect_skills(text):

    text = text.lower()

    detected = []

    for skill in SKILLS:

        if skill.lower() in text:

            detected.append(skill)

    return detected


# =========================================================
# REALISTIC RESUME SCORE
# =========================================================
#
# TOTAL = 100
#
# Skills                 = 35
# Projects               = 20
# Education              = 15
# Experience/Internship  = 15
# Resume Completeness    = 15
#
# =========================================================

def calculate_resume_score(text, detected_skills):

    text = text.lower()


    # =====================================================
    # 1. SKILLS SCORE - 35 MARKS
    # =====================================================

    skill_score = min(
        len(detected_skills) * 2.5,
        35
    )


    # =====================================================
    # 2. PROJECTS SCORE - 20 MARKS
    # =====================================================

    project_keywords = [

        "project",
        "projects",
        "github",
        "developed",
        "built",
        "implemented",
        "application",
        "system"

    ]

    project_hits = sum(

        1
        for keyword in project_keywords
        if keyword in text

    )

    project_score = min(
        project_hits * 2.5,
        20
    )


    # =====================================================
    # 3. EDUCATION SCORE - 15 MARKS
    # =====================================================

    education_keywords = [

        "btech",
        "b.tech",
        "bachelor",
        "computer science",
        "engineering",
        "university",
        "college",
        "degree"

    ]

    education_hits = sum(

        1
        for keyword in education_keywords
        if keyword in text

    )

    education_score = min(
        education_hits * 2,
        15
    )


    # =====================================================
    # 4. EXPERIENCE / INTERNSHIP - 15 MARKS
    # =====================================================

    experience_keywords = [

        "internship",
        "intern",
        "experience",
        "work experience",
        "employment",
        "developer",
        "engineer"

    ]

    experience_hits = sum(

        1
        for keyword in experience_keywords
        if keyword in text

    )

    experience_score = min(
        experience_hits * 2.5,
        15
    )


    # =====================================================
    # 5. RESUME COMPLETENESS - 15 MARKS
    # =====================================================

    completeness_sections = [

        "education",
        "skills",
        "projects",
        "contact",
        "email",
        "phone",
        "resume",
        "objective",
        "summary",
        "certification",
        "certifications"

    ]

    completeness_hits = sum(

        1
        for section in completeness_sections
        if section in text

    )

    completeness_score = min(
        completeness_hits * 1.5,
        15
    )


    # =====================================================
    # FINAL SCORE
    # =====================================================

    score = (

        skill_score
        + project_score
        + education_score
        + experience_score
        + completeness_score

    )

    return round(
        min(score, 100)
    )


# =========================================================
# RESUME TEXT EXTRACTION
# =========================================================

def extract_resume_text(file_bytes, filename):

    filename = filename.lower()


    # =====================================================
    # PDF
    # =====================================================

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


    # =====================================================
    # DOCX
    # =====================================================

    elif filename.endswith(".docx"):

        document = Document(
            io.BytesIO(file_bytes)
        )

        text = ""

        for paragraph in document.paragraphs:

            text += paragraph.text + "\n"

        return text


    # =====================================================
    # INVALID FILE
    # =====================================================

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


        detected_skills = detect_skills(
            text
        )


        resume_score = calculate_resume_score(
            text,
            detected_skills
        )


        return {

            "filename": file.filename,

            "detected_skills": detected_skills,

            "skill_count": len(
                detected_skills
            ),

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


# =========================================================
# GET JOBS FROM MYSQL
# =========================================================

def get_jobs_from_database():

    db = get_db_connection()

    cursor = db.cursor(
        dictionary=True
    )


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

    "sql":
        "Learn SQL queries, joins, subqueries, group by and database concepts.",

    "dsa":
        "Learn arrays, strings, linked lists, stacks, queues, trees and graphs.",

    "oops":
        "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "oop":
        "Learn classes, objects, inheritance, polymorphism and abstraction.",

    "dbms":
        "Learn normalization, keys, transactions, indexing and SQL.",

    "git":
        "Learn Git commands, GitHub repositories, branching and version control.",

    "fastapi":
        "Learn FastAPI routes, APIs, request handling and database integration.",

    "mysql":
        "Learn MySQL databases, tables, queries, joins and relationships.",

    "pandas":
        "Learn DataFrame operations, filtering, grouping and data cleaning.",

    "numpy":
        "Learn arrays, mathematical operations and numerical computing.",

    "machine learning":
        "Learn regression, classification, clustering and model evaluation.",

    "data science":
        "Learn Python, statistics, SQL, pandas, visualization and machine learning.",

    "javascript":
        "Learn JavaScript fundamentals, DOM, events and modern ES6.",

    "html":
        "Learn HTML structure, forms, semantic tags and accessibility.",

    "css":
        "Learn CSS layouts, Flexbox, Grid, responsive design and animations.",

    "react":
        "Learn React components, props, state, hooks and API integration."

}


# =========================================================
# LEARNING SUGGESTIONS
# =========================================================

def get_learning_suggestions(
    missing_skills
):

    suggestions = []


    for skill in missing_skills:

        skill_lower = skill.lower()


        if skill_lower in LEARNING_MAP:

            suggestions.append({

                "skill": skill,

                "suggestion":
                    LEARNING_MAP[skill_lower]

            })


        else:

            suggestions.append({

                "skill": skill,

                "suggestion":
                    f"Learn {skill} and practice it through projects."

            })


    return suggestions


# =========================================================
# JOB MATCHING
# =========================================================

@app.post("/match-jobs")
async def match_jobs(
    file: UploadFile = File(...)
):

    try:

        # =================================================
        # READ RESUME
        # =================================================

        file_bytes = await file.read()


        text = extract_resume_text(
            file_bytes,
            file.filename
        )


        # =================================================
        # DETECT SKILLS
        # =================================================

        detected_skills = detect_skills(
            text
        )


        # =================================================
        # CALCULATE REALISTIC RESUME SCORE
        # =================================================

        resume_score = calculate_resume_score(
            text,
            detected_skills
        )


        # =================================================
        # GET JOBS
        # =================================================

        jobs = get_jobs_from_database()


        matched_jobs = []


        # =================================================
        # MATCH EVERY JOB
        # =================================================

        for job in jobs:


            # ---------------------------------------------
            # REQUIRED SKILLS
            # ---------------------------------------------

            required_skills = [

                skill.strip().lower()

                for skill in
                job["required_skills"].split(",")

            ]


            # ---------------------------------------------
            # USER SKILLS
            # ---------------------------------------------

            user_skills = [

                skill.lower()

                for skill in detected_skills

            ]


            matched_skills = []

            missing_skills = []


            # ---------------------------------------------
            # COMPARE SKILLS
            # ---------------------------------------------

            for skill in required_skills:

                if skill in user_skills:

                    matched_skills.append(
                        skill
                    )

                else:

                    missing_skills.append(
                        skill
                    )


            # ---------------------------------------------
            # MATCH PERCENTAGE
            # ---------------------------------------------

            if len(required_skills) > 0:

                match_percentage = round(

                    (
                        len(matched_skills)
                        /
                        len(required_skills)
                    )
                    * 100

                )

            else:

                match_percentage = 0


            # ---------------------------------------------
            # ADD JOB
            # ---------------------------------------------

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

                "required_skills":
                    required_skills,

                "matched_skills":
                    matched_skills,

                "missing_skills":
                    missing_skills,

                "match_percentage":
                    match_percentage,

                "apply_url":
                    job["apply_url"],

                "what_to_learn":
                    get_learning_suggestions(
                        missing_skills
                    )

            })


        # =================================================
        # SORT BY MATCH
        # =================================================

        matched_jobs.sort(

            key=lambda x:
                x["match_percentage"],

            reverse=True

        )


        # =================================================
        # FINAL RESPONSE
        # =================================================

        return {

            "success": True,

            "filename":
                file.filename,

            "resume_score":
                resume_score,

            "detected_skills":
                detected_skills,

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