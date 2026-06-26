from typing import List, Dict, Any
import pandas as pd

def search_candidates(data: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Performs a smart key-term search across name, role, domain, and technologies,
    filtering out common recruiter query filler words (like 'profile', 'resume', etc.).
    """
    if not query:
        return data
        
    query = query.lower().strip()
    
    # Clean punctuation
    for char in [".", ",", "?", "!", ";", ":", "-", "_"]:
        query = query.replace(char, " ")
        
    words = query.split()
    
    # Recruiter query filler/stop words to ignore
    filler_words = {
        "profile", "profiles", "resume", "resumes", "cv", "cvs", "candidate", "candidates", 
        "need", "find", "search", "show", "me", "get", "who", "is", "are", "for", "a", "an", 
        "the", "with", "knows", "know", "have", "has", "in", "at", "please", "developer", "engineer"
    }
    
    search_terms = [w for w in words if w not in filler_words]
    
    # If query was just filler words (e.g. "show me profiles"), match everything
    if not search_terms:
        # Fall back to matching words that aren't very generic
        search_terms = [w for w in words if w not in {"me", "show", "find", "get", "please"}]
        if not search_terms:
            return data
        
    results = []
    
    for candidate in data:
        name = str(candidate.get('full_name', '')).lower()
        role = str(candidate.get('working_role', '')).lower()
        domain = str(candidate.get('industry_domain', '')).lower()
        techs = [str(t).lower() for t in candidate.get('technologies', [])]
        
        search_blob = f"{name} {role} {domain} {' '.join(techs)}"
        
        # Check if all key search terms are present in candidate profile
        match = True
        for term in search_terms:
            if term not in search_blob:
                match = False
                break
                
        if match:
            results.append(candidate)
            
    return results

