from typing import Dict, Any, List
from config import OLLAMA_MODEL

MATCHER_PROMPT = """
You are an expert HR recruitment matcher. Compare the provided Job Description (JD) with the Candidate's Resume details and provide a matching analysis.

Job Description:
{jd_text}

Candidate Details:
- Name: {full_name}
- Role: {working_role}
- Technologies: {technologies}
- Experience: {experience} years
- Summary: {summary}

Return the analysis in valid JSON format only:
{{
  "match_score": 85,
  "matching_skills": ["Skill 1", "Skill 2"],
  "missing_skills": ["Missing Skill 1"],
  "explanation": "Brief 2-sentence explanation of the match."
}}
"""

def match_candidate_to_jd(candidate_data: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
    """Uses LLM to calculate match score between candidate and JD."""
    tech_list = candidate_data.get("technologies", [])
    tech_str = ", ".join(tech_list) if isinstance(tech_list, list) else "N/A"
    
    prompt = MATCHER_PROMPT.format(
        jd_text=jd_text,
        full_name=candidate_data.get("full_name", "N/A"),
        working_role=candidate_data.get("working_role", "N/A"),
        technologies=tech_str,
        experience=candidate_data.get("total_experience_years", 0),
        summary=candidate_data.get("summary", "")
    )
    
    try:
        from config import get_ollama_client
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={"temperature": 0.1}
        )
        
        # We can use the same clean/parse logic from core.json_parser
        from core.json_parser import parse_ai_response
        result = parse_ai_response(response['response'])
        return result or {"match_score": 0, "matching_skills": [], "missing_skills": [], "explanation": "Matching failed."}
    except Exception as e:
        print(f"Error in matcher engine: {e}")
        return {"match_score": 0, "matching_skills": [], "missing_skills": [], "explanation": f"Error: {e}"}
