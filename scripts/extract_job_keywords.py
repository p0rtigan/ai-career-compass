# scripts/extract_job_keywords.py

import spacy
from collections import Counter
import string

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if token.pos_ in ["NOUN", "PROPN", "VERB"]
        and token.text not in string.punctuation
        and not token.is_stop
    ]
    return Counter(tokens).most_common(20)

with open("../data/sample_jobs/job1.txt", "r", encoding="utf-8") as f:
    job_text = f.read()

keywords = extract_keywords(job_text)

print("🔍 Top keywords in job description:")
for word, freq in keywords:
    print(f"{word}: {freq}")
