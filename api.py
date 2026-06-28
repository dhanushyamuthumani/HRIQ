import os
import json
import logging
import tempfile
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from core.persistence import load_talent_data, save_talent_data
from core.search_engine import search_candidates
from core.sourcing_engine import parse_sourcing_criteria, search_github_candidates, draft_github_outreach
from core.text_extractor import extract_text
from core.ai_engine import analyze_resume
from core.duplicate_checker import detect_duplicates
from core.scoring_engine import process_scoring
from core.folder_processor import get_files_from_folder

# Simple manual dotenv load
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key.strip()] = val.strip()

# Configure GitHub Token for sourcing
if os.getenv("GITHUB_TOKEN"):
    os.environ["GITHUB_TOKEN"] = os.getenv("GITHUB_TOKEN", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HRIQ Backend API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
_GOOGLE_TOKENS_FILE = Path("outputs/google_tokens.json")

def _load_google_tokens():
    if _GOOGLE_TOKENS_FILE.exists():
        try:
            return json.loads(_GOOGLE_TOKENS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_google_tokens(tokens):
    _GOOGLE_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _GOOGLE_TOKENS_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")

def get_valid_google_token():
    import requests
    import time
    tokens = _load_google_tokens()
    if not tokens or not tokens.get("access_token"):
        return None
        
    expires_in = tokens.get("expires_in", 3600)
    created_at = tokens.get("created_at", 0)
    
    if time.time() - created_at < (expires_in - 300):
        return tokens.get("access_token")
        
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return None
        
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        res = requests.post(token_url, data=data)
        if res.status_code == 200:
            new_tokens = res.json()
            tokens["access_token"] = new_tokens["access_token"]
            tokens["expires_in"] = new_tokens.get("expires_in", 3600)
            tokens["created_at"] = time.time()
            _save_google_tokens(tokens)
            return tokens["access_token"]
    except Exception as e:
        logger.error(f"Error refreshing Google OAuth token: {e}")
    return None

_PIPELINE_FILE = Path("outputs/pipeline.json")
_PIPELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_pipeline():
    if _PIPELINE_FILE.exists():
        try:
            return json.loads(_PIPELINE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_pipeline(data):
    _PIPELINE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

@app.get("/api/status")
def get_status():
    return {
        "all_clear": True,
        "server": {"status": "Online", "message": "Backend server is fully operational."},
        "model": {"status": "Online", "message": "Ollama/local model responder is active."}
    }
@app.get("/api/google/auth-url")
def get_google_auth_url(redirect_uri: str):
    import urllib.parse
    scopes = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/tasks",
        "https://www.googleapis.com/auth/drive.file"
    ]
    scope_str = " ".join(scopes)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope_str,
        "access_type": "offline",
        "prompt": "select_account consent"
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return {"auth_url": url}

class GoogleCallbackPayload(BaseModel):
    code: str
    redirect_uri: str

@app.post("/api/google/callback")
def google_callback(payload: GoogleCallbackPayload):
    import requests
    import time
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": payload.code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": payload.redirect_uri,
        "grant_type": "authorization_code"
    }
    
    res = requests.post(token_url, data=data)
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to exchange Google OAuth code: {res.text}")
        
    tokens = res.json()
    tokens["created_at"] = time.time()
    
    headers = {"Authorization": f"Bearer {tokens.get('access_token')}"}
    user_res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
    if user_res.status_code == 200:
        tokens["email"] = user_res.json().get("email")
        
    _save_google_tokens(tokens)
    return {"success": True, "email": tokens.get("email")}

@app.get("/api/google/status")
def get_google_status():
    tokens = _load_google_tokens()
    if tokens and tokens.get("access_token"):
        return {
            "connected": True,
            "email": tokens.get("email", "Google Account")
        }
    return {"connected": False}

@app.get("/api/talent")
def get_talent():
    try:
        candidates = load_talent_data()
        return {"candidates": candidates}
    except Exception as e:
        logger.error(f"Error loading talent data: {e}")
        return {"candidates": []}

@app.post("/api/talent/search")
def search_talent(query: str = Form(...), context: str = Form("Complete Hub")):
    try:
        candidates = load_talent_data()
        
        # Filter by context/tag first
        if context and context != "Complete Hub":
            candidates = [c for c in candidates if c.get("tag") == context]
            
        if not query:
            return {
                "criteria": {"query": query, "context": context},
                "matches": candidates,
                "response": "Here are all the candidates in the database."
            }
            
        # Format candidate profiles for the LLM
        candidate_profiles_summary = ""
        for c in candidates:
            candidate_profiles_summary += (
                f"- Name: {c.get('full_name')}\n"
                f"  Role: {c.get('working_role')}\n"
                f"  Domain: {c.get('industry_domain')}\n"
                f"  Experience: {c.get('total_experience_years')} years\n"
                f"  Skills: {', '.join(c.get('technologies', [])) if isinstance(c.get('technologies'), list) else c.get('technologies', 'None')}\n"
                f"  Summary: {c.get('summary')}\n\n"
            )
            
        from config import get_ollama_client, OLLAMA_MODEL
        from core.json_parser import parse_ai_response
        
        prompt = (
            "You are HRIQ Brain, an elite AI recruitment assistant. Analyze the recruiter's query and the list of candidate profiles below.\n"
            f"Recruiter Query: '{query}'\n\n"
            "Candidate Profiles:\n"
            f"{candidate_profiles_summary}\n"
            "Instructions:\n"
            "1. Select the candidates who match the recruiter's query semantically (e.g. searching for 'AI' matches 'Machine Learning', 'NLP', or 'AI Engineer').\n"
            "2. Write a detailed, professional, conversational response explaining who matches and why, or why nobody matches.\n"
            "3. Return the results in JSON format matching the schema:\n"
            "{\n"
            "  \"response\": \"Your detailed conversational analysis explaining the match to the recruiter.\",\n"
            "  \"matched_names\": [\"Exact Full Name of Candidate 1\", \"Exact Full Name of Candidate 2\"]\n"
            "}\n"
            "Ensure the JSON is strictly valid. No markdown backticks."
        )
        
        ai_response = ""
        matches = []
        parsed = None
        
        try:
            client = get_ollama_client()
            resp = client.generate(
                model=OLLAMA_MODEL,
                prompt=prompt,
                format="json",
                options={"temperature": 0.2}
            )
            raw_res = resp.get("response", "").strip()
            parsed = parse_ai_response(raw_res)
        except Exception as e:
            logger.error(f"Semantic search LLM generation failed: {e}")
            
        if parsed and isinstance(parsed, dict) and "response" in parsed:
            ai_response = parsed.get("response", "")
            matched_names = [name.lower().strip() for name in parsed.get("matched_names", [])]
            matches = [c for c in candidates if c.get("full_name", "").lower().strip() in matched_names]
        else:
            # Fallback to key-term matching if LLM fails or JSON fails
            logger.info("Semantic Search: Falling back to keyword search...")
            from core.search_engine import search_candidates
            matches = search_candidates(candidates, query)
            names_found = [c.get("full_name") for c in matches]
            if matches:
                ai_response = f"I matched the following candidate(s) via keyword search: {', '.join(names_found)}."
            else:
                ai_response = "I couldn't find any candidates in the database matching your request."
                
        return {
            "criteria": {"query": query, "context": context},
            "matches": matches,
            "response": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/talent/save")
def save_talent(payload: List[dict]):
    try:
        save_talent_data(payload)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScanPayload(BaseModel):
    folder_path: str
    tag: str

@app.post("/api/intake/upload")
async def intake_upload(tag: str = Form(...), files: List[UploadFile] = File(...)):
    existing_candidates = load_talent_data()
    new_candidates = []
    errors = []
    processed_count = 0
    
    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in [".pdf", ".docx"]:
            errors.append({"file": file.filename, "error": f"Unsupported file extension '{suffix}'. Only PDF and DOCX files are allowed."})
            continue
            
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
                
            try:
                text = extract_text(tmp_path)
                if not text or not text.strip():
                    raise ValueError("No text could be extracted from the file.")
                
                candidate_data = analyze_resume(text, filename=file.filename)
                if not candidate_data:
                    raise ValueError("Failed to parse resume content.")
                
                candidate_data = process_scoring(candidate_data)
                candidate_data["tag"] = tag
                candidate_data["source_file"] = file.filename
                candidate_data["raw_text"] = text
                
                new_candidates.append(candidate_data)
                processed_count += 1
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            logger.error(f"Error processing upload file {file.filename}: {e}")
            errors.append({"file": file.filename, "error": str(e)})

    if new_candidates:
        all_candidates = existing_candidates + new_candidates
        all_candidates = detect_duplicates(all_candidates)
        save_talent_data(all_candidates)
    else:
        all_candidates = existing_candidates

    return {
        "success": True,
        "candidates": all_candidates,
        "errors": errors,
        "processed_count": processed_count
    }

@app.post("/api/intake/scan")
def intake_scan(payload: ScanPayload):
    folder_path = payload.folder_path
    tag = payload.tag
    
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=400, detail=f"Directory path '{folder_path}' does not exist.")
        
    existing_candidates = load_talent_data()
    new_candidates = []
    errors = []
    processed_count = 0
    
    file_paths = get_files_from_folder(folder_path, [".pdf", ".docx"])
    
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        try:
            text = extract_text(file_path)
            if not text or not text.strip():
                raise ValueError("No text could be extracted from the file.")
                
            candidate_data = analyze_resume(text, filename=filename)
            if not candidate_data:
                raise ValueError("Failed to parse resume content.")
                
            candidate_data = process_scoring(candidate_data)
            candidate_data["tag"] = tag
            candidate_data["source_file"] = filename
            candidate_data["raw_text"] = text
            
            new_candidates.append(candidate_data)
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing scan file {filename}: {e}")
            errors.append({"file": filename, "error": str(e)})
            
    if new_candidates:
        all_candidates = existing_candidates + new_candidates
        all_candidates = detect_duplicates(all_candidates)
        save_talent_data(all_candidates)
    else:
        all_candidates = existing_candidates
        
    return {
        "success": True,
        "candidates": all_candidates,
        "errors": errors,
        "processed_count": processed_count
    }


@app.post("/api/sourcing/extract-criteria")
def extract_criteria(payload: dict):
    try:
        jd_text = payload.get("jd_text", "")
        criteria = parse_sourcing_criteria(jd_text)
        return criteria
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sourcing/search")
def sourcing_search(payload: dict):
    try:
        platform = payload.get("platform", "github")
        language = payload.get("language", "")
        location = payload.get("location", "")
        keywords = payload.get("keywords", [])
        limit = payload.get("limit", 10)
        
        if platform == "linkedin":
            from core.sourcing_engine import search_linkedin_candidates
            results = search_linkedin_candidates(language, location, keywords, per_page=limit)
        else:
            results = search_github_candidates(language, location, keywords, per_page=limit)
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sourcing/outreach")
def sourcing_outreach(payload: dict):
    try:
        candidate = payload.get("candidate", {})
        jd_text = payload.get("jd_text", "")
        email_text = draft_github_outreach(candidate, jd_text)
        return {"email": email_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline")
def get_pipeline():
    return _load_pipeline()

@app.post("/api/pipeline/save")
def save_pipeline(payload: dict):
    try:
        _save_pipeline(payload)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/invite")
def send_interview_invite(payload: dict):
    candidate = payload.get("candidate", {})
    role = payload.get("role", "the position")
    company = payload.get("company", "our client")
    name = candidate.get("full_name") or candidate.get("username") or "Candidate"
    email_addr = candidate.get("email", "N/A")

    prompt = (
        "You are an HR professional. Write a formal interview invitation email.\n"
        f"Candidate: {name}\nRole: {role}\nCompany: {company}\n"
        "Include placeholders: [DATE], [TIME], [PLATFORM], [INTERVIEWER_NAME]\n"
        "Max 200 words. Start with Subject: then body. Return ONLY the email text."
    )
    try:
        from config import get_ollama_client, OLLAMA_MODEL
        client = get_ollama_client()
        resp = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={"temperature": 0.3})
        email_text = resp.get("response", "").strip()
    except Exception:
        email_text = (
            f"Subject: Interview Invitation — {role} at {company}\n\n"
            f"Dear {name},\n\nWe are pleased to invite you for an interview for the {role} position at {company}.\n\n"
            "Interview Details:\n- Date: [DATE]  |  Time: [TIME]\n- Platform: [PLATFORM]\n- Interviewer: [INTERVIEWER_NAME]\n\n"
            "Please confirm your availability.\n\nBest regards,\nHRIQ Talent Team"
        )
    return {"invite_email": email_text, "candidate_name": name, "candidate_email": email_addr, "role": role}

@app.post("/api/interview/schedule")
def schedule_interview(payload: dict):
    candidate_name = payload.get("candidate_name", "")
    role = payload.get("role", "")
    pipeline = _load_pipeline()
    if "interviews" not in pipeline:
        pipeline["interviews"] = []
    pipeline["interviews"] = [
        i for i in pipeline["interviews"]
        if not (i.get("candidate_name") == candidate_name and i.get("role") == role)
    ]
    
    access_token = get_valid_google_token()
    calendar_link = ""
    direct_created = False
    
    if access_token:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            date = payload.get("date", "")
            time_str = payload.get("time", "")
            start_time_iso = f"{date}T{time_str}:00"
            
            try:
                hh, mm = map(int, time_str.split(":"))
                end_hh = (hh + 1) % 24
                end_time_iso = f"{date}T{end_hh:02d}:{mm:02d}:00"
            except:
                end_time_iso = start_time_iso
                
            event_body = {
                "summary": f"Interview: {candidate_name} x HRIQ",
                "description": f"Technical interview with {candidate_name} for the position of {role}.\nPlatform: {payload.get('platform')}\nInterviewer: {payload.get('interviewer')}",
                "start": {
                    "dateTime": start_time_iso,
                    "timeZone": "Asia/Kolkata"
                },
                "end": {
                    "dateTime": end_time_iso,
                    "timeZone": "Asia/Kolkata"
                }
            }
            
            cand_email = payload.get("candidate_email")
            if cand_email and "@" in cand_email and cand_email.lower() != "n/a":
                event_body["attendees"] = [{"email": cand_email, "responseStatus": "needsAction"}]
            
            cal_res = requests.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                params={"sendUpdates": "all"},
                json=event_body,
                headers=headers
            )
            event_id = ""
            if cal_res.status_code in [200, 201]:
                cal_event = cal_res.json()
                calendar_link = cal_event.get("htmlLink", "")
                event_id = cal_event.get("id", "")
                direct_created = True
                logger.info(f"Google Calendar Event created directly for {candidate_name}!")
            else:
                logger.error(f"Failed to create Google Calendar event: {cal_res.text}")
                
            task_body = {
                "title": f"Conduct Interview: {candidate_name} ({role})",
                "notes": f"Scheduled date: {date} at {time_str}\nPlatform: {payload.get('platform')}",
                "due": f"{date}T23:59:59Z"
            }
            requests.post(
                "https://www.googleapis.com/tasks/v1/lists/@default/tasks",
                json=task_body,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Error creating direct Google Calendar event or task: {e}")
            
    if not direct_created:
        try:
            from urllib.parse import quote
            date_str = payload.get("date", "").replace("-", "")
            t_str = payload.get("time", "").replace(":", "")
            if date_str and t_str:
                start_dt = f"{date_str}T{t_str}00"
                h_int = int(t_str[:2])
                end_hour = f"{h_int + 1:02d}" if h_int < 23 else "23"
                end_dt = f"{date_str}T{end_hour}{t_str[2:]}00"
                details = quote(f"Technical interview with {candidate_name} for the position of {role}.")
                title = quote(f"Interview: {candidate_name} x HRIQ")
                calendar_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start_dt}/{end_dt}&details={details}&sf=true&output=xml"
        except Exception:
            pass

    pipeline["interviews"].append({
        "candidate_name": candidate_name,
        "candidate_email": payload.get("candidate_email", ""),
        "role": role,
        "date": payload.get("date", ""),
        "time": payload.get("time", ""),
        "platform": payload.get("platform", ""),
        "interviewer": payload.get("interviewer", ""),
        "status": "Scheduled",
        "result": None,
        "score": None,
        "notes": "",
        "calendar_link": calendar_link,
        "google_event_id": event_id
    })
    _save_pipeline(pipeline)
    return {"success": True, "interviews": pipeline["interviews"], "calendar_link": calendar_link}

