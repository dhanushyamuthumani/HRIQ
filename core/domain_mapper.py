from config import INDUSTRY_DOMAINS

def map_domain(domain: str) -> str:
    """Fallback/Validation for industry domain mapping."""
    if not domain:
        return "Other"
    
    # Normalize
    domain_clean = domain.strip()
    if domain_clean in INDUSTRY_DOMAINS:
        return domain_clean
    
    # Check for partial matches
    for valid_domain in INDUSTRY_DOMAINS:
        if valid_domain.lower() in domain_clean.lower():
            return valid_domain
            
    return "Other"
