import streamlit as st
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import spacy
import subprocess
import sys
from pathlib import Path
from keybert import KeyBERT
import re

# Optional for DOCX support
try:
    import docx2txt
except ImportError:
    docx2txt = None

st.set_page_config(page_title="AI Career Compass", layout="wide")
st.title("\U0001F680 AI Career Compass")
st.markdown("Matching job listings to your resume using local AI.")

# Load spaCy NLP model (cached at startup)
@st.cache_resource
def load_nlp_model():
    return spacy.load("en_core_web_sm")

nlp = load_nlp_model()

def flatten_keywords(phrases):
    words = set()
    for phrase in phrases:
        for word in phrase.lower().split():
            words.add(word.strip())
    return sorted(words)




def is_valid_phrase(kw: str) -> bool:
    kw = kw.strip().lower()

    # Ignore empty or purely numeric
    if not kw or kw.isnumeric():
        return False

    # Ignore phrases with only stopwords or filler terms
    WEAK_WORDS = {"skills", "experience", "expertise", "proficient", "ability", "various", "strong", "knowledge", "understanding", "working", "role", "team"}
    tokens = kw.split()
    if all(tok in WEAK_WORDS for tok in tokens):
        return False

    # Too short (e.g., "bi", "ai", unless useful — tweak min length as needed)
    if len(kw) < 3:
        return False

    # Ignore phrases with weak structure like "adjective noun"
    # e.g., "proficient sql", "strong cloud"
    if len(tokens) == 2 and re.match(r"^(proficient|strong|expertise|solid)$", tokens[0]):
        return False

    # Optional: Keep only noun-based phrases (could plug in spaCy here)

    return True


@st.cache_resource
def load_keybert_model():
    return KeyBERT("all-MiniLM-L6-v2")

kw_model = load_keybert_model()

@st.cache_resource
def load_sentence_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

STOPWORDS = {
    "various", "several", "role", "team", "position", "skills", "work",
    "ability", "knowledge", "experience", "others", "requirements"
}


def extract_skills(text):
    raw_keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=15,
    )
    seen = set()
    cleaned = set()

    for kw, _ in raw_keywords:
        kw_clean = kw.lower().strip()
        if kw_clean in STOPWORDS:
            continue
        if not any(kw_clean in s or s in kw_clean for s in seen):
            cleaned.add(kw_clean)
            seen.add(kw_clean)

    return cleaned

def extract_resume_keywords(text, top_n=20):
    raw_keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        top_n=top_n,
    )

    seen = set()
    cleaned = []

    for kw, _ in raw_keywords:
        kw_clean = kw.lower().strip()

        if not is_valid_phrase(kw_clean):
            continue

        # Deduplicate loosely
        if not any(kw_clean in s or s in kw_clean for s in seen):
            cleaned.append(kw_clean)
            seen.add(kw_clean)

    return cleaned


def build_cover_letter(job, resume_keywords, matched_skills, missing_skills):
    company = job.get("company", "the company")
    title = job.get("title", "this role")
    location = job.get("location", "your location")
    top_keywords = ", ".join(list(resume_keywords)[:6]) if resume_keywords else "relevant experience"
    matched = ", ".join(matched_skills[:6]) if matched_skills else "key requirements"
    missing = ", ".join(missing_skills[:4]) if missing_skills else "no major gaps"
    return (
        f"Dear Hiring Manager,\n\n"
        f"I am writing to apply for the {title} position at {company} in {location}. "
        f"My background includes {top_keywords}, and I have hands-on experience with {matched}. "
        f"I’m excited by the role and confident I can contribute quickly.\n\n"
        f"From your job description, I see a focus on {matched}. "
        f"If selected, I can strengthen areas like {missing} through focused learning and collaboration.\n\n"
        f"Thank you for your time and consideration. I’d welcome the chance to discuss how I can help.\n\n"
        f"Sincerely,\n"
        f"[Your Name]\n"
    )
    
st.sidebar.header("\U0001F4C4 Upload Your Resume")
uploaded_file = st.sidebar.file_uploader("Upload .txt or .docx file", type=["txt", "docx"])

if uploaded_file is None:
    st.warning("Please upload your resume to get match scores.")
    st.stop()

# Read uploaded file
if uploaded_file.name.endswith(".txt"):
    resume_text = uploaded_file.read().decode("utf-8")
elif uploaded_file.name.endswith(".docx") and docx2txt:
    resume_text = docx2txt.process(uploaded_file)
else:
    st.error("Unsupported file type or missing docx2txt.")
    st.stop()


resume_skills = set(extract_resume_keywords(resume_text))  # still returns phrases
flat_keywords = flatten_keywords(resume_skills)
suggested_keywords = " ".join(flat_keywords) or "data"

# Region and search settings
st.sidebar.subheader("\U0001F30D Choose Region")
region = st.sidebar.selectbox("Seek Region", options=["Australia", "New Zealand"])