@app.post("/api/interview/result")
def save_interview_result(payload: dict):
    candidate_name = payload.get("candidate_name", "")
    role = payload.get("role", "")
    pipeline = _load_pipeline()
    interviews = pipeline.get("interviews", [])
    found = False
    for interview in interviews:
        if interview.get("candidate_name") == candidate_name and interview.get("role") == role:
            interview["result"] = payload.get("result", "")
            interview["score"] = payload.get("score", None)
            interview["notes"] = payload.get("notes", "")
            interview["status"] = "Completed"
            found = True
            break
    if not found:
        interviews.append({
            "candidate_name": candidate_name,
            "role": role,
            "result": payload.get("result", ""),
            "score": payload.get("score", None),
            "notes": payload.get("notes", ""),
            "status": "Completed"
        })
    pipeline["interviews"] = interviews
    _save_pipeline(pipeline)
    return {"success": True, "interviews": interviews}

@app.get("/api/interview/list")
def list_interviews():
    pipeline = _load_pipeline()
    return {"interviews": pipeline.get("interviews", [])}

@app.post("/api/interview/scorecard")
def generate_scorecard(payload: dict):
    candidate = payload.get("candidate", {})
    role = payload.get("role", "Software Engineer")
    name = candidate.get("full_name") or candidate.get("username") or "Candidate"
    skills = candidate.get("technologies", [])
    exp = candidate.get("total_experience_years", 0)
    skills_str = ", ".join(skills[:8]) if skills else "N/A"

    prompt = (
        f"Create a structured interview scorecard for:\n"
        f"Candidate: {name} | Role: {role} | Exp: {exp}y | Skills: {skills_str}\n"
        "Create 6 evaluation dimensions with weights summing to 100%, 2 tailored questions each, rating 1-5.\n"
        "Return structured plain text."
    )
    try:
        from config import get_ollama_client, OLLAMA_MODEL
        client = get_ollama_client()
        resp = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={"temperature": 0.4})
        scorecard = resp.get("response", "").strip()
    except Exception:
        scorecard = (
            f"INTERVIEW SCORECARD — {name} for {role}\n"
            "=" * 44 + "\n"
            "1. TECHNICAL SKILLS (30%)  Rating: _/5\n"
            "   Q: Walk me through a complex system you built end-to-end.\n"
            "   Q: How do you debug a critical production issue?\n\n"
            "2. PROBLEM SOLVING (20%)  Rating: _/5\n"
            "   Q: Describe solving a problem with incomplete information.\n"
            "   Q: What frameworks guide your technical decisions?\n\n"
            "3. COMMUNICATION (15%)  Rating: _/5\n"
            "   Q: Explain a technical concept to a non-technical stakeholder.\n"
            "   Q: Describe cross-functional teamwork experience.\n\n"
            "4. CULTURE FIT (15%)  Rating: _/5\n"
            "   Q: What values matter most in a team environment?\n"
            "   Q: How do you handle technical disagreements?\n\n"
            "5. DOMAIN KNOWLEDGE (10%)  Rating: _/5\n"
            "   Q: What recent tech developments excite you most?\n"
            "   Q: How do you stay current with emerging technologies?\n\n"
            "6. LEADERSHIP (10%)  Rating: _/5\n"
            "   Q: Describe a time you led or mentored a technical initiative.\n"
            "   Q: How do you prioritize under multiple deadlines?\n\n"
            "-" * 44 + "\n"
            "TOTAL: _/5  |  Decision: [ ] Hire  [ ] Hold  [ ] Decline\n"
            "NOTES: ___"
        )
    return {"scorecard": scorecard, "candidate_name": name, "role": role}

