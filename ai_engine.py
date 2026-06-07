import os
import json
from groq import Groq

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        newline_idx = text.find("\n")
        if newline_idx != -1:
            text = text[newline_idx:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx+1]
    return text

def analyze_resume(resume_text, job_description, api_key, model_name="llama-3.3-70b-versatile"):
    """
    Sends resume text and job description to Groq to analyze ATS score, metrics, gaps, and improvements.
    Returns a structured dictionary of results.
    """
    if not api_key:
        raise ValueError("Groq API Key is required.")
        
    client = Groq(api_key=api_key)
    
    # Define a default job description if none provided to enable general ATS check
    if not job_description or not job_description.strip():
        job_description = "General professional role aligning with the candidate's core industry. Focus on standard ATS structure, clear formatting, quantifiable results, and professional representation."

    prompt = f"""
You are an expert ATS (Applicant Tracking System) algorithm, professional recruiter, and executive resume writer. 
Analyze the provided RESUME against the target JOB DESCRIPTION. 

RESUME:
\"\"\"
{resume_text}
\"\"\"

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

Perform an in-depth analysis and return a JSON object containing the evaluation. Ensure the JSON is valid and matches the format below. Do not add any markdown formatting (like ```json ... ```) or extra text, just output raw JSON content.

Expected JSON schema:
{{
  "overall_score": 85, // Integer out of 100
  "metrics": {{
    "keyword_match": 80, // Integer out of 100 (matching keywords from JD)
    "structure_formatting": 90, // Integer out of 100 (sections, margins, general parseability)
    "impact_quantification": 75, // Integer out of 100 (measuring achievements using metrics)
    "action_verbs": 85 // Integer out of 100 (usage of power verbs vs passive language)
  }},
  "key_findings": "Summary of overall resume strengths and critical issues...",
  "ats_checks": [
    {{
      "item": "Check name (e.g. Standard Contact Details, Core Section Headers, Page Length, Table/Graphic Usage, Font Standard)",
      "passed": true,
      "feedback": "Why it passed or how to fix it."
    }}
  ],
  "keyword_analysis": {{
    "matched": ["list", "of", "keywords", "present", "in", "both"],
    "missing": ["list", "of", "high-priority", "keywords", "from", "JD", "missing", "in", "resume"]
  }},
  "gap_analysis": {{
    "missing_hard_skills": ["essential", "technical", "skills", "tools", "or", "certifications", "missing"],
    "missing_soft_skills": ["soft", "skills", "or", "methodologies", "missing"],
    "experience_gaps": ["description of gaps in years, seniority level, domain knowledge, or responsibilities compared to JD requirements"]
  }},
  "bullet_point_improvements": [
    {{
      "original": "Original weak bullet point from the candidate's resume",
      "revised": "High-impact, keyword-optimized bullet point using the STAR (Situation-Task-Action-Result) format, showing quantifiable impact.",
      "reason": "Explanation of the correction (e.g., added specific metric, included missing keyword X, removed weak verb 'responsible for')"
    }}
  ]
}}
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a professional ATS analyzer that only outputs raw valid JSON in response."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model_name,
        response_format={"type": "json_object"}
    )
    
    response_text = chat_completion.choices[0].message.content
    cleaned_text = clean_json_response(response_text)
    
    try:
        data = json.loads(cleaned_text)
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse Groq JSON response. Raw output:\n{response_text}\nError: {str(e)}")

def generate_tailored_resume(resume_text, job_description, gaps_analysis, api_key, model_name="llama-3.3-70b-versatile"):
    """
    Directs Groq to rewrite the candidate's resume to match the JD, incorporating
    missing keywords, hard/soft skills, and STAR method bullets. Returns structured tailored resume JSON.
    """
    if not api_key:
        raise ValueError("Groq API Key is required.")
        
    client = Groq(api_key=api_key)
    
    if not job_description or not job_description.strip():
        job_description = "General professional role aligning with the candidate's core industry."

    prompt = f"""
You are an elite resume builder. You must rewrite the candidate's original resume to optimize it for the target Job Description and close identified gaps. 
Make sure you include relevant keywords naturally, use active language, restructure information chronologically, and rewrite accomplishments in the STAR format (with placeholder numbers/metrics if they were missing, format as '[insert metric, e.g., 20%]' to show the candidate where to fill in actual data).

ORIGINAL RESUME:
\"\"\"
{resume_text}
\"\"\"

TARGET JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

GAP ANALYSIS REPORT:
\"\"\"
{json.dumps(gaps_analysis, indent=2)}
\"\"\"

Generate a beautifully structured, tailored resume. You must output a JSON object adhering exactly to the structure below. Do not output any markdown formatting (like ```json ... ```) or extra text, just output raw JSON content.

Expected JSON schema:
{{
  "contact_info": {{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-123-456-7890",
    "location": "City, State",
    "linkedin": "linkedin.com/in/johndoe",
    "portfolio": "github.com/johndoe"
  }},
  "professional_summary": "A 3-4 sentence professional summary highlighting target role experience, key skills, and major value proposition matching the job description.",
  "skills": {{
    "technical_skills": ["Skill1", "Skill2", "Skill3"],
    "soft_skills": ["SkillA", "SkillB"],
    "tools_frameworks": ["ToolX", "ToolY"]
  }},
  "work_experience": [
    {{
      "job_title": "Software Engineer",
      "company": "Company Name",
      "location": "City, State",
      "dates": "Month Year - Month Year or Present",
      "bullet_points": [
        "Led development of [insert project name], leveraging [insert technology] which increased [insert performance metric, e.g., system speed] by [insert metric, e.g., 25%].",
        "Collaborated with cross-functional teams to integrate [insert feature], reducing [insert error rate, e.g., load times] by [insert metric, e.g., 15%]."
      ]
    }}
  ],
  "education": [
    {{
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University Name",
      "location": "City, State",
      "dates": "Year - Year",
      "gpa_or_honors": "GPA 3.8/4.0 or Cum Laude (optional)"
    }}
  ],
  "certifications": ["Certification 1", "Certification 2"],
  "projects": [
    {{
      "name": "Project Name",
      "role": "Lead Architect",
      "description": [
        "Designed and implemented X using Y, resolving scaling bottlenecks.",
        "Delivered project 2 weeks ahead of schedule, enabling client adoption."
      ]
    }}
  ]
}}
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a professional resume writer that only outputs raw valid JSON in response."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model_name,
        response_format={"type": "json_object"}
    )
    
    response_text = chat_completion.choices[0].message.content
    cleaned_text = clean_json_response(response_text)
    
    try:
        data = json.loads(cleaned_text)
        return data
    except Exception as e:
        raise ValueError(f"Failed to parse Groq tailored resume JSON response. Raw output:\n{response_text}\nError: {str(e)}")
