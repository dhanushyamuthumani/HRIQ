from typing import Dict, Any

def calculate_score(data: Dict[str, Any]) -> int:
    """
    Calculates a resume quality score from 0 to 100 based on several factors:
    - Completeness (Email, Phone, Summary)
    - Technical Depth (Number of technologies)
    - Experience level
    """
    score = 0
    
    # 1. Completeness (30 points)
    if data.get("email") and data.get("email") != "N/A":
        score += 10
    if data.get("phone") and data.get("phone") != "N/A":
        score += 10
    if data.get("summary") and data.get("summary") != "N/A":
        score += 10
        
    # 2. Technical Depth (40 points)
    techs = data.get("technologies", [])
    if isinstance(techs, list):
        count = len(techs)
        if count >= 8:
            score += 40
        elif count >= 5:
            score += 30
        elif count >= 3:
            score += 20
        elif count >= 1:
            score += 10
            
    # 3. Experience Depth (30 points)
    years = data.get("total_experience_years", 0)
    try:
        years = float(years)
    except:
        years = 0
        
    if years >= 10:
        score += 30
    elif years >= 5:
        score += 25
    elif years >= 3:
        score += 20
    elif years >= 1:
        score += 10
        
    return min(score, 100)

def process_scoring(ai_result: dict) -> dict:
    """Appends the score to the result dictionary."""
    ai_result["resume_score"] = calculate_score(ai_result)
    return ai_result
