# 🧭 AI Career Compass

> Match your resume to the most relevant jobs across Seek (AU & NZ) using local AI and skill analysis.

---

## 🔍 Overview

**AI Career Compass** is a resume-driven job matching app that:

- Extracts keywords and skills from your uploaded resume using **KeyBERT** and **spaCy**
- Fetches live job listings from **Seek Australia** and **Seek New Zealand** using **Selenium**
- Enriches listings with job descriptions, company, location, and posting age
- Computes **semantic match scores** with **sentence-transformers**
- Highlights matched/missing skills and keyword relevance
- Provides an interactive Streamlit UI for filtering and comparison

---

## 💻 Features

- ✅ Upload `.txt` or `.docx` resume  
- ✅ Auto-extract job-related keywords (customisable)  
- ✅ Live Seek scraping (AU + NZ) with multithreaded enrichment  
- ✅ Keyword override, salary, region, location, and match % filters  
- ✅ Skill gap insights with matched/missing highlights  
- ✅ Downloadable and transparent JSON data  
- ✅ Fully local and free — runs on your machine

---

## 🚀 Getting Started

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-career-compass.git
cd ai-career-compass
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate    # On Windows
# OR
source venv/bin/activate   # On Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Run the app

```bash
streamlit run app/match_explorer.py
```

---

## 📂 Project Structure

```
ai-career-compass/
├── app/
│   └── match_explorer.py          # Main Streamlit UI
├── scripts/
│   └── ingest_seek_selenium.py    # Live job scraping + enrichment
├── data/
│   └── seek_jobs_enriched.json    # Cached job data (optional)
├── requirements.txt
├── README.md
├── start.sh / render.yaml         # (Optional) for deployment
```

---

## 🧠 Tech Stack

- Streamlit — frontend UI  
- Selenium — for Seek scraping  
- spaCy — resume parsing  
- KeyBERT — keyword extraction  
- Sentence-Transformers — semantic similarity  
- Scikit-learn — cosine similarity + ranking

---

## 🧪 Testing

This project doesn't yet include unit tests. You can manually test it by:

- Uploading `.txt` or `.docx` resumes and verifying extracted keywords  
- Changing location/region/salary in the UI and confirming new jobs load  
- Confirming match score and skill gap displays work as expected

Test automation can be added with `pytest` and `unittest`.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repo  
2. Create a new branch: `git checkout -b my-feature`  
3. Make changes and commit: `git commit -m 'Add feature'`  
4. Push and open a pull request  

Please document any new modules or functions.

---

## 🛡️ Disclaimer

This tool is intended for **personal and educational use only**.  
Respect [Seek’s Terms of Use](https://www.seek.com.au/legal) and do not scrape at scale or commercially.

---

## 🌐 Deployment Options

- ✅ Works locally via Streamlit  
- ✅ Supports Render.com deployment (`start.sh` included)  
- 🔜 Fly.io / FastAPI / Gradio support coming soon

---

## 📬 Contact

Made by [Christopher Monteiro](https://www.linkedin.com/in/christopher-monteiro-943b96153/)  
Feel free to fork, extend, or contribute!
