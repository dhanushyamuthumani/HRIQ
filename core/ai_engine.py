import ollama
import time
from typing import Optional, Dict, Any
from config import OLLAMA_MODEL, OLLAMA_TIMEOUT, INDUSTRY_DOMAINS, MAX_TEXT_LENGTH, get_ollama_client
from core.json_parser import parse_ai_response
import re
import json
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def is_ollama_alive() -> bool:
    """Checks if the Ollama server is reachable (handles both cloud and local hosts)."""
    import socket
    import requests
    from config import OLLAMA_HOST, OLLAMA_API_KEY
    if OLLAMA_API_KEY:
        try:
            url = OLLAMA_HOST.rstrip("/") + "/api/tags"
            headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}"}
            response = requests.get(url, headers=headers, timeout=3)
            # A 200 means success, 404 is also acceptable as some gateways expose endpoints differently
            return response.status_code in [200, 404]
        except Exception as e:
            logger.warning(f"Ollama Cloud check failed: {e}")
            return False
    else:
        try:
            with socket.create_connection(("localhost", 11434), timeout=1):
                return True
        except:
            return False


PROMPT_TEMPLATE = """
As an elite HR analyst, extract structured data from the resume text into VALID JSON.

Resume Text:
{resume_text}

JSON Schema:
{{
  "full_name": "string",
  "email": "string",
  "phone": "Mobile Number",
  "industry_domain": "{domains}",
  "working_role": "Primary professional title (e.g., 'Senior Frontend Engineer')",
  "one_liner": "A 1-sentence catchy profile summary (e.g., 'Senior QA with 8 years experience in Automation')",
  "technologies": ["List specific tools/languages"],
  "total_experience_years": float,
  "technical_evaluation": "A 3-sentence expert assessment of their technical depth, architecture knowledge, and tool proficiency.",
  "summary": "2-sentence professional bio",
  "elevator_pitch": "A 2-sentence aggressive hook about why they are a top-tier hire"
}}

CRITICAL RULES:
1. TOTAL_EXPERIENCE_YEARS: Carefully calculate total years from the first job to today. If current year is 2026, and they started in 2018, that is 8.0 years. MUST BE A NUMBER.
2. INDUSTRY_DOMAIN: Select the MOST relevant from: {domains}. Use 'Other' if no match.
3. OUTPUT: Strictly valid JSON. No commentary. No markdown backticks.
"""

def get_dynamic_prompt(resume_text: str) -> str:
    """Returns the prompt template with current year context."""
    curr_year = datetime.now().year
    return PROMPT_TEMPLATE.replace("{domains}", ", ".join(INDUSTRY_DOMAINS)).replace("2026", str(curr_year)).format(resume_text=resume_text, domains=", ".join(INDUSTRY_DOMAINS))

def sanitize_ai_result(result: Dict[str, Any], original_text: str, filename: str = None) -> Dict[str, Any]:
    """
    Performs post-processing and sanitization on the AI-generated result.
    Ensures data types and values are within expected ranges.
    """
    if not result:
        return {}

    # Ensure experience is a float and not negative
    try:
        exp = float(result.get("total_experience_years", 0))
        result["total_experience_years"] = max(0.0, min(exp, 50.0)) # Sensible limits
    except (ValueError, TypeError):
        result["total_experience_years"] = 0.0
    
    # Clean Role
    if not result.get("working_role") or result["working_role"].lower() == "string":
        result["working_role"] = "Specialist"

    # Ensure technologies is a list
    if not isinstance(result.get("technologies"), list):
        result["technologies"] = []
    
    # Ensure technical_evaluation exists
    if not result.get("technical_evaluation"):
        result["technical_evaluation"] = "Technical depth assessment not provided by AI."
    
    # Ensure one_liner exists
    if not result.get("one_liner"):
        result["one_liner"] = f"{result.get('working_role', 'Specialist')} with focus on technical excellence."

    # Final "None" sweep: replace any remaining None with "N/A"
    for key in result:
        if result[key] is None:
            result[key] = "N/A"
    
    # Basic validation for critical fields
    if not result.get("full_name") or result["full_name"] == "Unknown Candidate" or len(result["full_name"]) < 3:
        # Attempt to extract name from first few meaningful lines
        lines = [l.strip() for l in original_text.splitlines() if l.strip()]
        # Skip generic headers
        headers_to_skip = ["resume", "curriculum vitae", "cv", "profile", "contact", "summary"]
        candidate_name = "Unknown Candidate"
        for line in lines[:5]:
            if line.lower() not in headers_to_skip and len(line) > 3:
                # Basic name check: must have at least one space and be mostly alphabetic
                if " " in line and all(c.isalpha() or c.isspace() or c == "." for c in line):
                    candidate_name = line
                    break
        result["full_name"] = candidate_name

    if not result.get("email") or "@" not in result["email"]:
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", original_text)
        if email_match:
            result["email"] = email_match.group(0).strip()
        else:
            result["email"] = "N/A"

    if not result.get("phone") or not re.search(r"\d", result["phone"]):
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", original_text)
        if phone_match:
            result["phone"] = phone_match.group(0).strip()
        else:
            result["phone"] = "N/A"

    # Ensure industry_domain is one of the allowed domains or 'Other'
    if result.get("industry_domain") not in INDUSTRY_DOMAINS:
        result["industry_domain"] = "Other"

    return result

