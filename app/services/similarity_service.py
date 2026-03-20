# ============================================================
# app/services/similarity_service.py
# Semantic Similarity Analysis using Sentence Transformers
#
# What is Semantic Similarity?
# Regular comparison: "dog" != "canine" (different words, marked as different)
# Semantic comparison: "dog" ≈ "canine" (same meaning, scored as similar!)
#
# How it works:
# 1. Convert text into a list of numbers (called "embedding vector")
#    Example: "dog" → [0.2, -0.5, 0.8, 0.1, ...]  (384 numbers!)
# 2. Compare two vectors using "Cosine Similarity"
#    - 1.0 = identical meaning
#    - 0.0 = completely unrelated
#    - -1.0 = opposite meaning
#
# Why Sentence Transformers?
# Trained on millions of sentences to understand MEANING, not just words.
# ============================================================

import hashlib
import json
import logging
from typing import List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

# ---- Load the AI model ----
# This model is downloaded once (~90MB) and cached locally
# It understands the meaning of sentences
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    
    print("🤖 Loading AI model (sentence-transformers)...")
    print("   First time may take a minute to download...")
    
    # 'all-MiniLM-L6-v2' is:
    # - Small (only 90MB)
    # - Fast
    # - Surprisingly accurate
    # Other options: 'all-mpnet-base-v2' (better but larger)
    MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    SIMILARITY_AVAILABLE = True
    print("✅ AI model loaded successfully!")
    
except ImportError as e:
    print(f"⚠️  Sentence Transformers not available: {e}")
    print("   Install with: pip install sentence-transformers scikit-learn")
    MODEL = None
    SIMILARITY_AVAILABLE = False


