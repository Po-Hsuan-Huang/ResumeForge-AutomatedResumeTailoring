#!/usr/bin/env python3
"""
ResumeForge - Automated Resume Tailoring Pipeline
Tailors resumes to specific job descriptions using AI-powered content selection.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template

# Load environment variables
load_dotenv()

# Configuration
LIBRARY_DIR = Path("library")
INPUT_DIR = Path("input")
TEMPLATES_DIR = Path("templates")
OUTPUT_DIR = Path("output")
JOB_DESCRIPTION_FILE = INPUT_DIR / "job_description.txt"
MASTER_TEMPLATE = TEMPLATES_DIR / "master_template.tex"


class ResumeForgeError(Exception):
    """Base exception for ResumeForge errors"""
    pass


def setup_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ResumeForgeError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please create a .env file with your API key. "
            "See .env.example for reference."
        )
    return OpenAI(api_key=api_key)


# ============================================================================
# MODULE A: The Classifier
# ============================================================================

def select_role_folder(jd_text: str, list_of_folders: List[str], client: OpenAI) -> str:
    """
    Classify which role folder best matches the job description.
    
    Args:
        jd_text: The job description text
        list_of_folders: List of available role folder names
        client: OpenAI client instance
        
    Returns:
        The name of the best matching folder
    """
    print("\n[MODULE A] Classifying job role...")
    
    system_prompt = """You are an expert career advisor and resume specialist. 
Your task is to analyze a job description and determine which role category it best fits into."""
    
    user_prompt = f"""Given the following job description, select the SINGLE role category that best matches.

Job Description:
{jd_text}

Available Role Categories:
{', '.join(list_of_folders)}

Return ONLY the exact folder name from the list above that best matches this job description.
Do not include any explanation, just the folder name."""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        selected_folder = response.choices[0].message.content.strip()
        
        # Validate the response
        if selected_folder not in list_of_folders:
            # Try to find a close match
            for folder in list_of_folders:
                if folder.lower() in selected_folder.lower() or selected_folder.lower() in folder.lower():
                    selected_folder = folder
                    break
            else:
                raise ResumeForgeError(
                    f"LLM returned invalid folder: '{selected_folder}'. "
                    f"Expected one of: {list_of_folders}"
                )
        
        print(f"✓ Selected role category: {selected_folder}")
        return selected_folder
        
    except Exception as e:
        raise ResumeForgeError(f"Error in role classification: {str(e)}")


# ============================================================================
# MODULE B: The Content Parser
# ============================================================================

def parse_tex_files(folder_path: Path) -> str:
    """
    Parse LaTeX files and extract content (bullet points and text blocks).
    
    Args:
        folder_path: Path to the folder containing .tex files
        
    Returns:
        Concatenated string of all extracted experience content
    """
    print(f"\n[MODULE B] Parsing LaTeX files from {folder_path}...")
    
    if not folder_path.exists():
        raise ResumeForgeError(f"Folder not found: {folder_path}")
    
    tex_files = list(folder_path.glob("*.tex"))
    
    if not tex_files:
        print(f"⚠ Warning: No .tex files found in {folder_path}")
        print("  Creating a placeholder experience file...")
        
        # Create a sample .tex file for this role
        sample_content = create_sample_tex_content(folder_path.name)
        sample_file = folder_path / "experience.tex"
        sample_file.write_text(sample_content)
        tex_files = [sample_file]
        print(f"✓ Created sample file: {sample_file}")
    
    all_content = []
    
    for tex_file in tex_files:
        print(f"  Processing: {tex_file.name}")
        content = tex_file.read_text(encoding='utf-8', errors='ignore')
        
        # Extract \item bullet points
        items = re.findall(r'\\item\s+(.+?)(?=\\item|\\end\{itemize\}|\\end\{enumerate\}|$)', 
                          content, re.DOTALL)
        
        # Clean up the items
        items = [item.strip().replace('\n', ' ').replace('  ', ' ') for item in items]
        
        # Extract text blocks (paragraphs not in lists)
        # Remove comments
        content_no_comments = re.sub(r'%.*', '', content)
        
        # Find text blocks between sections
        text_blocks = re.findall(r'(?:^|\n)([A-Z][^\\%\n]+(?:\n[^\\%\n]+)*)', content_no_comments)
        text_blocks = [block.strip() for block in text_blocks if len(block.strip()) > 50]
        
        all_content.extend(items)
        all_content.extend(text_blocks)
    
    combined_content = "\n\n".join(all_content)
    
    print(f"✓ Extracted {len(all_content)} content items from {len(tex_files)} file(s)")
    
    return combined_content


def create_sample_tex_content(role_category: str) -> str:
    """Create sample LaTeX content for a role category."""
    
    # Generic template that can be customized per role
    template = r"""\documentclass{article}
