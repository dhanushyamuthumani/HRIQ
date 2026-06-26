import requests
import re
import os
import logging
from typing import List, Dict, Any
from config import get_ollama_client, OLLAMA_MODEL

logger = logging.getLogger(__name__)

# Optional GitHub token for higher rate limits (set GITHUB_TOKEN env var)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def _github_headers() -> Dict[str, str]:
    headers = {"User-Agent": "HRIQ-Recruiter-App"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def parse_sourcing_criteria(jd_text: str) -> Dict[str, Any]:
    """Uses LLM to extract primary programming language and target keywords for GitHub sourcing from a JD."""
    prompt = f"""
You are an expert technical sourcer. Analyze the Job Description (JD) below and extract parameters to search GitHub for matching developers.

Job Description:
{jd_text}

JSON Schema output:
{{
  "primary_language": "The single most important programming language (e.g. 'Python', 'TypeScript', 'Go', 'Rust', 'Java', 'C++', 'Ruby') or empty string if not clear",
  "keywords": ["list of 2-3 key technologies or tools, e.g., 'React', 'Kubernetes'"],
  "suggested_location": "A target location if mentioned, or empty string"
}}

Return ONLY valid JSON.
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
        if result and (result.get("primary_language") or result.get("keywords")):
            return result
    except Exception as e:
        logger.error(f"Error parsing sourcing criteria from LLM: {e}")

    # Fallback: simple keyword extraction from JD text
    lang_map = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "java": "Java", "go": "Go", "rust": "Rust", "c++": "C++", "c#": "C#",
        "ruby": "Ruby", "php": "PHP", "swift": "Swift", "kotlin": "Kotlin"
    }
    jd_lower = jd_text.lower()
    detected_lang = ""
    for key, val in lang_map.items():
        if key in jd_lower:
            detected_lang = val
            break
    loc_words = [
        "hyderabad", "bangalore", "chennai", "mumbai", "delhi", "pune", "remote",
        "london", "new york", "san francisco", "berlin", "singapore", "kolkata"
    ]
    detected_loc = ""
    for loc in loc_words:
        if loc in jd_lower:
            detected_loc = loc.title()
            break
    return {"primary_language": detected_lang, "keywords": [], "suggested_location": detected_loc}


def search_github_candidates(language: str, location: str, keywords: List[str] = None, per_page: int = 10) -> List[Dict[str, Any]]:
    """Searches GitHub API for developers matching criteria and retrieves detailed profiles."""
    query_parts = []
    if location:
        query_parts.append(f'location:"{location}"')
    if language:
        query_parts.append(f'language:"{language}"')
    if keywords:
        for kw in keywords:
            if kw:
                query_parts.append(kw)

    if not query_parts:
        logger.warning("No search criteria provided for GitHub sourcing.")
        return []

    query_str = " ".join(query_parts)
    url = "https://api.github.com/search/users"
    params = {"q": query_str, "per_page": min(per_page, 30), "sort": "followers", "order": "desc"}
    headers = _github_headers()

    try:
        response = requests.get(url, params=params, headers=headers, timeout=12)
        if response.status_code == 403:
            logger.error("GitHub API rate limit exceeded. Set GITHUB_TOKEN env var for higher limits.")
            return []
        if response.status_code != 200:
            logger.error(f"GitHub Search API returned {response.status_code}: {response.text[:300]}")
            return []

        data = response.json()
        items = data.get("items", [])
        candidates = []

        for item in items[:per_page]:
            user_url = item.get("url")
            if not user_url:
                continue
            try:
                detail_res = requests.get(user_url, headers=headers, timeout=6)
                if detail_res.status_code == 200:
                    u = detail_res.json()
                    candidates.append({
                        "username": u.get("login"),
                        "full_name": u.get("name") or u.get("login"),
                        "avatar_url": u.get("avatar_url"),
                        "profile_url": u.get("html_url"),
                        "bio": u.get("bio") or "No bio provided.",
                        "company": u.get("company") or "N/A",
                        "location": u.get("location") or location or "N/A",
                        "email": u.get("email") or "N/A",
                        "public_repos": u.get("public_repos", 0),
                        "followers": u.get("followers", 0),
                        "blog": u.get("blog") or "N/A"
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch detail for {user_url}: {e}")
                continue

        return candidates
    except Exception as e:
        logger.error(f"Error in search_github_candidates: {e}")
        return []


def draft_github_outreach(candidate_data: Dict[str, Any], jd_text: str = None) -> str:
    """Uses LLM to draft a highly personalized cold email/message referencing their GitHub work."""
    context = f"""
Candidate Info:
- Name: {candidate_data.get('full_name')}
- Username: {candidate_data.get('username')}
- Bio: {candidate_data.get('bio')}
- Company: {candidate_data.get('company')}
- Public Repos: {candidate_data.get('public_repos')}
- Followers: {candidate_data.get('followers')}
"""
    if jd_text:
        context += f"\nTarget Job Description:\n{jd_text}"

    prompt = f"""
You are an elite technical recruiter. Write a short, highly personalized cold outreach email to the developer.
Reference their GitHub profile info, and briefly pitch the target role.

{context}

Rules:
1. Make it stand out — NO generic templates. Mention they have {candidate_data.get('public_repos')} public repos.
2. Keep it under 150 words.
3. Be professional, friendly, and low-pressure.
4. Include placeholders: [MEETING_LINK] and [DATE].
5. Format: Subject: ... then the email body.

Return ONLY the outreach message text.
"""
    try:
        client = get_ollama_client()
        response = client.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response.get('response', '').strip()
    except Exception as e:
        logger.error(f"Error drafting outreach: {e}")
        name = candidate_data.get('full_name', 'there')
        repos = candidate_data.get('public_repos', 0)
        return f"""Subject: Exciting Opportunity for {name}

Hi {name},

I came across your GitHub profile and was genuinely impressed by your {repos} public repositories. Your technical depth stands out, and I believe you could be an exceptional fit for a role we're working on.

I'd love to share more details in a quick 15-minute conversation.

[MEETING_LINK] | [DATE]

Looking forward to connecting!

Best regards,
HRIQ Recruitment Team"""


def search_linkedin_candidates(language: str, location: str, keywords: List[str] = None, per_page: int = 10) -> List[Dict[str, Any]]:
    """Searches Google via SerpAPI to locate LinkedIn developer profiles matching criteria."""
    serp_api_key = os.environ.get("SERPAPI_KEY", "db55e1933b785d2374852be1500ef396ec92a576099a894fa43e5cda2cefd0e8")
    if not serp_api_key:
        logger.error("No SERPAPI_KEY configured.")
        return []

    # Construct clean site search query for LinkedIn profiles
    query_parts = ["site:linkedin.com/in/"]
    if language:
        query_parts.append(f'"{language}"')
    if location:
        query_parts.append(f'"{location}"')
    if keywords:
        for kw in keywords:
            if kw:
                query_parts.append(f'"{kw}"')

    query_str = " ".join(query_parts)
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query_str,
        "api_key": serp_api_key,
        "num": min(per_page, 20)
    }

    try:
        response = requests.get(url, params=params, timeout=12)
        if response.status_code != 200:
            logger.error(f"SerpAPI returned status {response.status_code}: {response.text[:300]}")
            return []

        data = response.json()
        results = data.get("organic_results", [])
        candidates = []

        for item in results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            profile_url = item.get("link", "")
            
            # Extract name and headline/role from Google title e.g. "John Doe - Senior Developer - Company | LinkedIn"
            name = title.split("-")[0].strip() if "-" in title else title
            if " | LinkedIn" in name:
                name = name.replace(" | LinkedIn", "").strip()
            
            headline = "No headline provided."
            parts = title.split("-")
            if len(parts) > 1:
                headline = " - ".join(parts[1:]).replace(" | LinkedIn", "").strip()

            username = profile_url.split("/in/")[-1].replace("/", "").strip() if "/in/" in profile_url else "linkedin_user"

            # Parse experience heuristic from snippet if possible
            exp_match = re.search(r"(\d+)\+?\s*years?", snippet, re.IGNORECASE)
            exp_years = float(exp_match.group(1)) if exp_match else 0.0

            candidates.append({
                "username": username,
                "full_name": name,
                "avatar_url": None, # LinkedIn avatars require auth/scraping, fallback to null/placeholder
                "profile_url": profile_url,
                "bio": snippet or headline,
                "company": "N/A",
                "location": location or "N/A",
                "email": "N/A", # Public search index doesn't expose emails directly
                "experience_years": f"{exp_years}y" if exp_years > 0 else "N/A",
                "domain": language or "Software Engineering"
            })
        return candidates
    except Exception as e:
        logger.error(f"Error in search_linkedin_candidates: {e}")
        return []