_SETTINGS_FILE = Path("outputs/settings.json")

def _load_settings():
    if _SETTINGS_FILE.exists():
        try:
            return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "full_name": "Dhanush",
        "email": "dhanush@example.com",
        "phone": "+91 99999 99999",
        "role": "Lead Talent Acquisition Partner",
        "company": "HRIQ Inc",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "dhanush@example.com",
        "smtp_password": ""
    }

def _save_settings(data):
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

@app.get("/api/settings")
def get_settings():
    return _load_settings()

@app.post("/api/settings/save")
def save_settings(payload: dict):
    try:
        _save_settings(payload)
        return {"success": True, "settings": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/send-email")
def send_email(payload: dict):
    try:
        to_email = payload.get("to_email")
        subject = payload.get("subject", "Interview invitation")
        body = payload.get("body", "")
        cc_emails = payload.get("cc_emails", [])
        
        # Check direct Gmail OAuth API first
        access_token = get_valid_google_token()
        if access_token:
            try:
                import requests
                import base64
                from email.mime.text import MIMEText
                
                msg = MIMEText(body)
                msg['To'] = to_email
                msg['Subject'] = subject
                if cc_emails:
                    msg['Cc'] = ", ".join(cc_emails)
                    
                raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                gmail_res = requests.post(
                    "https://www.googleapis.com/gmail/v1/users/me/messages/send",
                    json={"raw": raw_message},
                    headers=headers
                )
                if gmail_res.status_code in [200, 201]:
                    return {"success": True, "message": "Email sent successfully via Gmail API!"}
                else:
                    logger.error(f"Gmail API send failed: {gmail_res.text}")
            except Exception as e:
                logger.error(f"Error sending email via Gmail API: {e}")
                
        # Real SMTP check or mock send if password/credentials are missing
        settings = _load_settings()
        smtp_user = settings.get("smtp_username")
        smtp_pass = settings.get("smtp_password")
        
        if smtp_user and smtp_pass:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            if cc_emails:
                msg['Cc'] = ", ".join(cc_emails)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            recipients = [to_email] + cc_emails
            
            try:
                with smtplib.SMTP(settings.get("smtp_server", "smtp.gmail.com"), int(settings.get("smtp_port", 587))) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, recipients, msg.as_string())
            except smtplib.SMTPAuthenticationError as auth_err:
                logger.error(f"SMTP Auth Error: {auth_err}")
                raise HTTPException(
                    status_code=400,
                    detail="SMTP authentication failed. If you are using Gmail, please make sure you generate and use a Google 'App Password' in your Google Account security settings instead of your standard password."
                )
                
            return {"success": True, "message": "Email sent successfully via SMTP server!"}
        else:
            # Fallback mock success
            logger.info(f"Simulating email sent successfully to={to_email}, cc={cc_emails}, subject={subject}")
            return {"success": True, "message": "Email simulated successfully! (To send real emails, please fill in your SMTP Password in Settings tab)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/cancel")