with st.sidebar.form("search_form"):
    st.subheader("📡 Live Job Search (Seek)")

    keywords = st.text_input("Keywords", value=suggested_keywords)
    location = st.text_input("Location", value="Melbourne")
    min_salary = st.number_input("Min Salary", value=100000, step=10000)
    max_salary = st.number_input("Max Salary", value=200000, step=10000)
    st.caption("Salary filtering is best-effort and depends on Seek’s URL parameters.")
    max_jobs = st.number_input("Number of Jobs", value=20, step=10)
    threads = st.number_input("Number of threads", value=1, step=1)
    submitted = st.form_submit_button("🔍 Search Seek Now")
    
jobs = []

if submitted:
    st.info("\U0001F50D Fetching jobs from Seek... this may take a minute.")

    scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
    ingest_script = scripts_dir / "ingest_seek_selenium.py"
    result = subprocess.run([
        sys.executable, str(ingest_script),
        "--keywords", keywords,
        "--location", location,
        "--min_salary", str(min_salary),
        "--max_salary", str(max_salary),
        "--region", region,
        "--max_jobs", str(max_jobs),
        "--threads", str(threads)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        st.error("\u274C Failed to fetch jobs:\n" + result.stderr)
        st.stop()
    else:
        st.success("\u2705 Successfully scraped and enriched jobs.")
        data_path = Path(__file__).resolve().parent.parent / "data" / "seek_jobs_enriched.json"
        with open(data_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

    # Generate embeddings
    if not jobs:
        st.warning("No jobs found for the current search filters.")
        st.stop()

    model = load_sentence_model()
    resume_embedding = model.encode(resume_text)
    job_texts = [job.get("description", "") for job in jobs]
    if not any(job_texts):
        st.warning("Fetched jobs are missing descriptions. Try a different search.")
        st.stop()
    job_embeddings = model.encode(job_texts)
    scores = cosine_similarity([resume_embedding], job_embeddings)[0]

    for job, score in zip(jobs, scores):
        job["match_score"] = round(float(score), 4)

    jobs = sorted(jobs, key=lambda x: x["match_score"], reverse=True)

    st.sidebar.header("\U0001F50D Filter Jobs")
    min_score = st.sidebar.slider("Minimum Match %", 0, 100, 50)
    keyword = st.sidebar.text_input("\U0001F524 Keyword in Title or Description")
    location_filter = st.sidebar.text_input("\U0001F4CD Location Filter")

    filtered = []
    for job in jobs:
        if job["match_score"] * 100 < min_score:
            continue
        if keyword and keyword.lower() not in (job["title"] + job["description"]).lower():
            continue
        if location_filter and location_filter.lower() not in job.get("location", "").lower():
            continue
        filtered.append(job)

    st.markdown(f"### \U0001F3AF Showing {len(filtered)} job(s) above {min_score}% match")

    for job in filtered:
        st.markdown(f"**{job['title']}** at *{job.get('company', 'Unknown')}*")
        st.markdown(f"\U0001F4CD {job.get('location', 'N/A')} | \U0001F517 [View on Seek]({job['link']}) | Match: {round(float(job['match_score']*100), 2)}% | Age: {job.get('date_posted', 'Unknown')}")
        st.progress(job["match_score"])

        with st.expander("\U0001F4C4 Description"):
            st.write(job["description"])

        job_skills = extract_skills(job["description"])
        matched_skills = sorted(resume_skills.intersection(job_skills))
        missing_skills = sorted(job_skills - resume_skills)

        with st.expander("\U0001F9E0 Skill Gap Analysis"):
            if matched_skills:
                st.markdown("\u2705 **Matched Skills:** " + ", ".join(matched_skills))
            else:
                st.markdown("\u274C No matched skills found.")
            if missing_skills:
                st.markdown("\u26A0\ufe0f **Missing Skills:** " + ", ".join(missing_skills))
            else:
                st.markdown("\U0001F389 You're covered on all listed skills!")

        with st.expander("\U0001F4E8 Application Toolkit"):
            cover_letter = build_cover_letter(job, resume_skills, matched_skills, missing_skills)
            edited_cover_letter = st.text_area(
                "Cover letter (editable)",
                value=cover_letter,
                height=240,
                key=f"cover_letter_{job.get('link', job.get('title', 'job'))}"
            )
            st.download_button(
                "Download cover letter (.txt)",
                data=edited_cover_letter,
                file_name="cover_letter.txt",
                mime="text/plain",
            )

            application_pack = {
                "job": {
                    "title": job.get("title"),
                    "company": job.get("company"),
                    "location": job.get("location"),
                    "link": job.get("link"),
                },
                "resume_keywords": sorted(resume_skills),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "cover_letter": edited_cover_letter,
            }
            st.download_button(
                "Download application pack (.json)",
                data=json.dumps(application_pack, indent=2),
                file_name="application_pack.json",
                mime="application/json",
            )

        st.markdown("---")
