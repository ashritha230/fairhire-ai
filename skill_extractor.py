SKILLS_DB = [
    # Programming languages
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
    # Frameworks
    'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', '.net',
    # Databases
    'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite',
    # Tools
    'docker', 'kubernetes', 'aws', 'azure', 'git', 'jenkins'
]

def extract_skills(text: str) -> list:
    """Extract skills from text using keyword matching"""
    text_lower = text.lower()
    found_skills = []
    
    for skill in SKILLS_DB:
        if skill in text_lower and skill not in found_skills:
            found_skills.append(skill)
    
    return found_skills[:10]  # Top 10 skills