\begin{document}

\section*{Experience}

\begin{itemize}
    \item Developed and deployed machine learning models for production systems
    \item Collaborated with cross-functional teams to deliver AI-powered solutions
    \item Optimized algorithms for performance and scalability
    \item Conducted research and implemented state-of-the-art techniques
    \item Mentored junior team members and led technical discussions
\end{itemize}

\section*{Projects}

\begin{itemize}
    \item Built end-to-end data pipelines for large-scale data processing
    \item Implemented deep learning models using PyTorch and TensorFlow
    \item Designed and developed RESTful APIs for model serving
    \item Created automated testing and CI/CD pipelines
    \item Published research findings in peer-reviewed conferences
\end{itemize}

\end{document}
"""
    return template


# ============================================================================
# MODULE C: The Synthesizer (OpenAI API)
# ============================================================================

def generate_tailored_content(jd_text: str, available_experience: str, client: OpenAI) -> Dict:
    """
    Use OpenAI API to generate tailored resume content.
    
    Args:
        jd_text: The job description text
        available_experience: Extracted experience from LaTeX files
        client: OpenAI client instance
        
    Returns:
        Dictionary with 'summary', 'experience_items', and 'skills'
    """
    print("\n[MODULE C] Generating tailored content with OpenAI...")
    
    system_prompt = """You are an expert resume writer with deep knowledge of ATS optimization and hiring practices.
Your task is to tailor resume content to match specific job descriptions while maintaining authenticity."""

    user_prompt = f"""Using the available experience below, create tailored resume content for the following job description.

JOB DESCRIPTION:
{jd_text}

AVAILABLE EXPERIENCE:
{available_experience}

Please provide:
1. A compelling 3-sentence Profile Summary that highlights the most relevant qualifications for this role
2. Select the top 5-7 bullet points from the available experience that best match the job requirements
3. A list of Technical Skills found in the experience that match the job description

Return your response as a JSON object with this exact structure:
{{
    "summary": "Your 3-sentence profile summary here...",
    "experience_items": [
        "First relevant bullet point...",
        "Second relevant bullet point...",
        "etc..."
    ],
    "skills": "Python, TensorFlow, PyTorch, Computer Vision, Deep Learning, etc."
}}

