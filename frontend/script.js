const API_URL = "https://ai-job-recommender-live-production.up.railway.app";

const resumeFile = document.getElementById("resumeFile");
const selectedFile = document.getElementById("selectedFile");
const analyzeBtn = document.getElementById("analyzeBtn");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");

const results = document.getElementById("results");

const resumeScore = document.getElementById("resumeScore");
const skillCount = document.getElementById("skillCount");
const jobCount = document.getElementById("jobCount");

const skillsContainer = document.getElementById("skillsContainer");
const jobsList = document.getElementById("jobsList");


// =============================
// FILE SELECT
// =============================

resumeFile.addEventListener("change", function () {

    if (resumeFile.files.length > 0) {

        selectedFile.textContent =
            "Selected: " + resumeFile.files[0].name;

    } else {

        selectedFile.textContent =
            "No file selected";

    }

});


// =============================
// ANALYZE RESUME
// =============================

analyzeBtn.addEventListener("click", async function () {

    errorMessage.classList.add("hidden");
    loading.classList.add("hidden");

    if (resumeFile.files.length === 0) {

        errorMessage.textContent =
            "Please select your resume first.";

        errorMessage.classList.remove("hidden");

        return;
    }

    const file = resumeFile.files[0];

    const formData = new FormData();

    formData.append("file", file);

    analyzeBtn.disabled = true;

    loading.textContent =
        "Analyzing your resume...";

    loading.classList.remove("hidden");

    try {

        const response = await fetch(
            `${API_URL}/match-jobs`,
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {

            throw new Error(
                "Server returned error: " + response.status
            );

        }

        const data = await response.json();

        if (!data.success) {

            throw new Error(
                "Resume analysis failed."
            );

        }

        displayResults(data);

    } catch (error) {

        console.error(error);

        errorMessage.textContent =
            "Backend se connection nahi ho pa raha. Make sure FastAPI server is running.";

        errorMessage.classList.remove("hidden");

    } finally {

        analyzeBtn.disabled = false;

        loading.classList.add("hidden");

    }

});


// =============================
// DISPLAY RESULTS
// =============================

function displayResults(data) {

    results.classList.remove("hidden");

    // Resume score
    resumeScore.textContent =
        data.resume_score + "/100";

    // Skill count
    skillCount.textContent =
        data.detected_skills.length;

    // Job count
    jobCount.textContent =
        data.total_jobs_checked;


    // =============================
    // DETECTED SKILLS
    // =============================

    skillsContainer.innerHTML = "";

    data.detected_skills.forEach(function (skill) {

        const skillElement =
            document.createElement("span");

        skillElement.className =
            "skill-tag";

        skillElement.textContent =
            formatSkillName(skill);

        skillsContainer.appendChild(
            skillElement
        );

    });


    // =============================
    // JOBS
    // =============================

    jobsList.innerHTML = "";

    data.recommendations.forEach(function (job) {

        const jobCard =
            document.createElement("div");

        jobCard.className =
            "job-card";


        // =============================
        // MATCHED SKILLS
        // =============================

        let matchedSkillsHTML = "";

        job.matched_skills.forEach(function (skill) {

            matchedSkillsHTML += `
                <span class="job-skill matched">
                    ${escapeHTML(formatSkillName(skill))}
                </span>
            `;

        });


        // =============================
        // MISSING SKILLS
        // =============================

        let missingSkillsHTML = "";

        job.missing_skills.forEach(function (skill) {

            missingSkillsHTML += `
                <span class="job-skill missing">
                    ${escapeHTML(formatSkillName(skill))}
                </span>
            `;

        });


        // =============================
        // LEARNING SUGGESTIONS
        // =============================

        let learningHTML = "";

        if (job.what_to_learn.length > 0) {

            learningHTML = `
                <div class="learn-box">

                    <h4>
                        What to Learn
                    </h4>

                    ${job.what_to_learn.map(function (item) {

                        return `
                            <p>
                                <strong>
                                    ${escapeHTML(
                                        formatSkillName(item.skill)
                                    )}
                                </strong>
                                — ${escapeHTML(item.suggestion)}
                            </p>
                        `;

                    }).join("")}

                </div>
            `;

        }


        // =============================
        // JOB CARD HTML
        // =============================

        jobCard.innerHTML = `

            <div class="job-header">

                <div>

                    <h3 class="job-title">
                        ${escapeHTML(job.job_title)}
                    </h3>

                    <p class="company">
                        ${escapeHTML(job.company)}
                    </p>

                    <p class="job-info">
                        📍 ${escapeHTML(job.location)}
                        &nbsp; • &nbsp;
                        ${escapeHTML(job.experience)}
                    </p>

                </div>

                <div class="match-badge">
                    ${job.match_percentage}% Match
                </div>

            </div>


            <div class="job-section">

                <h4>
                    Matched Skills
                </h4>

                <div class="job-skills">

                    ${
                        matchedSkillsHTML ||
                        "<span>No matching skills</span>"
                    }

                </div>

            </div>


            <div class="job-section">

                <h4>
                    Missing Skills
                </h4>

                <div class="job-skills">

                    ${
                        missingSkillsHTML ||
                        "<span>No missing skills 🎉</span>"
                    }

                </div>

            </div>


            ${learningHTML}


            <a
                href="${escapeHTML(job.apply_url)}"
                target="_blank"
                rel="noopener noreferrer"
                class="apply-btn"
            >
                Apply for Job →
            </a>

        `;

        jobsList.appendChild(jobCard);

    });


    // Scroll to results

    results.scrollIntoView({
        behavior: "smooth"
    });

}


// =============================
// FORMAT SKILL NAME
// =============================

function formatSkillName(skill) {

    const skillNames = {

        "python": "Python",
        "c++": "C++",
        "java": "Java",
        "javascript": "JavaScript",
        "html": "HTML",
        "css": "CSS",
        "react": "React",

        "sql": "SQL",
        "mysql": "MySQL",

        "git": "Git",
        "github": "GitHub",

        "dsa": "DSA",
        "algorithms": "Algorithms",
        "data structures": "Data Structures",

        "oops": "OOPS",
        "oop": "OOP",
        "dbms": "DBMS",
        "operating systems": "Operating Systems",
        "computer networks": "Computer Networks",

        "pandas": "Pandas",
        "numpy": "NumPy",
        "matplotlib": "Matplotlib",

        "machine learning": "Machine Learning",
        "scikit-learn": "Scikit-Learn",
        "deep learning": "Deep Learning",

        "artificial intelligence": "Artificial Intelligence",
        "data science": "Data Science",

        "excel": "Excel",
        "power bi": "Power BI",
        "tableau": "Tableau",

        "fastapi": "FastAPI",
        "aws": "AWS",
        "azure": "Azure",
        "docker": "Docker"

    };

    const key = String(skill).toLowerCase().trim();

    return skillNames[key] || skill;

}


// =============================
// SECURITY HELPER
// =============================

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}