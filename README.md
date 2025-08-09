# Advanced ATS Score Predictor & Resume Optimizer

An intelligent web application that analyzes a candidate’s resume against a job description (JD), predicts an ATS (Applicant Tracking System) compatibility score, identifies missing skills, and automatically updates the resume to maximize chances of passing ATS filters.

---

## Features

- Upload resume file (PDF or DOCX) and paste job description text.
- Extract and preprocess text from resume and JD (tokenization, stopword removal, lemmatization).
- Compute semantic similarity score between resume and JD using TF-IDF and BERT embeddings.
- Extract key skills from the job description and compare them with the resume.
- Generate detailed ATS score breakdown including matched skills, missing skills, and formatting issues.
- Automatically insert missing skills into the Skills section and integrate them into experience bullets without altering original formatting.
- Output updated resume preserving original styles and structure.
- Provide suggestions to improve the resume further.
- Download the modified resume as DOCX (optionally PDF).

---

## Tech Stack

- Backend: Python, Django
- NLP & Text Processing: spaCy, scikit-learn, sentence-transformers (BERT)
- Resume parsing and editing: `python-docx`, `pdfplumber`, `PyMuPDF`
- Optional: OpenAI GPT API for rewriting bullet points naturally
- Frontend: Django Templates (HTML/CSS)

---

## Installation & Setup

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/ats-score-predictor.git
    cd ats-score-predictor
    ```

2. **Create and activate virtual environment**

    ```bash
    python3 -m venv venv
    source venv/bin/activate       # Linux/Mac
    venv\Scripts\activate          # Windows
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

4. **Run migrations**

    ```bash
    python manage.py migrate
    ```

5. **Run the development server**

    ```bash
    python manage.py runserver
    ```

6. **Open in browser**

    Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) to access the app.

---

## Usage

- Upload your resume file (PDF or DOCX).
- Paste or enter the job description text.
- Click **Analyze** to receive:
  - ATS compatibility score (0-100)
  - Matched and missing skills
  - Semantic similarity heatmap visualization
  - Suggestions to improve your resume
- Download your optimized resume with missing skills integrated.

---

## Future Improvements

- Multi-job description matching and aggregated scoring.
- AI-powered bullet rewriting using OpenAI GPT for natural, contextual skill integration.
- Support for additional resume formats.
- Enhanced resume formatting and style checks.
- User accounts, history, and saved analysis.
- Interactive dashboard with detailed skill gap analytics.

---

## Acknowledgments

- [spaCy](https://spacy.io/)
- [sentence-transformers](https://www.sbert.net/)
- [python-docx](https://python-docx.readthedocs.io/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- OpenAI API for advanced text rewriting (optional)

---

## Contact

For questions or feedback, please contact:  
**Adi Karthikeya S B** – [adikarthikeya1234@gmail.com]  
GitHub: [https://github.com/adikarthikeya2003](https://github.com/adikarthikeya2003)