Important: Return ONLY the JSON object, no additional text or formatting."""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in content:
            content = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
        elif "```" in content:
            content = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
        
        # Parse JSON
        tailored_content = json.loads(content)
        
        # Validate structure
        required_keys = {"summary", "experience_items", "skills"}
        if not required_keys.issubset(tailored_content.keys()):
            raise ResumeForgeError(f"Missing required keys in response. Expected: {required_keys}")
        
        print(f"✓ Generated tailored content:")
        print(f"  - Summary: {len(tailored_content['summary'])} characters")
        print(f"  - Experience items: {len(tailored_content['experience_items'])}")
        print(f"  - Skills: {len(tailored_content['skills'].split(','))} skills")
        
        return tailored_content
        
    except json.JSONDecodeError as e:
        raise ResumeForgeError(f"Failed to parse JSON response: {str(e)}\nResponse: {content}")
    except Exception as e:
        raise ResumeForgeError(f"Error generating tailored content: {str(e)}")


# ============================================================================
# MODULE D: The PDF Compiler
# ============================================================================

def render_pdf(json_data: Dict, template_path: Path, output_dir: Path) -> Path:
    """
    Render PDF from template and tailored content.
    
    Args:
        json_data: Dictionary with summary, experience_items, and skills
        template_path: Path to the LaTeX template file
        output_dir: Directory to save output files
        
    Returns:
        Path to the generated PDF file
    """
    print("\n[MODULE D] Compiling PDF...")
    
    # Check if pdflatex is available
    try:
        subprocess.run(["pdflatex", "--version"], 
                      capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        raise ResumeForgeError(
            "pdflatex not found. Please install LaTeX:\n"
            "  Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra\n"
            "  macOS: brew install --cask mactex\n"
            "  Windows: Download from https://miktex.org/"
        )
    
    # Load template
    if not template_path.exists():
        raise ResumeForgeError(f"Template not found: {template_path}")
    
    template_content = template_path.read_text(encoding='utf-8')
    template = Template(template_content)
    
    # Render template with data
    rendered_tex = template.render(
        summary=json_data['summary'],
        experience_items=json_data['experience_items'],
        skills=json_data['skills']
    )
    
    # Write temporary .tex file
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_tex_file = output_dir / "tailored_resume.tex"
    temp_tex_file.write_text(rendered_tex, encoding='utf-8')
    
    print(f"✓ Generated LaTeX file: {temp_tex_file}")
    
    # Compile with pdflatex
    print("  Compiling with pdflatex...")
    try:
        # Run pdflatex twice for proper formatting
        for i in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", temp_tex_file.name],
                cwd=output_dir,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_log = output_dir / "tailored_resume.log"
                if error_log.exists():
                    log_content = error_log.read_text()
                    # Extract relevant error lines
                    errors = re.findall(r'! .*', log_content)
                    error_msg = "\n".join(errors[:5]) if errors else "Unknown LaTeX error"
                else:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                
                raise ResumeForgeError(f"pdflatex compilation failed:\n{error_msg}")
    
    except subprocess.TimeoutExpired:
        raise ResumeForgeError("pdflatex compilation timed out")
    
    # Check if PDF was created
    pdf_file = output_dir / "tailored_resume.pdf"
    if not pdf_file.exists():
        raise ResumeForgeError("PDF file was not generated")
    
    # Clean up auxiliary files
    for ext in ['.aux', '.log', '.out']:
        aux_file = output_dir / f"tailored_resume{ext}"
        if aux_file.exists():
            aux_file.unlink()
    
    print(f"✓ PDF compiled successfully: {pdf_file}")
    
    return pdf_file


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Main pipeline orchestration."""
    print("=" * 70)
    print("ResumeForge - Automated Resume Tailoring Pipeline")
    print("=" * 70)
    
    try:
        # Initialize OpenAI client
        client = setup_openai_client()
        print("✓ OpenAI client initialized")
        
        # Read job description
        if not JOB_DESCRIPTION_FILE.exists():
            raise ResumeForgeError(
                f"Job description file not found: {JOB_DESCRIPTION_FILE}\n"
                f"Please create this file with the job description text."
            )
        
        jd_text = JOB_DESCRIPTION_FILE.read_text(encoding='utf-8')
        print(f"✓ Loaded job description ({len(jd_text)} characters)")
        
        # Get list of role folders
        if not LIBRARY_DIR.exists():
            raise ResumeForgeError(f"Library directory not found: {LIBRARY_DIR}")
        
        role_folders = [f.name for f in LIBRARY_DIR.iterdir() if f.is_dir()]
        
        if not role_folders:
            raise ResumeForgeError(f"No role folders found in {LIBRARY_DIR}")
        
        print(f"✓ Found {len(role_folders)} role categories: {', '.join(role_folders)}")
        
        # MODULE A: Classify role
        selected_role = select_role_folder(jd_text, role_folders, client)
        
        # MODULE B: Parse LaTeX files
        role_folder_path = LIBRARY_DIR / selected_role
        available_experience = parse_tex_files(role_folder_path)
        
        # MODULE C: Generate tailored content
        tailored_content = generate_tailored_content(jd_text, available_experience, client)
        
        # MODULE D: Compile PDF
        pdf_path = render_pdf(tailored_content, MASTER_TEMPLATE, OUTPUT_DIR)
        
        # Success!
        print("\n" + "=" * 70)
        print("✓ SUCCESS! Resume tailored and compiled.")
        print(f"✓ Output PDF: {pdf_path.absolute()}")
        print("=" * 70)
        
        return 0
        
    except ResumeForgeError as e:
        print(f"\n❌ ERROR: {str(e)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