def _text_to_hash(text: str) -> str:
    """
    Create a unique fingerprint (hash) of a text string.
    Same text always produces same hash.
    Used to cache embeddings so we don't recompute them.
    
    Example: "hello world" → "b94d27b9934d3e08a52e52d7..."
    """
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def get_embedding(text: str, use_cache: bool = True) -> Optional[List[float]]:
    """
    Convert a text string into a vector of numbers (embedding).
    
    This is the "magic" that allows semantic comparison!
    The model has been trained to put similar-meaning sentences
    close together in this numerical space.
    
    Args:
        text: The text to convert
        use_cache: Whether to cache the result (saves time for repeated texts)
    
    Returns:
        A list of 384 float numbers, or None if model not available
    """
    if not SIMILARITY_AVAILABLE or MODEL is None:
        return None
    
    # Try to get from cache first (saves ~50ms per embedding)
    if use_cache:
        try:
            from app.utils.cache import cache
            text_hash = _text_to_hash(text)
            cached = cache.get_embeddings(text_hash)
            if cached is not None:
                return cached
        except Exception:
            pass
    
    # Compute the embedding
    try:
        # MODEL.encode() runs the neural network
        embedding = MODEL.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()  # Convert numpy array to Python list
        
        # Save to cache
        if use_cache:
            try:
                from app.utils.cache import cache
                cache.set_embeddings(text_hash, embedding_list)
            except Exception:
                pass
        
        return embedding_list
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        return None


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate how similar two embedding vectors are.
    
    Cosine Similarity measures the ANGLE between two vectors:
    - Angle = 0° → similarity = 1.0 (identical direction = same meaning)
    - Angle = 90° → similarity = 0.0 (perpendicular = unrelated)
    - Angle = 180° → similarity = -1.0 (opposite)
    
    Returns a value between 0.0 and 1.0 (we clamp negative values to 0).
    """
    try:
        # Reshape for sklearn's cosine_similarity function
        # It expects 2D arrays: [[1,2,3]] not [1,2,3]
        v1 = np.array(vec1).reshape(1, -1)
        v2 = np.array(vec2).reshape(1, -1)
        
        similarity = cosine_similarity(v1, v2)[0][0]
        
        # Clamp between 0 and 1 (semantic similarity is non-negative)
        return float(max(0.0, min(1.0, similarity)))
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        return 0.0


def analyze_semantic_similarity(
    student_answer: str,
    expected_answer: str
) -> dict:
    """
    Main function: Compare a student's answer to the expected answer.
    
    Returns a detailed analysis including:
    - How similar the answers are (0.0 to 1.0)
    - What key concepts were found/missing
    - Performance label (Excellent/Good/Average/Poor)
    
    Args:
        student_answer: What the student wrote
        expected_answer: The ideal/correct answer
    
    Returns:
        Dictionary with full analysis
    """
    
    # ---- Fallback if AI model is not available ----
    if not SIMILARITY_AVAILABLE:
        logger.warning("Using keyword fallback (AI model not available)")
        return _keyword_similarity_fallback(student_answer, expected_answer)
    
    # ---- Step 1: Get embeddings for both texts ----
    student_embedding = get_embedding(student_answer)
    expected_embedding = get_embedding(expected_answer)
    
    if student_embedding is None or expected_embedding is None:
        return _keyword_similarity_fallback(student_answer, expected_answer)
    
    # ---- Step 2: Calculate semantic similarity ----
    similarity_score = calculate_cosine_similarity(student_embedding, expected_embedding)
    
    # ---- Step 3: Find key concepts ----
    found_concepts, missing_concepts = _analyze_key_concepts(student_answer, expected_answer)
    
    # ---- Step 4: Determine performance level ----
    match_level, performance_label = _score_to_performance(similarity_score)
    
    return {
        "cosine_similarity": round(similarity_score, 4),
        "similarity_percentage": round(similarity_score * 100, 1),
        "semantic_match": similarity_score >= 0.35,
        "match_level": match_level,
        "performance_label": performance_label,
        "key_concepts_found": found_concepts,
        "key_concepts_missing": missing_concepts,
        "analysis_method": "semantic_ai"
    }


def _score_to_performance(score: float) -> Tuple[str, str]:
    """
    Convert a numeric score to human-readable labels.
    
    Score ranges:
    - 0.65 - 1.00: Excellent (knows the material very well)
    - 0.50 - 0.64: Good (understands the core concepts, different wording OK)
    - 0.35 - 0.49: Average (partial understanding)
    - 0.20 - 0.34: Poor (limited understanding)
    - 0.00 - 0.19: Very Poor (off-topic or wrong)
    """
    if score >= 0.65:
        return ("exact", "Excellent")
    elif score >= 0.50:
        return ("high", "Good")
    elif score >= 0.35:
        return ("medium", "Average")
    elif score >= 0.20:
        return ("low", "Poor")
    else:
        return ("very_low", "Very Poor")


def _analyze_key_concepts(student_answer: str, expected_answer: str) -> Tuple[List[str], List[str]]:
    """
    Check which key words/concepts from the expected answer appear in the student's answer.
    
    This is a simple word-overlap check (not semantic).
    Used alongside the AI similarity score for detailed feedback.
    """
    # Words to ignore (too common to be meaningful)
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would',
        'can', 'could', 'should', 'may', 'might', 'shall', 'must',
        'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from',
        'that', 'this', 'it', 'its', 'and', 'or', 'but', 'not', 'no',
        'which', 'who', 'what', 'when', 'where', 'how', 'why',
        'i', 'you', 'he', 'she', 'we', 'they', 'all', 'also'
    }
    
    def extract_key_words(text: str) -> set:
        """Extract meaningful words from text."""
        words = text.lower().split()
        # Keep words longer than 3 chars that aren't stop words
        return {w.strip('.,!?;:()[]') for w in words 
                if len(w) > 3 and w not in stop_words}
    
    expected_keywords = extract_key_words(expected_answer)
    student_keywords = extract_key_words(student_answer)
    
    # Which expected keywords did the student mention?
    found = list(expected_keywords & student_keywords)[:5]  # Max 5
    missing = list(expected_keywords - student_keywords)[:5]  # Max 5
    
    return found, missing


def _keyword_similarity_fallback(student_answer: str, expected_answer: str) -> dict:
    """
    Simple keyword overlap similarity (no AI needed).
    Used when the AI model is not available.
    
    Not as smart as semantic similarity, but better than nothing!
    """
    def get_words(text: str) -> set:
        return set(text.lower().split())
    
    student_words = get_words(student_answer)
    expected_words = get_words(expected_answer)
    
    if not expected_words:
        return {"cosine_similarity": 0.0, "similarity_percentage": 0.0}
    
    # Jaccard similarity: intersection / union
    intersection = len(student_words & expected_words)
    union = len(student_words | expected_words)
    similarity = intersection / union if union > 0 else 0.0
    
    found = list(student_words & expected_words)[:5]
    missing = list(expected_words - student_words)[:5]
    
    match_level, performance_label = _score_to_performance(similarity)
    
    return {
        "cosine_similarity": round(similarity, 4),
        "similarity_percentage": round(similarity * 100, 1),
        "semantic_match": similarity >= 0.3,
        "match_level": match_level,
        "performance_label": performance_label,
        "key_concepts_found": found,
        "key_concepts_missing": missing,
        "analysis_method": "keyword_fallback"
    }


def generate_question_fingerprint(question_text: str) -> str:
    """
    Create a unique fingerprint for a question.
    Used to detect if two questions are semantically similar
    (prevents asking the same question twice in different words).
    
    Returns: A hash string representing the question's meaning
    """
    # Get the semantic embedding of the question
    embedding = get_embedding(question_text)
    
    if embedding:
        # Use first 10 values of embedding as fingerprint
        # (Good enough to detect similar questions)
        fingerprint_data = [round(v, 2) for v in embedding[:10]]
        fingerprint = hashlib.sha256(str(fingerprint_data).encode()).hexdigest()[:16]
    else:
        # Fallback: simple hash of the question text
        fingerprint = hashlib.md5(question_text.lower().encode()).hexdigest()[:16]
    
    return fingerprint


def find_similar_questions(
    new_question: str,
    existing_questions: List[dict],
    threshold: float = 0.85
) -> List[dict]:
    """
    Check if a new question is too similar to existing questions.
    Returns any existing questions that are too similar.
    
    Used when adding new questions to prevent duplicates.
    
    Args:
        new_question: The question text to check
        existing_questions: List of existing questions (with 'question_text' field)
        threshold: Similarity threshold (0.85 = 85% similar is considered duplicate)
    """
    if not SIMILARITY_AVAILABLE or not existing_questions:
        return []
    
    new_embedding = get_embedding(new_question)
    if new_embedding is None:
        return []
    
    similar_questions = []
    
    for q in existing_questions:
        existing_embedding = get_embedding(q.get("question_text", ""))
        if existing_embedding is None:
            continue
        
        similarity = calculate_cosine_similarity(new_embedding, existing_embedding)
        
        if similarity >= threshold:
            similar_questions.append({
                **q,
                "similarity_to_new": round(similarity, 4)
            })
    
    return similar_questions