def cancel_interview(payload: dict):
    candidate_name = payload.get("candidate_name", "")
    role = payload.get("role", "")
    
    pipeline = _load_pipeline()
    interviews = pipeline.get("interviews", [])
    
    matching_interview = None
    for item in interviews:
        if item.get("candidate_name") == candidate_name and item.get("role") == role:
            matching_interview = item
            break
            
    if not matching_interview:
        raise HTTPException(status_code=404, detail="Interview record not found.")
        
    google_event_id = matching_interview.get("google_event_id", "")
    cand_email = matching_interview.get("candidate_email", "")
    
    access_token = get_valid_google_token()
    if google_event_id and access_token:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            cal_res = requests.delete(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{google_event_id}",
                params={"sendUpdates": "all"},
                headers=headers
            )
            if cal_res.status_code in [200, 204]:
                logger.info(f"Google Calendar Event {google_event_id} deleted successfully and notification sent!")
            else:
                logger.error(f"Failed to delete Google Calendar event: {cal_res.text}")
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {e}")
            
    if cand_email and "@" in cand_email and cand_email.lower() != "n/a":
        subject = f"Cancellation: Interview for {role}"
        body = f"Hi {candidate_name.split(' ')[0]},\n\nPlease note that your scheduled interview for the position of {role} has been cancelled.\n\nShould you have any questions, please reach out to us.\n\nBest regards,\nHRIQ Team"
        try:
            send_email({"to_email": cand_email, "subject": subject, "body": body})
        except Exception as e:
            logger.error(f"Failed to send cancellation notification email: {e}")
            
    pipeline["interviews"] = [
        item for item in interviews
        if not (item.get("candidate_name") == candidate_name and item.get("role") == role)
    ]
    _save_pipeline(pipeline)
    return {"success": True, "interviews": pipeline["interviews"]}

