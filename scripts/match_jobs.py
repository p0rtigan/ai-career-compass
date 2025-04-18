from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json

# Load enriched job listings
with open("../data/seek_jobs_enriched.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Load your resume as plain text (you can paste it into a .txt file)
with open("../data/resume.txt", "r", encoding="utf-8") as f:
    resume_text = f.read()

# Load model (this is free + local)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Encode resume and each job description
resume_embedding = model.encode(resume_text)
job_embeddings = [model.encode(job["description"]) for job in jobs]

# Compute similarity scores
scores = cosine_similarity([resume_embedding], job_embeddings)[0]

# Attach scores to jobs
for job, score in zip(jobs, scores):
    job["match_score"] = round(float(score), 4)  # easier to read

# Sort jobs by best match
jobs_sorted = sorted(jobs, key=lambda x: x["match_score"], reverse=True)

# Output top 10
print("\n📊 Top Matching Jobs:\n")
for job in jobs_sorted[:10]:
    print(f"{job['match_score']*100:.1f}% match — {job['title']} at {job.get('company', 'N/A')}")

# Save results
with open("../data/seek_jobs_ranked.json", "w", encoding="utf-8") as f:
    json.dump(jobs_sorted, f, indent=2)
