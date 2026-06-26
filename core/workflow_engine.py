import logging
from typing import Dict, Any
from config import OLLAMA_MODEL

# Configure logging
logger = logging.getLogger(__name__)

WORKFLOW_PROMPT = """
You are an HR Assistant. Generate a professional email to the candidate based on the following details and the desired action.

Action: {action} (e.g., Interview Invite, Rejection)
Candidate Name: {full_name}
Role Applied For: {working_role}
JD Summary: {jd_summary}

Rules:
1. Keep it professional and concise.
2. Use placeholders for meeting dates/times if it's an invite.
3. If it's a rejection, be polite and encouraging.

Return ONLY the email body.
"""

def generate_email(candidate_data: Dict[str, Any], action: str, jd_summary: str = "") -> str:
    """Generates an email draft for a candidate."""
    prompt = WORKFLOW_PROMPT.format(
        action=action,
        full_name=candidate_data.get("full_name", "Candidate"),
        working_role=candidate_data.get("working_role", "Position"),
        jd_summary=jd_summary
    )
    
    try:
        from config import get_ollama_client
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response['response'].strip()
    except Exception as e:
        logger.error(f"Error in workflow engine: {e}")
        return f"Failed to generate email: {e}"