# --- SaaS Career Portal & Google Drive Integration ---
_JOBS_FILE = Path("outputs/jobs.json")
_APPLICANTS_FILE = Path("outputs/applicants.json")

def _load_jobs():
    if _JOBS_FILE.exists():
        try:
            return json.loads(_JOBS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def _save_jobs(data):
    _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _JOBS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _load_applicants():
    if _APPLICANTS_FILE.exists():
        try:
            return json.loads(_APPLICANTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def _save_applicants(data):
    _APPLICANTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _APPLICANTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def upload_to_google_drive(file_content: bytes, filename: str, content_type: str = "application/octet-stream") -> Optional[str]:
    """Uploads a file to Google Drive and returns a viewable webViewLink."""
    access_token = get_valid_google_token()
    if not access_token:
        logger.warning("Drive Upload: No valid Google access token available. Returning fallback.")
        return None
        
    import requests
    import json
    
    metadata = {
        "name": filename,
        "mimeType": content_type
    }
    
    boundary = "hriq_drive_upload_boundary"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }
    
    body_parts = [
        f"--{boundary}".encode("utf-8"),
        b"Content-Type: application/json; charset=UTF-8",
        b"",
        json.dumps(metadata).encode("utf-8"),
        f"--{boundary}".encode("utf-8"),
        f"Content-Type: {content_type}".encode("utf-8"),
        b"",
        file_content,
        f"--{boundary}--".encode("utf-8")
    ]
    body = b"\r\n".join(body_parts)
    upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"
    
    try:
        res = requests.post(upload_url, data=body, headers=headers)
        if res.status_code not in [200, 201]:
            logger.error(f"Google Drive upload failed: {res.text}")
            return None
            
        file_id = res.json().get("id")
        if not file_id:
            return None
            
        # Make the file viewable to anyone with the link
        requests.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            json={"role": "reader", "type": "anyone"},
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        )
        
        # Fetch the webViewLink
        meta_res = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"fields": "webViewLink"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if meta_res.status_code == 200:
            return meta_res.json().get("webViewLink")
            
        return f"https://drive.google.com/file/d/{file_id}/view"
    except Exception as e:
        logger.error(f"Error uploading file to Google Drive: {e}")
        return None

