# scripts/compare_similarity.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Paste your extracted keywords as "documents"
resume_keywords = [
    "datum", "management", "framework", "sql", "solution", "incident", "ssis",
    "teradata", "develop", "automate", "science", "data", "analytic", "etl",
    "automation", "reporting", "python", "platform", "team", "leadership"
]

job_keywords = [
    "work", "experience", "integration", "solution", "baker", "delight",
    "design", "include", "technology", "office", "system", "bakery",
    "development", "opportunity", "develop", "maintain", "team", "program",
    "policy", "manager"
]

# Convert to strings
doc1 = " ".join(resume_keywords)
doc2 = " ".join(job_keywords)

# Vectorise
vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform([doc1, doc2])

# Compute cosine similarity
similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

print(f"🧠 Resume-to-Job Match Score: {similarity:.2f} (0 = no match, 1 = perfect match)")
