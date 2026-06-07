import os
import base64
import streamlit as st
import streamlit.components.v1 as components
import json
import re
from dotenv import load_dotenv

# Import helper modules
import parser
import ai_engine
import exporter
from templates import TEMPLATES

# Load environment variables
load_dotenv(override=True)

# Page config
st.set_page_config(
    page_title="ATSify — AI Resume Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS stylesheet
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("Custom CSS file not found.")

load_css("style.css")

# --- SESSION STATE INITIALIZATION ---
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "tailored_resume" not in st.session_state:
    st.session_state.tailored_resume = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = ""
if "selected_template" not in st.session_state or st.session_state.selected_template not in TEMPLATES:
    st.session_state.selected_template = "executive_elite"
if "zoom_pct" not in st.session_state:
    st.session_state.zoom_pct = 100
if "filter_category" not in st.session_state:
    st.session_state.filter_category = "All"

# Custom Template States (Allows customization overrides)
if "custom_primary_color" not in st.session_state:
    st.session_state.custom_primary_color = None
if "custom_font" not in st.session_state:
    st.session_state.custom_font = None
if "custom_margin" not in st.session_state:
    st.session_state.custom_margin = None
if "custom_layout" not in st.session_state:
    st.session_state.custom_layout = None
if "custom_accent_style" not in st.session_state:
    st.session_state.custom_accent_style = None
if "custom_density" not in st.session_state:
    st.session_state.custom_density = None
if "include_profile_photo" not in st.session_state:
    st.session_state.include_profile_photo = False
if "profile_photo_bytes" not in st.session_state:
    st.session_state.profile_photo_bytes = None
if "active_sections" not in st.session_state:
    st.session_state.active_sections = ["summary", "skills", "experience", "projects", "education", "certifications"]

# Helper to retrieve API key transparently
def get_api_key():
    # 1. Try to read directly from .env file to ensure real-time updates without restarting server
    try:
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("your_"):
                            return val
    except Exception:
        pass

    # 2. Try Streamlit secrets first (for streamlit cloud deployment)
    try:
        if "GROQ_API_KEY" in st.secrets:
            val = st.secrets["GROQ_API_KEY"]
            if val and val.strip() and not val.startswith("your_"):
                return val
    except Exception:
        pass
        
    # Try environment variables next
    val = os.getenv("GROQ_API_KEY")
    if val and val.strip() and not val.startswith("your_"):
        return val
    return None

api_key = get_api_key()

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.markdown('<h2 class="gradient-text">Settings</h2>', unsafe_allow_html=True)
    st.write("---")
    
    if not api_key:
        st.error("🛠️ Developer Setup Required")
        st.markdown(
            """
            To deploy this app for everyone, configure a Groq API Key:
            - **Locally**: Add `GROQ_API_KEY="your_key"` to a `.env` file in this directory.
            - **Streamlit Cloud**: Add `GROQ_API_KEY = "your_key"` in App Settings ➔ Secrets.
            """
        )
        st.write("---")
        
    # Model Selection
    model_name = st.selectbox(
        "Choose Groq Model",
        options=["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it", "llama-3.1-8b-instant"],
        index=0,
        help="llama-3.3-70b-versatile is the recommended large model. llama-3.1-8b-instant is extremely fast."
    )
    
    # Demo Sandbox Mode
    st.write("---")
    st.markdown("### Demo Sandbox")
    if st.button("📊 Load Demo Data", use_container_width=True):
        st.session_state.analysis_results = {
            "overall_score": 82,
            "metrics": {
                "keyword_match": 75,
                "structure_formatting": 90,
                "impact_quantification": 80,
                "action_verbs": 85
            },
            "key_findings": "The resume is well-structured but lacks several critical technical skills. Experience descriptions need additional metrics.",
            "ats_checks": [
                {"item": "Standard Contact Details", "passed": True, "feedback": "All primary contact info found."},
                {"item": "Section Headers Parseability", "passed": True, "feedback": "Standards headers found."},
                {"item": "Page Length & Margins", "passed": True, "feedback": "Valid page structures."},
                {"item": "Table or Graphic Usage", "passed": False, "feedback": "Table usage detected."}
            ],
            "keyword_analysis": {
                "matched": ["Python", "Docker", "REST APIs", "AWS"],
                "missing": ["Kubernetes", "Terraform", "CI/CD Pipelines"]
            },
            "gap_analysis": {
                "missing_hard_skills": ["Kubernetes", "Terraform / IaC", "CI/CD (GitHub Actions / Jenkins)"],
                "missing_soft_skills": ["Agile/Scrum Leadership"],
                "experience_gaps": ["Requires documented scale deployments (>100k users)."]
            },
            "bullet_point_improvements": [
                {
                    "original": "Responsible for managing server deployments and fixing bugs.",
                    "revised": "Orchestrated containerized deployments for 15+ microservices using Docker, reducing average deployment downtime by 40%.",
                    "reason": "Used power verbs and added measurable outcomes."
                }
            ]
        }
        st.session_state.tailored_resume = {
            "contact_info": {
                "full_name": "Alexander Sterling",
                "email": "alex.sterling@example.com",
                "phone": "+1-555-0199",
                "location": "San Francisco, CA",
                "linkedin": "linkedin.com/in/alexster",
                "portfolio": "github.com/alexster"
            },
            "professional_summary": "Lead Software Engineer with 5+ years of experience designing, building, and maintaining cloud-native applications. Expert in Python, Docker, and AWS, with a proven track record of optimizing deployment pipelines and increasing system reliability. Adept at collaborating in Agile teams to deliver high-quality, customer-focused features.",
            "skills": {
                "technical_skills": ["Python", "SQL", "REST APIs", "AWS (EC2, S3, RDS)", "Docker", "Git", "Kubernetes", "Terraform"],
                "soft_skills": ["Agile/Scrum", "Cross-functional Collaboration", "Technical Writing"],
                "tools_frameworks": ["Django", "FastAPI", "PostgreSQL", "GitHub Actions"]
            },
            "work_experience": [
                {
                    "job_title": "Lead Software Engineer",
                    "company": "TechInnovate Solutions",
                    "location": "San Francisco, CA",
                    "dates": "June 2022 - Present",
                    "bullet_points": [
                        "Orchestrated containerized deployments for 15+ microservices using **Docker** and **Kubernetes**, reducing average deployment downtime by **40%**.",
                        "Collaborated in a 6-person Agile team to deploy 5 new customer-facing features using **FastAPI**, boosting user engagement by **18%**.",
                        "Designed and optimized SQL database schemas in **PostgreSQL**, improving query performance and load times by **25%**."
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California, Berkeley",
                    "location": "Berkeley, CA",
                    "dates": "2018 - 2022",
                    "gpa_or_honors": "GPA 3.8/4.0"
                }
            ],
            "certifications": ["AWS Certified Solutions Architect", "Certified ScrumMaster (CSM)"],
            "projects": [
                {
                    "name": "CloudScale Proxy",
                    "role": "Creator & Maintainer",
                    "description": [
                        "Designed and implemented high-performance reverse proxy in Go with dynamic rate-limiting, handling 50k requests daily.",
                        "Integrated Docker containers to standardize development environments, reducing onboard setup time by 50%."
                    ]
                }
            ]
        }
        st.session_state.resume_text = "Alexander Sterling Resume Text..."
        st.session_state.job_desc = "Software Engineer Job Description..."
        st.rerun()

# --- HEADER SECTION ---
st.markdown('<h1 class="gradient-text" style="text-align: center; font-size: 2.5rem; margin-bottom: 4px; letter-spacing: -0.03em;">ATSify</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: var(--text-muted, #71717a); font-size: 1rem; margin-bottom: 28px; font-weight: 400;">AI-powered resume studio — 7 premium templates, live preview, instant export</p>', unsafe_allow_html=True)

# --- MAIN INPUT SECTION ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📁 Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume/CV (PDF or DOCX)", 
        type=["pdf", "docx"], 
        help="Upload document for text extraction"
    )
    if uploaded_file:
        if uploaded_file.name != st.session_state.uploaded_file_name:
            try:
                with st.spinner("Extracting text from resume..."):
                    st.session_state.resume_text = parser.extract_text(uploaded_file)
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.session_state.analysis_results = None
                    st.session_state.tailored_resume = None
                st.success(f"Successfully loaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error parsing resume: {str(e)}")
                st.session_state.resume_text = ""
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("💼 Target Job Description")
    job_desc = st.text_area(
        "Paste the Job Description (JD) here",
        height=120,
        placeholder="Paste requirements, skills, and details of the target position to evaluate against...",
        help="Paste target JD or roles details"
    )
    if job_desc != st.session_state.job_desc:
        st.session_state.job_desc = job_desc
        st.session_state.analysis_results = None
        st.session_state.tailored_resume = None
    st.markdown('</div>', unsafe_allow_html=True)

# Analyze and tailoring unified trigger
btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
with btn_col2:
    analyze_button = st.button("Analyze Resume", use_container_width=True)

if analyze_button:
    if not api_key:
        st.error("Application API Key is missing. Please configure GROQ_API_KEY in the local `.env` file.")
    elif not st.session_state.resume_text:
        st.error("Please upload a resume first.")
    else:
        try:
            with st.spinner("Step 1: ATS System Checking & Scanning Resume..."):
                analysis = ai_engine.analyze_resume(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    api_key,
                    model_name=model_name
                )
                st.session_state.analysis_results = analysis
                
            with st.spinner("Step 2: Rewriting resume content using STAR methodology and keywords..."):
                gaps_summary = analysis.get("gap_analysis", {})
                tailored = ai_engine.generate_tailored_resume(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    gaps_summary,
                    api_key,
                    model_name=model_name
                )
                st.session_state.tailored_resume = tailored
                
            st.success("ATS Audit Scored & Optimized Resume Generated successfully!")
            st.rerun()
        except Exception as e:
            err_msg = str(e)
            if "invalid_api_key" in err_msg or "401" in err_msg:
                st.error("❌ Invalid API Key! The Groq API key is invalid or has expired. Please verify your `.env` configuration or enter a correct key in the sidebar.")
            else:
                st.error(f"Failed to generate optimized resume: {err_msg}")


# --- RESUME QUALITY ENGINE (SCORE CALCULATOR) ---
def calculate_scores(tailored_data, style_config, analysis_results):
    base = style_config.get("base_scores", {})
    if not isinstance(base, dict):
        base = {}
    
    ats = base.get("ats", 85)
    visual = base.get("visual", 85)
    rec = base.get("recruiter", 85)
    read = base.get("readability", 85)
    prem = base.get("premium", 85)
    
    # Custom values adjustments
    if st.session_state.custom_primary_color:
        visual = min(100, visual + 2)
    if st.session_state.custom_margin:
        m = st.session_state.custom_margin
        if 0.65 <= m <= 0.85:
            visual = min(100, visual + 3)
            read = min(100, read + 2)
            
    # Keyword deductions for ATS
    if analysis_results:
        keyword_data = analysis_results.get("keyword_analysis", {}) or {}
        missing_kw = keyword_data.get("missing", []) or []
        ats = max(45, ats - (len(missing_kw) * 3))
        
    # Recruiter Score adjustments (STAR bullet checks)
    num_bullets = 0
    bullets_with_metrics = 0
    
    # Experience bullets
    for job in tailored_data.get("work_experience", []):
        for bp in job.get("bullet_points", []):
            num_bullets += 1
            if any(char.isdigit() or char == '%' for char in bp) and "[insert" not in bp:
                bullets_with_metrics += 1
                
    # Projects bullets
    for proj in tailored_data.get("projects", []):
        for bp in proj.get("description", []):
            num_bullets += 1
            if any(char.isdigit() or char == '%' for char in bp) and "[insert" not in bp:
                bullets_with_metrics += 1
                
    if num_bullets > 0:
        pct_metrics = (bullets_with_metrics / num_bullets) * 100
        if pct_metrics >= 60:
            rec = min(100, rec + 6)
        elif pct_metrics < 25:
            rec = max(50, rec - 10)
            
    # Readability adjustments (bullet length checks)
    excessive_len_count = 0
    for job in tailored_data.get("work_experience", []):
        for bp in job.get("bullet_points", []):
            if len(bp.split()) > 28:
                excessive_len_count += 1
                
    if excessive_len_count > 2:
        read = max(55, read - 8)
    else:
        read = min(100, read + 3)
        
    # Calculate premium score (weighted average)
    prem = int((ats * 0.35) + (visual * 0.25) + (rec * 0.20) + (read * 0.20))
        
    return {
        "ats": int(ats),
        "visual": int(visual),
        "recruiter": int(rec),
        "readability": int(read),
        "premium": int(prem)
    }


def clean_md_bold_html(text):
    parts = text.split('**')
    for idx in range(len(parts)):
        if idx % 2 == 1:
            parts[idx] = f"<strong>{parts[idx]}</strong>"
    return "".join(parts)

MOCK_THUMBNAIL_DATA = {
    "contact_info": {
        "full_name": "Alexander Wright",
        "email": "alex.wright@email.com",
        "phone": "(555) 019-2834",
        "location": "San Francisco, CA"
    },
    "professional_summary": "Results-driven Senior Professional with 8+ years of experience leading cross-functional teams, executing high-impact technical programs, and designing scalable architectures.",
    "skills": {
        "technical_skills": ["Python", "System Architecture", "Cloud Infrastructure", "API Design", "SQL"],
        "soft_skills": ["Leadership", "Stakeholder Communication"],
        "tools_frameworks": ["AWS", "Docker", "Git", "Kubernetes"]
    },
    "work_experience": [
        {
            "job_title": "Lead Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "dates": "2022 - Present",
            "bullet_points": [
                "Led design and architecture of high-traffic core microservices, improving throughput by 40%."
            ]
        }
    ],
    "education": [
        {
            "degree": "B.S. in Computer Science",
            "institution": "Stanford University",
            "dates": "2014 - 2018",
            "gpa_or_honors": "3.8 GPA"
        }
    ],
    "projects": [
        {
            "name": "CloudMigrate",
            "role": "Lead Architect",
            "description": ["Designed automated database migration tools scaling backups to S3."]
        }
    ],
    "certifications": ["AWS Solutions Architect"]
}

@st.cache_data
def get_cached_thumbnail_html(resume_data_json, style_config_json):
    import json
    try:
        data = json.loads(resume_data_json)
        style_config = json.loads(style_config_json)
        return render_thumbnail_html(data, style_config)
    except Exception as e:
        # Fallback to direct rendering if JSON parsing fails
        return f"""
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; color: #64748b;">
            <h4>Error loading preview</h4>
            <p style="font-size: 11px;">{str(e)}</p>
        </div>
        """

def render_thumbnail_html(data, style_config):
    # Simply call render_resume_html but ignore customizer overrides to show default styles
    return render_resume_html(data, style_config, zoom_pct=100, ignore_customizer=True)

def render_resume_html(data, style_config, zoom_pct=100, active_sections=None, ignore_customizer=False):
    if active_sections is None:
        active_sections = ["summary", "skills", "experience", "projects", "education", "certifications"]
        
    # Safe data extraction fallbacks
    if not isinstance(data, dict):
        data = {}
    if not isinstance(style_config, dict):
        style_config = {}

    # Extract template defaults or overrides
    if ignore_customizer:
        primary_color = style_config.get("primary_color", "#2563eb")
        font_docx = style_config.get("font_docx", "Arial")
        margin_val = style_config.get("margin", 0.75)
        layout = style_config.get("layout", "single_column")
        accent_style = "underline"
        density = "spacious"
        include_photo = (style_config.get("id") in ["elite_portfolio", "dark_executive", "startup_founder"])
        photo_bytes = None
        active_sects = ["summary", "skills", "experience", "projects", "education", "certifications"]
    else:
        primary_color = st.session_state.custom_primary_color or style_config.get("primary_color", "#2563eb")
        font_docx = st.session_state.custom_font or style_config.get("font_docx", "Arial")
        margin_val = st.session_state.custom_margin or style_config.get("margin", 0.75)
        layout = st.session_state.custom_layout or style_config.get("layout", "single_column")
        accent_style = st.session_state.custom_accent_style or "underline"
        density = st.session_state.custom_density or "spacious"
        include_photo = st.session_state.include_profile_photo
        photo_bytes = st.session_state.profile_photo_bytes
        active_sects = st.session_state.active_sections

    # Base font sizes aligned with rules:
    # Name: 40-52px, Section: 16-18px, Body: 10-12px
    if density == "compact":
        base_size = 10.5 * (zoom_pct / 100.0)
        padding_val = margin_val * 32
        line_height = "1.3"
    else: # spacious
        base_size = 11.5 * (zoom_pct / 100.0)
        padding_val = margin_val * 45
        line_height = "1.5"

    name_size = 46 * (zoom_pct / 100.0)
    section_font_size = 17 * (zoom_pct / 100.0)

    # Map Font Families
    font_stacks = {
        "Poppins": "'Poppins', sans-serif",
        "Inter": "'Inter', sans-serif",
        "Montserrat": "'Montserrat', sans-serif",
        "Playfair Display": "'Playfair Display', Georgia, serif",
        "Garamond": "'EB Garamond', Garamond, Georgia, serif",
        "Times New Roman": "'EB Garamond', Garamond, Georgia, serif",
        "Georgia": "'Playfair Display', Georgia, serif",
        "Arial": "'Inter', sans-serif",
        "Calibri": "'Inter', sans-serif",
        "Segoe UI": "'Inter', sans-serif",
        "Consolas": "Consolas, monospace"
    }
    font_style = font_stacks.get(font_docx, "'Inter', sans-serif")
    bg_color = style_config.get("bg_color", "#ffffff")
    text_color = style_config.get("text_color", "#334155")
    
    # Custom Heading Builder
    def get_heading_html(title):
        return f'<h3 class="section-title">{title}</h3>'

    c_info = data.get('contact_info') or {}
    full_name = c_info.get('full_name') or 'Your Name'
    
    contact_items = []
    for k in ['email', 'phone', 'location', 'linkedin', 'portfolio']:
        if c_info.get(k):
            contact_items.append(str(c_info.get(k)))
    contact_line = " &bull; ".join(contact_items) if contact_items else ""

    # Profile Photo HTML
    photo_html = ""
    if include_photo:
        if photo_bytes:
            try:
                import base64
                encoded = base64.b64encode(photo_bytes).decode()
                photo_src = f"data:image/png;base64,{encoded}"
                photo_html = f'<img src="{photo_src}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {primary_color};" />'
            except Exception:
                pass
        elif style_config.get("id") in ["elite_portfolio", "dark_executive", "startup_founder"]:
            # Show an elegant SVG avatar placeholder for premium templates that need it
            photo_html = f'''
            <div style="width: 80px; height: 80px; border-radius: 50%; background: #e2e8f0; display: flex; align-items: center; justify-content: center; border: 2px solid {primary_color}; color: #94a3b8;">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            </div>
            '''

    # Build section HTML chunks
    # 1. Summary
    summary_html = ""
    summary = data.get('professional_summary')
    if summary and "summary" in active_sects:
        summary_html = f"""
        <div class="section-card">
            {get_heading_html("Professional Summary")}
            <div style="font-size: 0.95em; line-height: {line_height}; text-align: justify; color: {text_color};">
                {summary}
            </div>
        </div>
        """

    # 2. Skills
    skills_html = ""
    sk = data.get('skills') or {}
    if sk and "skills" in active_sects:
        tech = sk.get('technical_skills') or []
        soft = sk.get('soft_skills') or []
        tools = sk.get('tools_frameworks') or []
        
        tech_p = f"<div style='margin-bottom: 5px;'><strong>Technical Skills:</strong> {', '.join(tech)}</div>" if tech else ""
        soft_p = f"<div style='margin-bottom: 5px;'><strong>Soft Skills:</strong> {', '.join(soft)}</div>" if soft else ""
        tools_p = f"<div style='margin-bottom: 5px;'><strong>Tools & Systems:</strong> {', '.join(tools)}</div>" if tools else ""
        
        skills_html = f"""
        <div class="section-card">
            {get_heading_html("Skills")}
            <div style="font-size: 0.95em; line-height: {line_height}; color: {text_color};">
                {tech_p}
                {soft_p}
                {tools_p}
            </div>
        </div>
        """

    # 3. Experience
    exp_html = ""
    jobs = data.get('work_experience') or []
    if jobs and "experience" in active_sects:
        job_blocks = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            bullet_list = job.get('bullet_points') or []
            bullets = "".join([f"<li class='bullet-item'>{clean_md_bold_html(bp)}</li>" for bp in bullet_list if bp])
            
            if style_config.get("id") == "timeline_pro":
                job_blocks.append(f"""
                <div class="timeline-container">
                    <div class="timeline-dot"></div>
                    <div class="job-header">
                        <span style="font-weight: 700;"><span class="job-title">{job.get('job_title', '')}</span> &bull; <span class="meta-text">{job.get('company', '')} ({job.get('location', '')})</span></span>
                        <span class="meta-text" style="font-weight: 600;">{job.get('dates', '')}</span>
                    </div>
                    <ul class="bullet-list">
                        {bullets}
                    </ul>
                </div>
                """)
            else:
                job_blocks.append(f"""
                <div style="margin-bottom: 12px;">
                    <div class="job-header">
                        <span style="font-weight: 700;"><span class="job-title">{job.get('job_title', '')}</span> &bull; <span class="meta-text">{job.get('company', '')} ({job.get('location', '')})</span></span>
                        <span class="meta-text" style="font-weight: 600;">{job.get('dates', '')}</span>
                    </div>
                    <ul class="bullet-list">
                        {bullets}
                    </ul>
                </div>
                """)
                
        exp_html = f"""
        <div class="section-card">
            {get_heading_html("Professional Experience")}
            <div style="margin-top: 6px;">
                {"".join(job_blocks)}
            </div>
        </div>
        """

    # 4. Projects
    proj_html = ""
    projects = data.get('projects') or []
    if projects and "projects" in active_sects:
        proj_blocks = []
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            bullet_list = proj.get('description') or []
            bullets = "".join([f"<li class='bullet-item'>{clean_md_bold_html(bp)}</li>" for bp in bullet_list if bp])
            role_text = f" &bull; <span style='font-style: italic; font-weight: normal; font-size: 0.9em; color: #475569;'>{proj.get('role', '')}</span>" if proj.get('role') else ""
            
            proj_blocks.append(f"""
            <div style="margin-bottom: 10px;">
                <div class="job-header">
                    <span style="font-weight: 700;"><span class="job-title">{proj.get('name', '')}</span>{role_text}</span>
                </div>
                <ul class="bullet-list">
                    {bullets}
                </ul>
            </div>
            """)
            
        proj_html = f"""
        <div class="section-card">
            {get_heading_html("Projects")}
            <div style="margin-top: 6px;">
                {"".join(proj_blocks)}
            </div>
        </div>
        """

    # 5. Education
    edu_html = ""
    edu_list = data.get('education') or []
    if edu_list and "education" in active_sects:
        edu_blocks = []
        for edu in edu_list:
            if not isinstance(edu, dict):
                continue
            gpa_text = f" ({edu.get('gpa_or_honors', '')})" if edu.get('gpa_or_honors') else ""
            edu_blocks.append(f"""
            <div class="edu-header">
                <span style="font-weight: 700;">{edu.get('degree', '')} &bull; <span class="meta-text">{edu.get('institution', '')}{gpa_text}</span></span>
                <span class="meta-text" style="font-weight: 600;">{edu.get('dates', '')}</span>
            </div>
            """)
            
        edu_html = f"""
        <div class="section-card">
            {get_heading_html("Education")}
            <div style="margin-top: 6px;">
                {"".join(edu_blocks)}
            </div>
        </div>
        """

    # 6. Certifications
    certs_html = ""
    certs = data.get('certifications') or []
    if certs and "certifications" in active_sects:
        certs_html = f"""
        <div class="section-card">
            {get_heading_html("Certifications")}
            <div style="font-size: 0.95em; line-height: {line_height}; color: {text_color}; margin-top: 4px;">
                {", ".join([str(c) for c in certs])}
            </div>
        </div>
        """

    # Determine sidebar backgrounds and styles
    sidebar_bg_color = "#f8fafc"
    if style_config.get("id") == "split_vision":
        sidebar_bg_color = "#f0fdf4" # Soft green
    elif style_config.get("id") == "executive_elite":
        sidebar_bg_color = "#f8fafc" # Soft navy-ish gray
    elif style_config.get("id") == "product_designer":
        sidebar_bg_color = "#faf5ff" # Soft lavender
    elif style_config.get("id") == "startup_founder":
        sidebar_bg_color = "#fffbeb" # Soft warm amber
    elif style_config.get("id") == "elite_portfolio":
        sidebar_bg_color = "#fafaf9" # Soft warm stone

    # Check if header is dark
    is_dark_header = (style_config.get("id") == "dark_executive")

    # Generate custom template-specific CSS stylesheet
    css_stylesheet = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..800;1,400..800&family=Inter:ital,wght@0,100..900;1,100..900&family=Montserrat:ital,wght@0,100..900;1,100..900&family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Poppins:ital,wght@0,100..900;1,100..900&display=swap');
      
      * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
      }}
      body {{
          margin: 0;
          padding: 0;
          background: {bg_color};
      }}
      
      .resume-container {{
          font-family: {font_style};
          color: {text_color};
          background-color: {bg_color};
          font-size: {base_size}px;
          line-height: {line_height};
          min-height: 1123px;
          position: relative;
          text-align: left;
          box-sizing: border-box;
      }}
      
      /* Typography scale from rules */
      .resume-name {{
          font-size: {name_size}px;
          font-weight: 800;
          color: {primary_color};
          letter-spacing: -0.02em;
          line-height: 1.1;
      }}
      
      .section-title {{
          color: {primary_color};
          font-size: {section_font_size}px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-top: 14px;
          margin-bottom: 6px;
          font-family: {font_style};
      }}
      
      .bullet-list {{
          margin-top: 4px;
          padding-left: 16px;
          font-size: 0.92em;
          color: {text_color};
          list-style-type: disc;
      }}
      
      .bullet-item {{
          margin-bottom: 3px;
          line-height: {line_height};
      }}
      
      .job-header, .edu-header {{
          display: flex;
          justify-content: space-between;
          font-size: 0.95em;
          margin-bottom: 4px;
      }}
      
      .job-title {{
          color: {primary_color};
      }}
      
      .meta-text {{
          color: #64748b;
          font-size: 0.9em;
          font-weight: normal;
      }}
      
      /* Timeline Pro specific timeline path styling */
      .timeline-container {{
          position: relative;
          border-left: 2px solid {primary_color};
          padding-left: 15px;
          margin-left: 8px;
          padding-bottom: 12px;
      }}
      
      .timeline-dot {{
          position: absolute;
          left: -6px;
          top: 4px;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: {primary_color};
          border: 2px solid white;
      }}
      
      /* --- Template Specific Stylesheet Overrides --- */
      
      /* 1. Executive Elite (navy + white, serif headings, elegant luxury) */
      .tpl-executive_elite .section-title {{
          font-family: 'Playfair Display', Georgia, serif;
          border-bottom: 2px solid {primary_color};
          padding-bottom: 2px;
          margin-bottom: 8px;
          letter-spacing: 0.03em;
      }}
      
      /* 2. Modern Tech (minimal white + blue, sans-serif) */
      .tpl-modern_tech .section-title {{
          font-family: 'Inter', sans-serif;
          background: rgba(37, 99, 235, 0.05);
          color: {primary_color};
          padding: 4px 8px;
          border-radius: 4px;
          display: inline-block;
          letter-spacing: 0.02em;
      }}
      
      /* 3. Harvard Professional (academic serif, clean parsing) */
      .tpl-harvard_professional .section-title {{
          font-family: 'EB Garamond', Garamond, serif;
          border-bottom: 1px solid #111827;
          padding-bottom: 2px;
          letter-spacing: 0.08em;
      }}
      
      /* 4. Startup Founder (bold orange/amber, founder vibe) */
      .tpl-startup_founder .section-title {{
          font-family: 'Montserrat', sans-serif;
          border-left: 4px solid {primary_color};
          padding-left: 8px;
          letter-spacing: 0.04em;
      }}
      
      /* 5. Product Designer (soft color accent pink/rose, creative) */
      .tpl-product_designer .section-title {{
          font-family: 'Poppins', sans-serif;
          position: relative;
          display: inline-block;
      }}
      .tpl-product_designer .section-title::after {{
          content: '';
          position: absolute;
          bottom: -3px;
          left: 0;
          width: 30px;
          height: 3px;
          background: {primary_color};
          border-radius: 2px;
      }}
      
      /* 6. Nordic Minimal (generous whitespace, grey/slate accents) */
      .tpl-nordic_minimal .section-title {{
          font-family: 'Inter', sans-serif;
          color: #475569;
          font-weight: 600;
          letter-spacing: 0.12em;
      }}
      
      /* 7. Timeline Pro (teal timeline, vertical timeline) */
      .tpl-timeline_pro .section-title {{
          font-family: 'Poppins', sans-serif;
          border-bottom: 1.5px dashed {primary_color};
          padding-bottom: 3px;
      }}
      
      /* 8. Magazine CV (large hero editorial burgundy) */
      .tpl-magazine_cv .section-title {{
          font-family: 'Playfair Display', Georgia, serif;
          border-bottom: 1px solid {primary_color};
          padding-bottom: 1px;
          text-transform: none;
          font-style: italic;
          font-weight: 800;
      }}
      
      /* 9. Split Vision (green background layout) */
      .tpl-split_vision .section-title {{
          font-family: 'Inter', sans-serif;
          border-bottom: 2px solid {primary_color};
          padding-bottom: 2px;
      }}
      
      /* 10. Metro Resume (grid rounded block cards, subtle shadows) */
      .tpl-metro_resume .section-card {{
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.03);
          margin-bottom: 4px;
      }}
      .tpl-metro_resume .section-title {{
          font-family: 'Montserrat', sans-serif;
          margin-top: 0;
      }}
      
      /* 11. Dark Executive (charcoal header banner, gold text/decor) */
      .tpl-dark_executive .section-title {{
          font-family: 'EB Garamond', Garamond, serif;
          border-bottom: 1.5px solid {primary_color};
          padding-bottom: 2px;
      }}
      
      /* 12. Elite Portfolio (profile photo circle, portfolio) */
      .tpl-elite_portfolio .section-title {{
          font-family: 'Playfair Display', Georgia, serif;
          border-bottom: 1px solid {primary_color};
          padding-bottom: 2px;
      }}
    </style>
    """

    # Assemble Sidebar Layout
    if layout == "two_column_sidebar":
        # Sidebar ordered content
        contact_sidebar_html = f"""
        <div class="section-card">
            {get_heading_html("Contact")}
            <div style="font-size: 0.85em; line-height: 1.4; color: #475569; display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
                {f"<div><strong>Email:</strong><br/>{c_info.get('email', '')}</div>" if c_info.get('email') else ""}
                {f"<div><strong>Phone:</strong><br/>{c_info.get('phone', '')}</div>" if c_info.get('phone') else ""}
                {f"<div><strong>Location:</strong><br/>{c_info.get('location', '')}</div>" if c_info.get('location') else ""}
                {f"<div><strong>LinkedIn:</strong><br/>{c_info.get('linkedin', '')}</div>" if c_info.get('linkedin') else ""}
                {f"<div><strong>Portfolio:</strong><br/>{c_info.get('portfolio', '')}</div>" if c_info.get('portfolio') else ""}
            </div>
        </div>
        """
        left_html = contact_sidebar_html + skills_html + certs_html
        
        # Main content ordered
        right_blocks_map = {
            "summary": summary_html,
            "experience": exp_html,
            "projects": proj_html,
            "education": edu_html
        }
        right_html_list = []
        for sec_id in style_config.get("section_order", []):
            if sec_id in right_blocks_map and right_blocks_map[sec_id]:
                right_html_list.append(right_blocks_map[sec_id])
        right_html = "".join(right_html_list)

        html_output = f"""
        {css_stylesheet}
        <div class="resume-container tpl-{style_config.get("id")}" style="display: flex; min-height: 1123px; padding: 0;">
            <!-- Left Sidebar -->
            <div class="sidebar" style="width: 32%; flex-shrink: 0; background-color: {sidebar_bg_color}; padding: {padding_val}px 24px; box-sizing: border-box; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 16px;">
                {f'<div style="text-align: center; margin-bottom: 8px; display: flex; justify-content: center;">{photo_html}</div>' if photo_html else ""}
                {left_html}
            </div>
            <!-- Right Main Content -->
            <div class="main-content" style="width: 68%; padding: {padding_val}px 24px; box-sizing: border-box; display: flex; flex-direction: column; gap: 16px;">
                <h1 class="resume-name" style="margin-bottom: 6px;">{full_name}</h1>
                {right_html}
            </div>
        </div>
        """
    else:
        # Single Column Layout ordered
        sections_map = {
            "summary": summary_html,
            "skills": skills_html,
            "experience": exp_html,
            "projects": proj_html,
            "education": edu_html,
            "certifications": certs_html
        }
        
        sections_ordered_html = []
        for sec_id in style_config.get("section_order", []):
            if sec_id in sections_map and sections_map[sec_id]:
                sections_ordered_html.append(sections_map[sec_id])
                
        # Header layout
        if is_dark_header:
            header_layout = f"""
            <div class="dark-header-banner" style="background: #0f172a; color: #ffffff; padding: 32px 40px; margin: -{padding_val}px -{padding_val}px 20px -{padding_val}px; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #b45309;">
                <div style="text-align: left;">
                    <h1 class="resume-name" style="color: #f59e0b; margin: 0 0 6px 0;">{full_name}</h1>
                    <div class="contact-line" style="font-size: 0.9em; color: #cbd5e1; font-weight: 500;">{contact_line}</div>
                </div>
                <div style="flex-shrink: 0; margin-left: 20px;">
                    {photo_html}
                </div>
            </div>
            """
        elif style_config.get("id") == "magazine_cv":
            header_layout = f"""
            <div style="text-align: center; margin-bottom: 24px; border-bottom: 3px double {primary_color}; padding-bottom: 16px; width: 100%;">
                {f'<div style="margin-bottom: 12px; display: flex; justify-content: center;">{photo_html}</div>' if photo_html else ""}
                <h1 class="resume-name" style="font-size: {name_size * 1.1}px; font-weight: 900; margin-top: 0; margin-bottom: 8px; letter-spacing: -0.01em; text-transform: uppercase;">{full_name}</h1>
                <div class="contact-line" style="font-size: 0.9em; color: #64748b; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">{contact_line}</div>
            </div>
            """
        else:
            # Standard single column header
            if photo_html:
                header_layout = f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 12px; width: 100%;">
                    <div style="text-align: left;">
                        <h1 class="resume-name" style="margin-top: 0; margin-bottom: 6px;">{full_name}</h1>
                        <div class="contact-line" style="font-size: 0.9em; color: #64748b; font-weight: 500;">{contact_line}</div>
                    </div>
                    <div style="flex-shrink: 0; margin-left: 20px;">
                        {photo_html}
                    </div>
                </div>
                """
            else:
                header_layout = f"""
                <div style="text-align: center; margin-bottom: 20px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 12px; width: 100%;">
                    <h1 class="resume-name" style="margin-top: 0; margin-bottom: 6px;">{full_name}</h1>
                    <div class="contact-line" style="font-size: 0.9em; color: #64748b; font-weight: 500;">{contact_line}</div>
                </div>
                """
            
        html_output = f"""
        {css_stylesheet}
        <div class="resume-container tpl-{style_config.get("id")}" style="padding: {padding_val}px; min-height: 1123px; box-sizing: border-box; display: flex; flex-direction: column;">
            {header_layout}
            <div style="display: flex; flex-direction: column; gap: 16px;">
                {"".join(sections_ordered_html)}
            </div>
        </div>
        """
        
    return html_output
        
 # --- RENDER RESULTS DASHBOARD ---
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    tab1, tab2, tab3 = st.tabs([
        "Resume Studio", 
        "ATS Audit", 
        "Bullet Optimization"
    ])
    score = results.get("overall_score", 0)
    badge_class = "high" if score >= 80 else ("medium" if score >= 60 else "low")
    badge_text = "Good Fit" if score >= 80 else ("Needs Work" if score >= 60 else "Critical")
    
    # ----------------- TAB 1: RESUME STUDIO -----------------
    with tab1:
        
        # Debug: show current selected template (temporary)
        st.caption(f"Debug: Active Template ID: `{st.session_state.selected_template}`")

        resume_data_to_use = st.session_state.tailored_resume or MOCK_THUMBNAIL_DATA

        # Build template cards
        import json
        resume_data_json = json.dumps(resume_data_to_use)

        # Build template cards in a grid layout (4 columns per row)
        cols_per_row = 4
        tpl_keys = list(TEMPLATES.keys())
        
        # Split template keys into rows of 4
        rows_keys = [tpl_keys[i:i + cols_per_row] for i in range(0, len(tpl_keys), cols_per_row)]
        
        for r_idx, row in enumerate(rows_keys):
            tpl_cols = st.columns(cols_per_row)
            for idx, tid in enumerate(row):
                t_config = TEMPLATES[tid]
                with tpl_cols[idx]:
                    selected = st.session_state.selected_template == tid
                    accent = t_config.get("accent_bar", t_config.get("primary_color", "#2563eb"))
                    t_name = t_config.get("name", "Template")
                    t_desc = t_config.get("description", "")
                    badge = t_config.get("badge", "")
                    
                    # Fetch ATS score
                    ats_score = t_config.get("base_scores", {}).get("ats", 90)
                    
                    badge_colors = {
                        "Premium": ("rgba(37,99,235,0.08)", "#2563eb"),
                        "FAANG Style": ("rgba(22,163,74,0.08)", "#16a34a"),
                        "ATS Max": ("rgba(15,23,42,0.08)", "#0f172a"),
                        "Bold": ("rgba(217,119,6,0.08)", "#d97706"),
                        "Creative": ("rgba(230,0,35,0.08)", "#e60023"),
                        "Nordic": ("rgba(113,113,122,0.08)", "#52525b"),
                        "Structured": ("rgba(13,148,136,0.08)", "#0d9488"),
                        "Editorial": ("rgba(136,19,55,0.08)", "#881337"),
                        "Split View": ("rgba(6,95,70,0.08)", "#065f46"),
                        "Grid Blocks": ("rgba(124,58,237,0.08)", "#7c3aed"),
                        "Gold Accent": ("rgba(180,83,9,0.08)", "#b45309"),
                        "Circular Photo": ("rgba(120,53,15,0.08)", "#78350f"),
                    }
                    b_bg, b_color = badge_colors.get(badge, ("rgba(113,113,122,0.08)", "#52525b"))
                    
                    badge_html = f'<span class="tpl-badge" style="background:{b_bg};color:{b_color};">{badge}</span>' if badge else ""
                    check_html = '<div class="tpl-check">&#10003;</div>' if selected else ""
                    
                    # Fetch cached template preview
                    style_config_json = json.dumps(t_config)
                    mini_resume_html = get_cached_thumbnail_html(resume_data_json, style_config_json)
                    
                    card_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: transparent; font-family: system-ui, -apple-system, sans-serif; overflow: hidden; padding: 4px; }}
  .tpl-card {{
      width: 100%;
      height: 420px;
      background: white;
      border: 2px solid {"#2563eb" if selected else "#e2e8f0"};
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      position: relative;
      transition: all 0.25s ease;
  }}
  .tpl-card:hover {{
      transform: translateY(-5px);
      border-color: #2563eb;
      box-shadow: 0 10px 20px rgba(37,99,235,0.15);
  }}
  .tpl-accent {{
      height: 4px;
      width: 100%;
      background: {accent};
  }}
  .tpl-thumb-container {{
      width: 100%;
      height: 290px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f8fafc;
      padding: 5px;
      border-bottom: 1px solid #f1f5f9;
  }}
  .tpl-thumb {{
      width: 220px;
      height: 280px;
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 4px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }}
  .tpl-thumb-scale {{
      transform: scale(0.275);
      transform-origin: top left;
      width: 800px;
      height: 1018px;
      overflow: hidden;
      pointer-events: none;
  }}
  .tpl-middle {{
      padding: 8px 10px 2px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
  }}
  .tpl-name {{
      font-size: 0.88rem;
      font-weight: 700;
      color: #0f172a;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
  }}
  .tpl-score {{
      font-size: 0.72rem;
      color: #16a34a;
      font-weight: 700;
  }}
  .tpl-desc {{
      padding: 0 10px 8px 10px;
      font-size: 0.72rem;
      color: #64748b;
      line-height: 1.2;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      text-overflow: ellipsis;
      height: 42px;
  }}
  .tpl-badge {{
      position: absolute;
      top: 8px;
      right: 8px;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      z-index: 10;
  }}
  .tpl-check {{
      position: absolute;
      top: 8px;
      left: 8px;
      width: 20px;
      height: 20px;
      background: #2563eb;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 0.75rem;
      z-index: 10;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  }}
