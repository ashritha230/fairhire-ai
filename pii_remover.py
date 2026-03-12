import re
from typing import List

PHONE_REGEX = r'[\+]?[1-9][\d]{0,15}'
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
NAME_PATTERNS = [
    r'^\s*[A-Z][a-z]+ [A-Z][a-z]+\s*$',  # Common name patterns
    r'\b[A-Z][a-z]{2,20}\s+[A-Z][a-z]{2,20}\b',
]

def remove_pii(text: str) -> str:
    """Remove PII from resume text"""
    cleaned = text
    
    # Remove phone numbers
    cleaned = re.sub(PHONE_REGEX, '[PHONE]', cleaned)
    
    # Remove emails
    cleaned = re.sub(EMAIL_REGEX, '[EMAIL]', cleaned, flags=re.IGNORECASE)
    
    # Remove potential names (basic heuristic)
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that look like just names/contact info
        if len(line.strip()) < 50 and any(pattern in line for pattern in ['[PHONE]', '[EMAIL]']):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