def analyze_resume(resume_text: str, filename: str = None) -> Optional[Dict[str, Any]]:
    """Sends the resume text to Ollama and returns the structured analysis."""
    # Truncate text moderately to balance context and speed
    truncated_text = resume_text[:MAX_TEXT_LENGTH]
    
    if not is_ollama_alive():
        logger.error("CRITICAL: Ollama server is not reachable. Generation skipped.")
        return None

    prompt = get_dynamic_prompt(truncated_text)
    
    try:
        client = get_ollama_client()
        
        start_time = time.time()
        # Primary Attempt: JSON Mode for strict adherence
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            format="json", # Force JSON output
            options={
                "temperature": 0.0,
                "num_ctx": 8192,
                "num_predict": 1024,
                "top_k": 20,
                "repeat_penalty": 1.1
            }
        )
        
        raw_response = response.get('response', '')
        result = None
        if raw_response:
            result = parse_ai_response(raw_response)
        
        # Secondary Attempt: Standard Prompt (if JSON mode failed or returned nothing)
        if not result:
            logger.info("AI Engine: Primary JSON attempt failed. Retrying with standard prompt...")
            response = client.generate(
                model=OLLAMA_MODEL,
                prompt=prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON.",
                options={"temperature": 0.1, "num_ctx": 8192}
            )
            raw_response = response.get('response', '')
            if raw_response:
                result = parse_ai_response(raw_response)

        # --- Intelligence Post-Processing ---
        if result:
            result = sanitize_ai_result(result, truncated_text, filename)
            duration = time.time() - start_time
            logger.info(f"AI Analysis completed in {duration:.2f}s.")
            return result
        
        # Fallback Attempt (Targeted Extraction)
        logger.warning("AI Engine: All JSON attempts failed. Attempting targeted fallback...")
        fallback_prompt = f"""
        Extract the following fields from the resume text:
        NAME: [Full Name]
        EMAIL: [Email Address]
        MOBILE: [Phone/Mobile]
        ROLE: [Current/Last Role]
        EXP: [Total Years of Experience as a Number]
        DOMAIN: [Industry Domain]
        
        Text: {truncated_text[:2000]}
        """
        
        fb_response = client.generate(model=OLLAMA_MODEL, prompt=fallback_prompt)
        fb_text = fb_response.get('response', '')
        
        # Extract via regex
        def get_f(p, t):
            m = re.search(p, t, re.I | re.M)
            return m.group(1).strip() if m else "N/A"

        result = {
            "full_name": get_f(r"NAME:\s*(.*)", fb_text),
            "email": get_f(r"EMAIL:\s*(.*)", fb_text),
            "phone": get_f(r"MOBILE:\s*(.*)", fb_text),
            "working_role": get_f(r"ROLE:\s*(.*)", fb_text),
            "one_liner": "Profile extracted via fallback.",
            "total_experience_years": 0.0,
            "industry_domain": get_f(r"DOMAIN:\s*(.*)", fb_text),
            "technologies": [],
            "technical_evaluation": "Basic extraction via fallback.",
            "summary": "Extraction via fallback."
        }
        
        exp_str = get_f(r"EXP:\s*(.*)", fb_text)
        try:
            result["total_experience_years"] = float(re.search(r"(\d+\.?\d*)", exp_str).group(1))
        except: pass
        
        logger.info("AI Engine: Targeted fallback extraction completed.")
        return sanitize_ai_result(result, truncated_text, filename)
        
    except Exception as e:
        # Improved error messages
        error_msg = str(e).lower()
        if "connection" in error_msg:
            logger.error("CRITICAL: Ollama server is not reachable. Run 'ollama serve'.")
        elif "not found" in error_msg:
            logger.error(f"CRITICAL: Model '{OLLAMA_MODEL}' is missing. Run 'ollama pull {OLLAMA_MODEL}'.")
        else:
            logger.error(f"Error calling Ollama: {e}")
        
        # FINAL HEURISTIC BACKUP (Non-AI)
        logger.warning("AI Engine failed completely. Falling back to Heuristic Extraction...")
        final_res = {
            "full_name": "Unknown Candidate",
            "email": "N/A",
            "phone": "N/A",
            "working_role": "Specialist",
            "one_liner": "Extraction via heuristic backup (AI Offline).",
            "total_experience_years": 0.0,
            "industry_domain": "Other",
            "technologies": [],
            "technical_evaluation": "Extraction failed.",
            "summary": "Extraction failed due to AI system error."
        }
        return sanitize_ai_result(final_res, truncated_text, filename)

