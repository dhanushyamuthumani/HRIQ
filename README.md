# ResumeIQ AI 🚀

**Local LLM-Based Intelligent Resume Parsing & Classification System**

ResumeIQ AI is a powerful, locally-hosted tool that extracts structured data from resumes and classifies them using Llama3 (via Ollama). It ensures 100% data privacy by processing everything offline.

## ✨ Features

- **Bulk & Single Processing:** Support for PDF and DOCX files.
- **AI-Powered Extraction:** Uses Llama3 to extract Name, Email, Phone, Role, Technologies, and Experience.
- **Job Description Matcher:** **[NEW]** AI-powered compatibility scoring between resumes and JDs.
- **Smart Outreach:** **[NEW]** Automated professional email generation (Invites/Rejections).
- **Candidate Search:** **[NEW]** Keyword-based searching across extracted data.
- **Resume Scoring Engine:** Automatically evaluates resume quality on a 0-100 scale.
- **Visual Analytics Dashboard:** Interactive insights using Plotly.
- **Experience Logic:** Automatically calculates experience levels (Fresher to Senior).
- **Duplicate Detection:** Identifies duplicate candidates based on Email or Phone.
- **ATS-Ready Export:** Generates structured Excel reports.
- **Privacy First:** No cloud dependency, 100% local processing.

## 🛠️ Technical Stack

- **UI:** Streamlit
- **AI Engine:** Ollama (Llama3)
- **Extraction:** pdfplumber, python-docx
- **Data:** Pandas, openpyxl

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com/) installed and running.
- Pull the Llama3 model:
  ```bash
  ollama pull llama3
  ```

### 2. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

## 📂 Project Structure

- `core/`: Core logic (text extraction, AI engine, business logic).
- `utils/`: Utilities (Excel generation).
- `outputs/`: Default folder for generated reports.
- `app.py`: Main Streamlit application.
- `config.py`: Global configuration.

## 🔮 Roadmap
- [x] Phase 2: Dashboard analytics and resume scoring.
- [x] Phase 3: JD matching, email workflows, and search.
- [ ] Phase 4: SaaS conversion and multi-user authentication.

---
Built with ❤️ for privacy-conscious recruitment.
