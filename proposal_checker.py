# --------------------------------------------------------------
#  proposal_checker_tfidf.py   (TF-IDF ONLY – NO TORCH, NO ONNX)
# --------------------------------------------------------------
import os
import numpy as np
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List

# ---------- CONFIG ----------
MIN_WORDS        = 30
CHUNK_SIZE       = 500
DATASET_DIR      = "Sample Poroposal"
UPLOAD_PATH      = "your_uploaded_proposal.pdf"
MERGE_THRESHOLD  = 60   # % for merge recommendation
# --------------------------------------------------------------

def extract_text(pdf_path: str) -> str:
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print(f"PDF extract error: {e}")
        return ""

def chunk_text(text: str) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i+CHUNK_SIZE]) for i in range(0, len(words), CHUNK_SIZE)]

# ---------- MAIN ----------
def analyze(upload_path: str = UPLOAD_PATH):
    print("Indexing dataset (fresh every time)...")
    dataset_chunks = []
    dataset_sources = []

    for root, _, files in os.walk(DATASET_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, DATASET_DIR)
                text = extract_text(path)
                for chunk in chunk_text(text):
                    if len(chunk.split()) >= MIN_WORDS:
                        dataset_chunks.append(chunk)
                        dataset_sources.append(rel_path)

    if not dataset_chunks:
        raise RuntimeError("No dataset content found")

    # Uploaded file
    uploaded_text = extract_text(upload_path)
    if not uploaded_text.strip():
        raise RuntimeError("Uploaded PDF is empty")
    upload_chunks = [c for c in chunk_text(uploaded_text) if len(c.split()) >= MIN_WORDS]
    if not upload_chunks:
        raise RuntimeError("Uploaded PDF too short")

    # TF-IDF Vectorizer
    print(f"Vectorizing {len(dataset_chunks)} dataset + {len(upload_chunks)} uploaded chunks...")
    vectorizer = TfidfVectorizer(
        stop_words='english',
        lowercase=True,
        max_features=5000,
        ngram_range=(1, 2)
    )
    all_texts = dataset_chunks + upload_chunks
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Split back
    dataset_tfidf = tfidf_matrix[:-len(upload_chunks)]
    upload_tfidf = tfidf_matrix[-len(upload_chunks):]

    # Similarity
    sim_matrix = cosine_similarity(upload_tfidf, dataset_tfidf)
    max_sim_per_chunk = np.max(sim_matrix, axis=1)
    overall_similarity = float(np.mean(max_sim_per_chunk) * 100)

    # Top matches
    top_matches = []
    for i, score in enumerate(max_sim_per_chunk):
        if score > 0.05:  # >5%
            best_idx = np.argmax(sim_matrix[i])
            top_matches.append({
                "chunk": i + 1,
                "similarity": round(float(score * 100), 2),
                "document": dataset_sources[best_idx],
                "queryText": upload_chunks[i][:120] + ("..." if len(upload_chunks[i]) > 120 else "")
            })
    top_matches.sort(key=lambda x: x["similarity"], reverse=True)

    should_merge = overall_similarity > MERGE_THRESHOLD
    recommendation = (
        "These proposals are too alike. Suggest combining them."
        if should_merge else "Proposal is sufficiently unique."
    )

    print(f"\nOverall Similarity: {overall_similarity:.2f}% → {'MERGE' if should_merge else 'UNIQUE'}")
    for m in top_matches[:3]:
        print(f"  → {m['similarity']:.1f}% in {m['document']}")

    return {
        "overallScore": round(overall_similarity, 2),
        "shouldMerge": should_merge,
        "recommendation": recommendation,
        "matches": top_matches[:20]
    }

# For server.py
def analyze_proposals(upload_path: str = UPLOAD_PATH):
    return analyze(upload_path)

if __name__ == "__main__":
    analyze()