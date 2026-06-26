from config import EXPERIENCE_LEVELS

def get_experience_category(years: float) -> str:
    """Categorizes experience based on years."""
    for category, (min_years, max_years) in EXPERIENCE_LEVELS.items():
        if min_years <= years < max_years:
            return category
    return "Unknown"

def process_experience(ai_result: dict) -> dict:
    """Extracts years and adds category to the result."""
    years = ai_result.get("total_experience_years", 0)
    try:
        years = float(years)
    except (ValueError, TypeError):
        years = 0.0
    
    ai_result["total_experience_years"] = years
    ai_result["experience_category"] = get_experience_category(years)
    return ai_result
