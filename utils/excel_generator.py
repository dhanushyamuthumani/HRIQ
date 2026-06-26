import pandas as pd
import os
from datetime import datetime
from config import OUTPUT_FOLDER, EXCEL_FILENAME

def generate_excel(data: list) -> str:
    """Generates an Excel file from the list of processed resumes."""
    if not data:
        return ""
    
    df = pd.DataFrame(data)
    
    # Add S.No
    df.insert(0, "S.No", range(1, len(df) + 1))
    
    # Reorder columns for better presentation
    columns_order = [
        "S.No", "full_name", "email", "phone", "one_liner", "industry_domain", "working_role", 
        "technologies", "total_experience_years", "experience_category", 
        "technical_evaluation", "resume_score", "is_duplicate"
    ]
    
    # Only keep columns that exist in the dataframe
    existing_cols = [col for col in columns_order if col in df.columns]
    df = df[existing_cols]
    
    # Rename columns for Excel
    df.columns = [col.replace("_", " ").title() for col in df.columns]
    
    # Format technologies list as string
    if "Technologies" in df.columns:
        df["Technologies"] = df["Technologies"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_FOLDER, f"resumes_analysis_{timestamp}.xlsx")
    
    df.to_excel(output_path, index=False)
    return output_path
