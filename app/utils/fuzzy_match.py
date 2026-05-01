"""
Fuzzy Match Utility — Helps matching mispronounced voice products to the database.
Uses a combination of SequenceMatcher and Token-set matching.
"""
from difflib import SequenceMatcher

def get_similarity(a: str, b: str) -> float:
    """Returns a similarity score between 0 and 1."""
    if not a or not b:
        return 0
        
    s1 = a.lower().strip()
    s2 = b.lower().strip()
    
    # 1. Base ratio (SequenceMatcher)
    base_ratio = SequenceMatcher(None, s1, s2).ratio()
    
    # 2. Token-based check
    tokens1 = s1.split()
    tokens2 = s2.split()
    
    if not tokens1 or not tokens2:
        return base_ratio
        
    set1 = set(tokens1)
    set2 = set(tokens2)
    
    intersection = set1.intersection(set2)
    token_ratio = len(intersection) / max(len(set1), len(set2))
    
    # 3. Subset check (very important for names like "Rajan" -> "Rajan Sharma")
    # If all tokens of the shorter string are in the longer string, it's a strong match
    is_subset = False
    if len(set1) < len(set2):
        is_subset = set1.issubset(set2)
    else:
        is_subset = set2.issubset(set1)
        
    subset_score = 0.9 if is_subset else 0
    
    return max(base_ratio, token_ratio, subset_score)

def find_best_match(query: str, choices: list[str], threshold: float = 0.6):
    """
    Finds the best match for 'query' among 'choices'.
    Returns (match_text, score) or (None, 0) if below threshold.
    """
    best_score = 0
    best_match = None
    
    query_clean = query.lower().strip()
    
    for choice in choices:
        score = get_similarity(query_clean, choice)
        if score > best_score:
            best_score = score
            best_match = choice
            
    if best_score >= threshold:
        return best_match, best_score
    
    return None, 0
