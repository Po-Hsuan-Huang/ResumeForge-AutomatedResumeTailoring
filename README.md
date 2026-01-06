# ResumeForge - Automated Resume Tailoring Pipeline

An intelligent Python automation tool that tailors your resume to specific job descriptions using AI-powered content selection and LaTeX compilation.

## 🎯 Features

- **Smart Role Classification**: Automatically identifies the best role category for a job description
- **Content Extraction**: Parses LaTeX resume files to extract relevant experience
- **AI-Powered Synthesis**: Uses OpenAI GPT-4 to select and tailor content to match job requirements
- **Professional PDF Output**: Compiles a polished resume PDF using LaTeX

## 📁 Project Structure

```
ResumeForge/
├── input/
│   └── job_description.txt       # Paste job descriptions here
├── library/                      # Your resume library (organized by role)
│   ├── Computer_Vision/
│   ├── Machine_Learning_Engineering/
│   ├── Healthcare_and_Research_Scientist/
│   ├── Software_Development_and_Architecture/
│   ├── Leadership_and_Strategy/
│   └── General_and_Academic/
├── templates/
│   └── master_template.tex       # LaTeX template with Jinja2 placeholders
├── output/                       # Generated PDFs appear here
├── main.py                       # Main pipeline script
├── requirements.txt              # Python dependencies
└── .env                          # API keys (create from .env.example)
```

## 🚀 Installation

### Prerequisites

1. **Python 3.8+**
2. **LaTeX Distribution** (for PDF compilation):
   - **Ubuntu/Debian**: `sudo apt-get install texlive-latex-base texlive-latex-extra`
   - **macOS**: `brew install --cask mactex`
   - **Windows**: Download from [MiKTeX](https://miktex.org/)

### Setup

1. **Clone or navigate to the repository**:
   ```bash
   cd /home/phsuanh/Documents/ResumeForge-AutomatedResumeTailoring
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure OpenAI API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## 📝 Usage

### Basic Workflow

1. **Add your job description**:
   ```bash
   # Edit input/job_description.txt and paste the job description
   nano input/job_description.txt
   ```

2. **Run the pipeline**:
   ```bash
   python main.py
   ```

3. **Get your tailored resume**:
   - The PDF will be generated in `output/tailored_resume.pdf`

### What Happens Under the Hood

The pipeline executes four main modules:

1. **Module A - Classifier**: Analyzes the job description and selects the most relevant role category from your library
2. **Module B - Parser**: Extracts bullet points and content from LaTeX files in the selected category
3. **Module C - Synthesizer**: Uses OpenAI API to:
   - Generate a tailored 3-sentence profile summary
   - Select the top 5-7 most relevant experience bullet points
   - Extract matching technical skills
4. **Module D - Compiler**: Injects the tailored content into the LaTeX template and compiles a PDF

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

### Customizing the Template

Edit `templates/master_template.tex` to customize:
- Header information (name, contact details)
- Section formatting
- Colors and styling
- Static sections (education, etc.)

The template uses Jinja2 placeholders:
- `{{ summary }}` - Profile summary
- `{{ experience_items }}` - List of experience bullet points
- `{{ skills }}` - Technical skills

## 📚 Library Organization

The `library/` directory contains symbolic links to your resume files organized by role:

- **Computer_Vision**: CV, visual algorithms, imaging roles
- **Machine_Learning_Engineering**: Core ML engineering and infrastructure
- **Healthcare_and_Research_Scientist**: Medical/clinical AI applications
- **Software_Development_and_Architecture**: General software engineering
- **Leadership_and_Strategy**: Senior and responsible AI roles
- **General_and_Academic**: Fallback and academic CVs

### Adding LaTeX Source Files

For each role category, add `.tex` files containing your experience:

```bash
# Example structure
library/Computer_Vision/
├── experience.tex
└── projects.tex
```

**Note**: If no `.tex` files are found, the system will automatically create sample content.

## 🐛 Troubleshooting

### "pdflatex not found"
Install a LaTeX distribution (see Prerequisites section).

### "OPENAI_API_KEY not found"
Create a `.env` file with your OpenAI API key (see Configuration section).

### "No .tex files found"
The system will create sample files automatically. Replace them with your actual LaTeX resume content.

### LaTeX Compilation Errors
Check the generated `.tex` file in `output/tailored_resume.tex` for syntax issues.

## 🔒 Privacy & Security

- All processing happens locally on your machine
- Only the job description and extracted resume content are sent to OpenAI API
- Your API key is stored locally in `.env` (never commit this file!)
- Add `.env` to `.gitignore` to prevent accidental commits

## 📄 License

This project is for personal use. Customize as needed for your resume tailoring workflow.

## 🤝 Contributing

This is a personal automation tool, but feel free to fork and adapt for your own needs!

---

**Happy job hunting! 🎯**
