# scripts/extract_skills.py

import docx
import spacy
from nltk.corpus import stopwords
from collections import Counter
import re

nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words("english"))

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def clean_text(text):
    text = re.sub(r'[^A-Za-z0-9\s]', '', text)
    text = text.lower()
    return text

def extract_keywords(text):
    doc = nlp(text)
    tokens = [
        token.lemma_ for token in doc
        if token.pos_ in ["NOUN", "PROPN", "VERB", "ADJ"]
        and token.text.lower() not in stop_words
    ]
    return Counter(tokens).most_common(20)

if __name__ == "__main__":
    resume_path = "../data/sample_resumes/chris_resume.docx"  # Replace with your path
    text = extract_text_from_docx(resume_path)
    clean = clean_text(text)
    keywords = extract_keywords(clean)

    print("🔍 Top extracted keywords:")
    for word, freq in keywords:
        print(f"{word}: {freq}")
