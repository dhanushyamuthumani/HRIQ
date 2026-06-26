import json
import re
from typing import Optional, Dict, Any

def clean_json_string(json_str: str) -> str:
    """Cleans the AI response to extract only the JSON part."""
    # Look for content between triple backticks if present (handling optional json label)
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_str, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Otherwise, try to find the first '{' and last '}'
    start = json_str.find('{')
    end = json_str.rfind('}')
    
    if start != -1 and end != -1:
        return json_str[start:end+1].strip()
    
    return json_str.strip()

def parse_ai_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parses the cleaned AI response string into a dictionary."""
    cleaned_str = clean_json_string(response_text)
    
    # Pre-parse cleaning for common LLM mistakes
    # 1. Remove trailing commas before closing braces/brackets
    cleaned_str = re.sub(r',\s*([\]\}])', r'\1', cleaned_str)
    
    try:
        return json.loads(cleaned_str)
    except json.JSONDecodeError as e:
        # Last ditch effort: try to fix common JSON errors without corrupting legitimate single quotes
        try:
            # 1. Try ast.literal_eval which handles python-style dicts with single quotes perfectly
            import ast
            return ast.literal_eval(cleaned_str)
        except:
            try:
                # 2. Conservative regex fallback for simple cases
                fixed_str = re.sub(r"'(.*?)':", r'"\1":', cleaned_str)
                fixed_str = re.sub(r":\s*'(.*?)'", r': "\1"', fixed_str)
                return json.loads(fixed_str)
            except:
                return None
        return None
