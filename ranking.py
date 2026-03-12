from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def compute_tfidf_similarity(job_desc: str, resume_text: str) -> float:
    """Compute TF-IDF cosine similarity between job desc and resume"""
    if not job_desc.strip() or not resume_text.strip():
        return 0.0
    
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([job_desc, resume_text])
    
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0][0]
    return float(similarity)