def generate_interview_questions(candidate_data: Dict[str, Any]) -> str:
    """Generates 5 tailored technical interview questions with ideal answers."""
    from config import get_ollama_client, OLLAMA_MODEL
    
    techs = candidate_data.get("technologies", [])
    tech_str = ", ".join(techs) if isinstance(techs, list) else "N/A"
    
    prompt = f"""
You are an elite technical interviewer. Generate 5 targeted technical interview questions for the candidate based on their profile.
For each question, provide:
1. The question.
2. The core concept being tested.
3. The expected/ideal answer.

Candidate Profile:
- Name: {candidate_data.get('full_name', 'N/A')}
- Role: {candidate_data.get('working_role', 'N/A')}
- Technologies: {tech_str}
- Experience: {candidate_data.get('total_experience_years', 0)} years
- Summary: {candidate_data.get('summary', 'N/A')}
- Technical Evaluation: {candidate_data.get('technical_evaluation', 'N/A')}

Return the output in a clean, professional, readable format with markdown headings and bold text. No JSON wrapper needed, just beautiful, direct markdown.
"""
    try:
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        return f"Failed to generate interview questions: {e}"

def generate_client_pitch(candidate_data: Dict[str, Any]) -> str:
    """Generates a professional, client-ready summary / client pitch."""
    from config import get_ollama_client, OLLAMA_MODEL
    
    techs = candidate_data.get("technologies", [])
    tech_str = ", ".join(techs) if isinstance(techs, list) else "N/A"
    
    prompt = f"""
You are an expert recruitment marketer. Create an elite candidate summary presentation ("Client Pitch") to send to potential hiring managers.
Highlight the candidate's core value proposition, key achievements, and why they would be an exceptional hire.

Candidate Profile:
- Name: {candidate_data.get('full_name', 'N/A')}
- Role: {candidate_data.get('working_role', 'N/A')}
- Technologies: {tech_str}
- Experience: {candidate_data.get('total_experience_years', 0)} years
- Bio Summary: {candidate_data.get('summary', 'N/A')}
- Elevator Pitch: {candidate_data.get('elevator_pitch', 'N/A')}
- Technical Evaluation: {candidate_data.get('technical_evaluation', 'N/A')}

Structure your response into these sections:
1. **Candidate Profile Summary** (brief professional intro)
2. **Core Competencies & Key Technical Strengths**
3. **Hiring Recommendation** (why they stand out)
4. **Target Roles & Best Fit**

Return the output in clean, professional markdown. Avoid using candidate's contact details (email/phone) to maintain privacy.
"""
    try:
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Error generating client pitch: {e}")
        return f"Failed to generate client pitch: {e}"