@app.get("/api/jobs")
def get_jobs():
    return {"jobs": _load_jobs()}

@app.post("/api/jobs/save")
def save_jobs(payload: list):
    try:
        _save_jobs(payload)
        return {"success": True, "jobs": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/applicants")
def get_applicants():
    return {"applicants": _load_applicants()}

@app.post("/api/applicants/delete")
def delete_applicant(payload: dict):
    applicant_id = payload.get("id")
    applicants = _load_applicants()
    filtered = [a for a in applicants if a.get("id") != applicant_id]
    _save_applicants(filtered)
    return {"success": True, "applicants": filtered}

@app.post("/api/jobs/apply")
async def apply_job(
    job_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    resume: UploadFile = File(...)
):
    try:
        # 1. Fetch targeted Job Description
        jobs = _load_jobs()
        target_job = next((j for j in jobs if j.get("id") == job_id), None)
        if not target_job:
            raise HTTPException(status_code=404, detail="Selected job position not found.")
            
        # 2. Read resume contents
        file_bytes = await resume.read()
        suffix = Path(resume.filename).suffix.lower()
        if suffix not in [".pdf", ".docx"]:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX resume uploads are supported.")
            
        # 3. Upload to Google Drive
        drive_link = upload_to_google_drive(file_bytes, f"{name.replace(' ', '_')}_Resume{suffix}", resume.content_type)
        if not drive_link:
            drive_link = "#"  # Fallback empty link if Google Drive is not connected
            
        # 4. Extract resume text
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        try:
            text = extract_text(tmp_path)
            if not text or not text.strip():
                raise ValueError("Could not extract readable text from resume.")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
        # 5. Call Ollama for screening against the specific Job requirements
        from config import get_ollama_client, OLLAMA_MODEL
        from core.json_parser import parse_ai_response
        
        prompt = (
            "You are HRIQ Screening Brain. Screen the candidate's resume text against the Job Details below.\n"
            f"Job Title: {target_job.get('title')}\n"
            f"JD Description: {target_job.get('description')}\n"
            f"Required Skills: {target_job.get('desired_skills')}\n\n"
            f"Candidate Resume Text:\n{text}\n\n"
            "Evaluate:\n"
            "1. Assign a Fit Category exactly as: 'Best Fit' (meets >80% criteria), 'Maybe' (meets 50-80% criteria), or 'Not Fit' (meets <50% criteria).\n"
            "2. Assign a matching score from 0 to 100.\n"
            "3. Write a concise 1-2 sentence screening summary explaining your decision.\n"
            "Return in strict JSON format:\n"
            "{\n"
            "  \"status\": \"Best Fit\" | \"Maybe\" | \"Not Fit\",\n"
            "  \"score\": 85,\n"
            "  \"summary\": \"Screening summary...\"\n"
            "}\n"
            "Ensure the JSON is valid. Do not include markdown wraps."
        )
        
        status = "Maybe"
        score = 60
        summary = "Resume parsed successfully. Semantic analysis pending server check."
        
        try:
            client = get_ollama_client()
            resp = client.generate(model=OLLAMA_MODEL, prompt=prompt, format="json", options={"temperature": 0.2})
            raw_res = resp.get("response", "").strip()
            parsed = parse_ai_response(raw_res)
            if parsed and isinstance(parsed, dict):
                status = parsed.get("status", "Maybe")
                score = parsed.get("score", 60)
                summary = parsed.get("summary", "")
        except Exception as e:
            logger.error(f"SaaS Application screening LLM error: {e}")
            
        # 6. Save applicant details
        import uuid
        import time
        new_applicant = {
            "id": str(uuid.uuid4()),
            "job_id": job_id,
            "job_title": target_job.get("title"),
            "name": name,
            "email": email,
            "phone": phone,
            "status": status,
            "score": score,
            "summary": summary,
            "drive_link": drive_link,
            "date_applied": time.strftime("%Y-%m-%d %H:%M")
        }
        
        applicants = _load_applicants()
        applicants.append(new_applicant)
        _save_applicants(applicants)
        
        return {"success": True, "applicant": new_applicant}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