</style>
</head>
<body>
  <div class="tpl-card">
      <div class="tpl-accent"></div>
      <div class="tpl-thumb-container">
          <div class="tpl-thumb">
              {check_html}
              {badge_html}
              <div class="tpl-thumb-scale">{mini_resume_html}</div>
          </div>
      </div>
      <div class="tpl-middle">
          <div class="tpl-name">{t_name}</div>
          <div class="tpl-score">ATS: {ats_score}%</div>
      </div>
      <div class="tpl-desc">{t_desc}</div>
  </div>
</body>
</html>'''
                    components.html(card_html, height=430, scrolling=False)
                    
                    # Bottom: Native Select Button
                    btn_label = "Selected" if selected else "Select Template"
                    if st.button(btn_label, key=f"select_template_{tid}", use_container_width=True, disabled=selected):
                        st.session_state.selected_template = tid
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.rerun()
        
        active_style = TEMPLATES[st.session_state.selected_template]
        
        # === MAIN LAYOUT: Left Panel (30%) + Right Preview (70%) ===
        tailored_data = st.session_state.tailored_resume or MOCK_THUMBNAIL_DATA
        if tailored_data:
            col_left, col_right = st.columns([1, 3])
            
            # ============ LEFT PANEL: Customizer + Scores + Export ============
            with col_left:
                
                # --- Quality Scores (compact) ---
                scores = calculate_scores(tailored_data, active_style, results)
                st.markdown(f"""
                <div class="quality-score-container">
                    <div class="quality-score-item">
                        <div class="quality-score-num" style="color: #16a34a;">{scores['ats']}%</div>
                        <div class="quality-score-label">ATS</div>
                    </div>
                    <div class="quality-score-item">
                        <div class="quality-score-num" style="color: #2563eb;">{scores['readability']}%</div>
                        <div class="quality-score-label">Read</div>
                    </div>
                    <div class="quality-score-item">
                        <div class="quality-score-num" style="color: #d97706;">{scores['recruiter']}%</div>
                        <div class="quality-score-label">Hire</div>
                    </div>
                    <div class="quality-score-item">
                        <div class="quality-score-num" style="color: #7c3aed;">{scores['visual']}%</div>
                        <div class="quality-score-label">Design</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- Customizer ---
                with st.expander("Colors & Fonts", expanded=True):
                    colors_presets = {
                        "Charcoal": "#18181b",
                        "Navy": "#1e3a5f",
                        "Blue": "#2563eb",
                        "Violet": "#7c3aed",
                        "Emerald": "#059669",
                        "Red": "#e60023",
                        "Slate": "#0f172a"
                    }
                    default_color = active_style.get("primary_color", "#2563eb")
                    preset_keys = list(colors_presets.keys())
                    preset_vals = list(colors_presets.values())
                    try:
                        default_idx = preset_vals.index(st.session_state.custom_primary_color or default_color)
                    except ValueError:
                        default_idx = 0
                    selected_preset = st.selectbox("Color", options=preset_keys, index=default_idx)
                    selected_color_val = colors_presets[selected_preset]
                    c_color = st.color_picker("Custom", value=selected_color_val)
                    st.session_state.custom_primary_color = c_color
                    
                    font_choices = ["Poppins", "Inter", "Montserrat", "Playfair Display", "Garamond"]
                    d_font = active_style.get("font_docx", "Inter")
                    # Map default fonts to premium equivalents
                    font_map_fallback = {
                        "Arial": "Inter",
                        "Calibri": "Inter",
                        "Segoe UI": "Inter",
                        "Times New Roman": "Garamond",
                        "Georgia": "Playfair Display"
                    }
                    mapped_font = font_map_fallback.get(d_font, d_font)
                    try:
                        d_font_idx = font_choices.index(st.session_state.custom_font or mapped_font)
                    except ValueError:
                        d_font_idx = 1 # Default to Inter
                    c_font = st.selectbox("Font", options=font_choices, index=d_font_idx)
                    st.session_state.custom_font = c_font
                
                with st.expander("Layout"):
                    accent_choices = ["Underline", "Left Border", "Minimal"]
                    accent_vals = ["underline", "left_border", "minimal"]
                    default_accent = st.session_state.custom_accent_style or "underline"
                    try:
                        d_accent_idx = accent_vals.index(default_accent)
                    except ValueError:
                        d_accent_idx = 0
                    c_accent_label = st.selectbox("Headings", options=accent_choices, index=d_accent_idx)
                    st.session_state.custom_accent_style = accent_vals[accent_choices.index(c_accent_label)]
                    
                    density_choices = ["Spacious", "Compact"]
                    density_vals = ["spacious", "compact"]
                    default_density = st.session_state.custom_density or "spacious"
                    try:
                        d_density_idx = density_vals.index(default_density)
                    except ValueError:
                        d_density_idx = 0
                    c_density_label = st.selectbox("Spacing", options=density_choices, index=d_density_idx)
                    st.session_state.custom_density = density_vals[density_choices.index(c_density_label)]
                    
                    d_margin = active_style.get("margin", 0.75)
                    c_margin = st.slider("Margin", min_value=0.4, max_value=1.0, value=st.session_state.custom_margin or d_margin, step=0.05)
                    st.session_state.custom_margin = c_margin
                    
                    d_layout = active_style.get("layout", "single_column")
                    layout_choices = ["single_column", "two_column_sidebar"]
                    try:
                        d_layout_idx = layout_choices.index(st.session_state.custom_layout or d_layout)
                    except ValueError:
                        d_layout_idx = 0
                    c_layout = st.selectbox("Columns", options=layout_choices, index=d_layout_idx)
                    st.session_state.custom_layout = c_layout
                
                with st.expander("Sections & Photo"):
                    include_photo = st.checkbox("Profile Photo", value=st.session_state.include_profile_photo)
                    st.session_state.include_profile_photo = include_photo
                    if include_photo:
                        uploaded_photo = st.file_uploader("Upload (PNG/JPG)", type=["png", "jpg", "jpeg"])
                        if uploaded_photo:
                            st.session_state.profile_photo_bytes = uploaded_photo.read()
                    
                    s_summary = st.checkbox("Summary", value=True)
                    s_skills = st.checkbox("Skills", value=True)
                    s_exp = st.checkbox("Experience", value=True)
                    s_proj = st.checkbox("Projects", value=True)
                    s_edu = st.checkbox("Education", value=True)
                    s_certs = st.checkbox("Certifications", value=True)
                    
                    active_sects = []
                    if s_summary: active_sects.append("summary")
                    if s_skills: active_sects.append("skills")
                    if s_exp: active_sects.append("experience")
                    if s_proj: active_sects.append("projects")
                    if s_edu: active_sects.append("education")
                    if s_certs: active_sects.append("certifications")
                    st.session_state.active_sections = active_sects
                
                # --- Content Editor ---
                with st.expander("Edit Contact"):
                    c_name = st.text_input("Full Name", value=tailored_data["contact_info"].get("full_name", ""))
                    c_email = st.text_input("Email", value=tailored_data["contact_info"].get("email", ""))
                    c_phone = st.text_input("Phone", value=tailored_data["contact_info"].get("phone", ""))
                    c_loc = st.text_input("Location", value=tailored_data["contact_info"].get("location", ""))
                    c_link = st.text_input("LinkedIn", value=tailored_data["contact_info"].get("linkedin", ""))
                    c_port = st.text_input("Portfolio", value=tailored_data["contact_info"].get("portfolio", ""))
                    tailored_data["contact_info"]["full_name"] = c_name
                    tailored_data["contact_info"]["email"] = c_email
                    tailored_data["contact_info"]["phone"] = c_phone
                    tailored_data["contact_info"]["location"] = c_loc
                    tailored_data["contact_info"]["linkedin"] = c_link
                    tailored_data["contact_info"]["portfolio"] = c_port
                    
                with st.expander("Edit Summary"):
                    c_sum = st.text_area("Summary", value=tailored_data.get("professional_summary", ""), height=100)
                    tailored_data["professional_summary"] = c_sum
                    
                with st.expander("Edit Skills"):
                    c_tech = st.text_area("Technical (comma-separated)", value=", ".join(tailored_data["skills"].get("technical_skills", [])))
                    c_soft = st.text_area("Soft Skills (comma-separated)", value=", ".join(tailored_data["skills"].get("soft_skills", [])))
                    c_tools = st.text_area("Tools (comma-separated)", value=", ".join(tailored_data["skills"].get("tools_frameworks", [])))
                    tailored_data["skills"]["technical_skills"] = [s.strip() for s in c_tech.split(",") if s.strip()]
                    tailored_data["skills"]["soft_skills"] = [s.strip() for s in c_soft.split(",") if s.strip()]
                    tailored_data["skills"]["tools_frameworks"] = [s.strip() for s in c_tools.split(",") if s.strip()]
                    
                with st.expander("Edit Experience"):
                    for idx, job in enumerate(tailored_data.get("work_experience", [])):
                        st.markdown(f"**{job.get('job_title', 'Position')} — {job.get('company', '')}**")
                        j_title = st.text_input("Title", value=job.get("job_title", ""), key=f"j_title_{idx}")
                        j_comp = st.text_input("Company", value=job.get("company", ""), key=f"j_comp_{idx}")
                        j_dates = st.text_input("Dates", value=job.get("dates", ""), key=f"j_dates_{idx}")
                        j_loc = st.text_input("Location", value=job.get("location", ""), key=f"j_loc_{idx}")
                        j_bullets = st.text_area("Achievements (one per line)", value="\n".join(job.get("bullet_points", [])), height=120, key=f"j_bullets_{idx}")
                        job["job_title"] = j_title
                        job["company"] = j_comp
                        job["dates"] = j_dates
                        job["location"] = j_loc
                        job["bullet_points"] = [b.strip() for b in j_bullets.split("\n") if b.strip()]
                        
                with st.expander("Edit Projects"):
                    for idx, proj in enumerate(tailored_data.get("projects", [])):
                        st.markdown(f"**{proj.get('name', 'Project')}**")
                        p_name = st.text_input("Name", value=proj.get("name", ""), key=f"p_name_{idx}")
                        p_role = st.text_input("Role", value=proj.get("role", ""), key=f"p_role_{idx}")
                        p_bullets = st.text_area("Description (one per line)", value="\n".join(proj.get("description", [])), height=80, key=f"p_bullets_{idx}")
                        proj["name"] = p_name
                        proj["role"] = p_role
                        proj["description"] = [b.strip() for b in p_bullets.split("\n") if b.strip()]
                        
                with st.expander("Edit Education"):
                    for idx, edu in enumerate(tailored_data.get("education", [])):
                        st.markdown(f"**{edu.get('degree', 'Degree')}**")
                        e_deg = st.text_input("Degree", value=edu.get("degree", ""), key=f"e_deg_{idx}")
                        e_inst = st.text_input("Institution", value=edu.get("institution", ""), key=f"e_inst_{idx}")
                        e_dates = st.text_input("Dates", value=edu.get("dates", ""), key=f"e_dates_{idx}")
                        e_gpa = st.text_input("GPA / Honors", value=edu.get("gpa_or_honors", ""), key=f"e_gpa_{idx}")
                        edu["degree"] = e_deg
                        edu["institution"] = e_inst
                        edu["dates"] = e_dates
                        edu["gpa_or_honors"] = e_gpa
                        
                with st.expander("Edit Certifications"):
                    c_certs = st.text_area("Certifications (comma-separated)", value=", ".join(tailored_data.get("certifications", [])))
                    tailored_data["certifications"] = [c.strip() for c in c_certs.split(",") if c.strip()]
                
                # --- Smart Recommendation ---
                st.write("---")
                role_match = "modern_tech"
                desc_lower = st.session_state.job_desc.lower()
                if "software" in desc_lower or "engineer" in desc_lower or "developer" in desc_lower or "qa" in desc_lower or "data" in desc_lower:
                    role_match = "modern_tech"
                    recom_reason = "skills-first layout for technical screening."
                elif "director" in desc_lower or "vp" in desc_lower or "cxo" in desc_lower or "lead" in desc_lower or "manager" in desc_lower:
                    role_match = "executive_elite"
                    recom_reason = "maximum white space for senior leadership."
                elif "creative" in desc_lower or "design" in desc_lower or "ux" in desc_lower or "marketing" in desc_lower:
                    role_match = "product_designer"
                    recom_reason = "visual sidebar layout for creative roles."
                elif "consulting" in desc_lower or "analyst" in desc_lower or "finance" in desc_lower or "law" in desc_lower or "bank" in desc_lower:
                    role_match = "data_consulting"
                    recom_reason = "refined serif for corporate environments."
                elif "product" in desc_lower or "apple" in desc_lower or "startup" in desc_lower:
                    role_match = "startup_founder"
                    recom_reason = "ultra-clean design for product roles."
                else:
                    role_match = "harvard_professional"
                    recom_reason = "maximum ATS compatibility."
                    
                rec_template = TEMPLATES.get(role_match, {})
                rec_name = rec_template.get("name", "Modern Professional")
                st.caption(f"Suggested: **{rec_name}** — {recom_reason}")
                if role_match != st.session_state.selected_template:
                    if st.button(f"Switch to {rec_name}", use_container_width=True):
                        st.session_state.selected_template = role_match
                        st.session_state.custom_primary_color = None
                        st.session_state.custom_font = None
                        st.session_state.custom_margin = None
                        st.session_state.custom_layout = None
                        st.session_state.custom_accent_style = None
                        st.session_state.custom_density = None
                        st.rerun()
                
                st.write("---")
                if st.button("Reset Preview Cache", key="reset_preview_cache_btn", use_container_width=True):
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.session_state.custom_primary_color = None
                    st.session_state.custom_font = None
                    st.session_state.custom_margin = None
                    st.session_state.custom_layout = None
                    st.session_state.custom_accent_style = None
                    st.session_state.custom_density = None
                    st.session_state.selected_template = "executive_elite"
                    st.rerun()
            
            # ============ RIGHT PANEL: Live Preview + Export ============
            with col_right:
                # Zoom controls
                col_z1, col_z2 = st.columns([3, 1])
                with col_z1:
                    zoom_slider = st.slider("Zoom", min_value=50, max_value=150, value=st.session_state.zoom_pct, step=10, format="%d%%")
                    st.session_state.zoom_pct = zoom_slider
                with col_z2:
                    st.write("")
                    st.write("")

                try:
                    html_preview = render_resume_html(
                        tailored_data,
                        active_style,
                        zoom_pct=st.session_state.zoom_pct,
                        active_sections=st.session_state.active_sections
                    )
                except Exception as e:
                    html_preview = f"""
                    <div style="font-family: system-ui, -apple-system, sans-serif; text-align: center; padding: 40px 20px; color: #64748b; background: white; border-radius: 8px; border: 1px dashed #cbd5e1; max-width: 400px; margin: 40px auto; box-sizing: border-box;">
                        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                        <h3 style="color: #0f172a; font-size: 18px; margin-bottom: 8px; font-weight:600;">Failed to Render Template</h3>
                        <p style="font-size: 14px; line-height: 1.5; margin-bottom: 12px;">The selected template encountered a rendering issue.</p>
                        <p style="font-size: 11px; color: #94a3b8; font-family: monospace; overflow-x: auto; background: #f8fafc; padding: 8px; border-radius:4px;">{str(e)}</p>
                    </div>
                    """

                # Wrap in a full HTML document for components.html
                full_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #f0f0f0; display: flex; justify-content: center; padding: 20px; }}
  .resume-page {{
    background: white;
    box-shadow: 0 2px 16px rgba(0,0,0,0.10);
    border-radius: 4px;
    width: 100%;
    max-width: 720px;
    animation: fadeIn 0.25s ease-in;
  }}
  @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
</style>
</head>
<body>
  <div class="resume-page">{html_preview}</div>
</body>
</html>'''
                components.html(full_html, height=1200, scrolling=True)
                
                # Export buttons below preview
                st.write("")
                export_config = {
                    "id": active_style["id"],
                    "name": active_style["name"],
                    "font_docx": st.session_state.custom_font or active_style["font_docx"],
                    "font_pdf": active_style["font_pdf"],
                    "primary_color": st.session_state.custom_primary_color or active_style["primary_color"],
                    "text_color": active_style["text_color"],
                    "bg_color": active_style["bg_color"],
                    "margin": st.session_state.custom_margin or active_style["margin"],
                    "layout": st.session_state.custom_layout or active_style["layout"],
                    "section_order": active_style["section_order"],
                    "density": st.session_state.custom_density or "spacious",
                    "accent_style": st.session_state.custom_accent_style or "underline",
                    "profile_photo": st.session_state.profile_photo_bytes if st.session_state.include_profile_photo else None
                }
                
                col_d1, col_d2 = st.columns(2)
                pdf_bytes, pdf_adjusted = exporter.generate_pdf(tailored_data, export_config)
                with col_d1:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"Resume_{active_style['id']}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                docx_bytes, docx_adjusted = exporter.generate_docx(tailored_data, export_config)
                with col_d2:
                    st.download_button(
                        label="Download DOCX",
                        data=docx_bytes,
                        file_name=f"Resume_{active_style['id']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                if pdf_adjusted or docx_adjusted:
                    st.caption("Layout auto-adjusted for page fit.")
                
        else:
            st.info("Click **Analyze Resume** to generate your optimized resume and start editing.")

    # ----------------- TAB 2: ATS AUDIT -----------------
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div style="text-align: center; margin-top: 15px;">
                <span class="score-badge {badge_class}">{badge_text}</span>
                <div class="quality-score-num" style="font-size: 5rem; margin-top: 15px; color:#4f46e5;">{score}%</div>
                <div class="quality-score-label">Overall ATS Score</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown('<h3 style="margin-top: 0;">ATS Optimization Breakdown</h3>', unsafe_allow_html=True)
            metrics = results.get("metrics", {})
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-item">
                    <div class="metric-value">{metrics.get("keyword_match", 0)}%</div>
                    <div class="metric-label">Keywords</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{metrics.get("structure_formatting", 0)}%</div>
                    <div class="metric-label">Structure</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{metrics.get("impact_quantification", 0)}%</div>
                    <div class="metric-label">STAR Impact</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{metrics.get("action_verbs", 0)}%</div>
                    <div class="metric-label">Power Verbs</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"**Key Auditing Findings:** {results.get('key_findings', '')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Keyword Gaps
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🔍 Role Competencies and Keywords Analysis")
        keyword_data = results.get("keyword_analysis", {})
        matched_kw = keyword_data.get("matched", [])
        missing_kw = keyword_data.get("missing", [])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("##### 🟢 Matched Industry Keywords")
            if matched_kw:
                chips = "".join([f'<span style="display:inline-block; margin:4px; padding:4px 10px; background:rgba(16,185,129,0.08); color:#10b981; border:1px solid rgba(16,185,129,0.2); border-radius:12px; font-size:0.85rem;">{kw}</span>' for kw in matched_kw])
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.info("No matched keywords identified.")
        with col_m2:
            st.markdown("##### 🔴 Missing High-Priority Keywords")
            if missing_kw:
                chips = "".join([f'<span style="display:inline-block; margin:4px; padding:4px 10px; background:rgba(244,63,94,0.08); color:#f43f5e; border:1px solid rgba(244,63,94,0.2); border-radius:12px; font-size:0.85rem;">{kw}</span>' for kw in missing_kw])
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.success("No missing high-priority keywords.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Skill Gaps
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 Skills & Experience Alignment Gaps")
        gaps = results.get("gap_analysis", {})
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.markdown("##### Hard Skills Gaps")
            for skill in gaps.get("missing_hard_skills", []):
                st.markdown(f"- 🔸 {skill}")
        with col_g2:
            st.markdown("##### Soft Skills Gaps")
            for skill in gaps.get("missing_soft_skills", []):
                st.markdown(f"- 🔸 {skill}")
        with col_g3:
            st.markdown("##### Experience Alignment")
            exp_g = gaps.get("experience_gaps", [])
            if isinstance(exp_g, list):
                for gap in exp_g:
                    st.markdown(f"- 💼 {gap}")
            else:
                st.markdown(f"- 💼 {exp_g}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # System checks
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📋 ATS Standard Systems Check")
        checks = results.get("ats_checks", [])
        if checks:
            cols = st.columns(2)
            for idx, chk in enumerate(checks):
                col_idx = idx % 2
                passed = chk.get("passed", False)
                item = chk.get("item", "")
                feedback = chk.get("feedback", "")
                status_icon = "🟢" if passed else "🔴"
                card_style = "success" if passed else "critical"
                
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="improvement-item {card_style}">
                        <strong>{status_icon} {item}</strong><br/>
                        <span style="font-size:0.9rem; color:#475569;">{feedback}</span>
                    </div>
                    """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------- TAB 3: BULLET OPTIMIZATION -----------------
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("##### Bullet Point Revisions")
        bullet_revisions = results.get("bullet_point_improvements", [])
        if bullet_revisions:
            for rev in bullet_revisions:
                st.markdown(f"""
                <div class="bullet-comparison-card">
                    <div class="bullet-comparison-header">
                        <span class="bullet-badge original">Original bullet</span>
                        <span class="bullet-badge revised">ATS Star format</span>
                    </div>
                    <div class="bullet-comparison-body">
                        <div class="bullet-half original-half">{rev.get("original", "")}</div>
                        <div class="bullet-half revised-half">{rev.get("revised", "")}</div>
                    </div>
                    <div class="bullet-comparison-footer">
                        <strong>🎯 Rationale:</strong> {rev.get("reason", "")}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
            
else:
    # Landing page state
    st.markdown("""
    <div class="welcome-card">
        <h2 style="margin-top: 0; font-size: 1.75rem; font-weight: 800; color: #09090b; letter-spacing: -0.02em;">ATSify</h2>
        <p style="color: #71717a; font-size: 0.95rem; line-height: 1.6; margin-bottom: 24px;">
            AI-powered resume studio. Optimize for ATS systems, rewrite bullets using the STAR methodology, identify skill gaps, customize templates, and export professionally formatted documents.
        </p>
        <div class="features-grid">
            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="9" x2="9" y2="17"></line><line x1="15" y1="13" x2="15" y2="17"></line><line x1="12" y1="5" x2="12" y2="17"></line></svg>
                </div>
                <div class="feature-text">
                    <h5>ATS Analysis</h5>
                    <p>Real-time scoring with keyword matching, structure checks, and optimization insights.</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                </div>
                <div class="feature-text">
                    <h5>Gap Detection</h5>
                    <p>Identify missing keywords, hard skills, soft skills, and experience gaps.</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path></svg>
                </div>
                <div class="feature-text">
                    <h5>7 Premium Templates</h5>
                    <p>Modern Professional, Executive Minimal, Apple Style, Pinterest Elegant, ATS Clean, Technical Engineer, Premium Corporate.</p>
                </div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                </div>
                <div class="feature-text">
                    <h5>Export</h5>
                    <p>Pixel-perfect PDF and editable DOCX. Formatting preserved across all templates.</p>
                </div>
            </div>
        </div>
        <div style="margin-top: 24px; padding: 12px; background: #f4f4f5; border: 1px solid #e4e4e7; border-radius: 10px; text-align: center; color: #71717a; font-size: 0.85rem;">
            Upload your resume, paste the job description, and click <strong>Analyze Resume</strong> to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)