def generate_boolean_sourcing(jd_text: str) -> str:
    """Generates optimized Boolean search query strings and sourcing strategy based on JD."""
    from config import get_ollama_client, OLLAMA_MODEL
    
    prompt = f"""
You are a senior talent sourcing specialist. Analyze the Job Description (JD) below and create a comprehensive Sourcing Blueprint.

Job Description:
{jd_text}

Provide:
1. **Target Job Titles**: (5 common variations)
2. **Boolean Search Queries**:
   - LinkedIn Search String (using OR, AND, site: etc)
   - Google X-Ray Search String (targeting LinkedIn profiles)
   - GitHub/Tech Search String
3. **Core Sourcing Channels**: (best places to search)
4. **Custom outreach icebreaker template**: (concise cold outreach message)

Return the output in a clean, professional markdown format.
"""
    try:
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Error generating boolean sourcing: {e}")
        return f"Failed to generate sourcing blueprint: {e}"

def generate_candidate_comparison(candidates: list) -> str:
    """Generates a side-by-side comparison battlecard for the selected candidates."""
    from config import get_ollama_client, OLLAMA_MODEL
    
    cand_summary = ""
    for i, c in enumerate(candidates):
        techs = c.get("technologies", [])
        tech_str = ", ".join(techs) if isinstance(techs, list) else "N/A"
        cand_summary += f"""
Candidate {i+1}:
- Name: {c.get('full_name', 'N/A')}
- Role: {c.get('working_role', 'N/A')}
- Experience: {c.get('total_experience_years', 0)} years
- Score: {c.get('resume_score', 0)}/100
- Technologies: {tech_str}
- Summary: {c.get('summary', 'N/A')}
"""

    prompt = f"""
You are an elite recruitment consultant. Create a side-by-side comparison Battlecard comparing the following candidates.

Candidates:
{cand_summary}

Structure your response into:
1. **Side-by-Side Comparison Matrix**: A markdown table comparing Name, Primary Role, Experience, Key Strengths, and Areas of Improvement.
2. **Detailed Fit Analysis**: Discuss the pros and cons of each candidate relative to each other.
3. **Hiring Verdict / Recommendation**: Give a clear, direct recommendation on which candidate is the best fit for senior roles vs specialized roles.

Return the output in clean, professional markdown.
"""
    try:
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Error generating candidate comparison: {e}")
        return f"Failed to generate candidate comparison battlecard: {e}"

def parse_natural_language_query(query: str) -> Dict[str, Any]:
    """Parses a natural language recruiter search query into structured search criteria."""
    from config import get_ollama_client, OLLAMA_MODEL
    
    prompt = f"""
You are an expert search query parser for a talent recruitment database. Parse the recruiter search query into JSON criteria.

Query: "{query}"

JSON Schema:
{{
  "role_keyword": "Primary job title keyword (or empty)",
  "skills": ["list of tech skills or languages mentioned (or empty)"],
  "min_experience": float (minimum experience years mentioned, default 0.0),
  "domain": "IT & Software" or "Digital Marketing" or "Design & Creative" or "Finance" or "Healthcare" or "HR" or "Sales" or "Other" (or empty if not mentioned)
}}

Return ONLY valid JSON. Keep it simple and accurate.
"""
    try:
        client = get_ollama_client()
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            format="json",
            options={"temperature": 0.0}
        )
        from core.json_parser import parse_ai_response
        result = parse_ai_response(response.get('response', ''))
        return result or {}
    except Exception as e:
        logger.error(f"Error parsing natural language search query: {e}")
        return {}

if __name__ == "__main__":
    # Quick manual test
    import os
    test_text = "John Doe is a Senior Software Engineer with 8 years of experience in React, Node.js and AWS."
    analysis = analyze_resume(test_text, "John_Doe_CV.pdf")
    print(json.dumps(analysis, indent=2))
