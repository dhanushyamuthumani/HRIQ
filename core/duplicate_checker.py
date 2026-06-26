import pandas as pd
from typing import List, Dict, Any

def detect_duplicates(processed_resumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """ Marks duplicates in a list of processed resume data based on Email and Phone. """
    if not processed_resumes:
        return []

    # Create a DataFrame for easier processing
    df = pd.DataFrame(processed_resumes)
    
    # Track seen email and phone identifiers separately to avoid collisions
    seen_emails = set()
    seen_phones = set()
    
    for index, row in df.iterrows():
        email = str(row.get('email', '')).strip().lower()
        phone = str(row.get('phone', '')).strip()
        
        is_duplicate = False
        
        # Check email duplicate
        if email and email not in ["n/a", "none", ""]:
            if email in seen_emails:
                is_duplicate = True
            else:
                seen_emails.add(email)
                
        # Check phone duplicate (only if not already marked)
        if not is_duplicate and phone and phone not in ["n/a", "none", ""]:
            if phone in seen_phones:
                is_duplicate = True
            else:
                seen_phones.add(phone)
        
        df.at[index, 'is_duplicate'] = "Yes" if is_duplicate else "No"
    
    return df.to_dict('records')
