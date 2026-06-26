"""Script to append pipeline/interview endpoints to api.py"""

EXTRA = '''

# ─── RECRUITMENT PIPELINE & INTERVIEW LIFECYCLE ENDPOINTS ──────────────────

import json as _json
from pathlib import Path as _Path

_PIPELINE_FILE = _Path("outputs/pipeline.json")
_PIPELINE_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_pipeline():
    if _PIPELINE_FILE.exists():
        try:
            return _json.loads(_PIPELINE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_pipeline(data):
    _PIPELINE_FILE.write_text(_json.dumps(data, indent=2))


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
        "You are an HR professional. Write a formal interview invitation email.\\n"
        f"Candidate: {name}\\nRole: {role}\\nCompany: {company}\\n"
        "Include placeholders: [DATE], [TIME], [PLATFORM], [INTERVIEWER_NAME]\\n"
        "Max 200 words. Start with Subject: then body. Return ONLY the email text."
    )
    try:
        from config import get_ollama_client, OLLAMA_MODEL
        client = get_ollama_client()
        resp = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={"temperature": 0.3})
        email_text = resp.get("response", "").strip()
    except Exception:
        email_text = (
            f"Subject: Interview Invitation — {role} at {company}\\n\\n"
            f"Dear {name},\\n\\nWe are pleased to invite you for an interview for the {role} position at {company}.\\n\\n"
            "Interview Details:\\n- Date: [DATE]  |  Time: [TIME]\\n- Platform: [PLATFORM]\\n- Interviewer: [INTERVIEWER_NAME]\\n\\n"
            "Please confirm your availability.\\n\\nBest regards,\\nHRIQ Talent Team"
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
    pipeline["interviews"].append({
        "candidate_name": candidate_name,
        "role": role,
        "date": payload.get("date", ""),
        "time": payload.get("time", ""),
        "platform": payload.get("platform", ""),
        "interviewer": payload.get("interviewer", ""),
        "status": "Scheduled",
        "result": None,
        "score": None,
        "notes": ""
    })
    _save_pipeline(pipeline)
    return {"success": True, "interviews": pipeline["interviews"]}


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
        f"Create a structured interview scorecard for:\\n"
        f"Candidate: {name} | Role: {role} | Exp: {exp}y | Skills: {skills_str}\\n"
        "Create 6 evaluation dimensions with weights summing to 100%%, 2 tailored questions each, rating 1-5.\\n"
        "Return structured plain text."
    )
    try:
        from config import get_ollama_client, OLLAMA_MODEL
        client = get_ollama_client()
        resp = client.generate(model=OLLAMA_MODEL, prompt=prompt, options={"temperature": 0.4})
        scorecard = resp.get("response", "").strip()
    except Exception:
        scorecard = (
            f"INTERVIEW SCORECARD — {name} for {role}\\n"
            "=" * 44 + "\\n"
            "1. TECHNICAL SKILLS (30%)  Rating: _/5\\n"
            "   Q: Walk me through a complex system you built end-to-end.\\n"
            "   Q: How do you debug a critical production issue?\\n\\n"
            "2. PROBLEM SOLVING (20%)  Rating: _/5\\n"
            "   Q: Describe solving a problem with incomplete information.\\n"
            "   Q: What frameworks guide your technical decisions?\\n\\n"
            "3. COMMUNICATION (15%)  Rating: _/5\\n"
            "   Q: Explain a technical concept to a non-technical stakeholder.\\n"
            "   Q: Describe cross-functional teamwork experience.\\n\\n"
            "4. CULTURE FIT (15%)  Rating: _/5\\n"
            "   Q: What values matter most in a team environment?\\n"
            "   Q: How do you handle technical disagreements?\\n\\n"
            "5. DOMAIN KNOWLEDGE (10%)  Rating: _/5\\n"
            "   Q: What recent tech developments excite you most?\\n"
            "   Q: How do you stay current with emerging technologies?\\n\\n"
            "6. LEADERSHIP (10%)  Rating: _/5\\n"
            "   Q: Describe a time you led or mentored a technical initiative.\\n"
            "   Q: How do you prioritize under multiple deadlines?\\n\\n"
            "-" * 44 + "\\n"
            "TOTAL: _/5  |  Decision: [ ] Hire  [ ] Hold  [ ] Decline\\n"
            "NOTES: ___"
        )
    return {"scorecard": scorecard, "candidate_name": name, "role": role}
'''

with open("api.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove existing __main__ block
main_idx = content.rfind('\nif __name__ == "__main__":')
if main_idx != -1:
    content = content[:main_idx]

content = content.rstrip() + EXTRA + '''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
'''

with open("api.py", "w", encoding="utf-8") as f:
    f.write(content)

print("api.py updated successfully!")
print(f"Total lines: {len(content.splitlines())}")
