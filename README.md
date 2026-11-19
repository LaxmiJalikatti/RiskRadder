# RiskRadder – AI-Powered Terms and Conditions Risk Analyzer

RiskRadder is an AI-powered application that analyzes Terms and Conditions, Privacy Policies, and other legal documents to identify potentially risky clauses. It uses Natural Language Processing (NLP) and Machine Learning to classify clauses into risk categories, assign severity levels, and calculate an overall risk score.

The application provides simple explanations and recommendations to help users understand potentially important terms before accepting an agreement.

## 🌐 Live Demo

Try RiskRadder here: https://riskradder.onrender.com/

## Features

- **Multiple Input Options:** Upload PDF, DOCX, TXT, and image files, or paste text directly.
- **Text Extraction:** Extracts text from documents and uses OCR to read text from images.
- **NLP Processing:** Cleans and splits document text into individual clauses or sentences.
- **Machine Learning Classification:** Uses TF-IDF features and Logistic Regression to classify clauses.
- **10 Risk Categories:** Identifies potentially risky clauses across ten predefined categories.
- **Severity Levels:** Classifies detected risks as High, Medium, or Low.
- **Risk Score:** Calculates an overall risk score from 0 to 100.
- **Simple Explanations:** Provides predefined explanations and recommendations for detected risks.
- **Text Report:** Displays a formatted plain-text analysis that can be copied.
- **PDF Report:** Generates a downloadable PDF report containing the analysis results.

## Risk Categories

| Category | Severity |
|---|---|
| Data Sharing | High |
| Arbitration Clause | High |
| Liability Limitation | High |
| Location Tracking | High |
| Auto Renewal | Medium |
| No Refund Policy | Medium |
| Account Termination | Medium |
| Data Retention | Medium |
| Policy Change Without Notice | Medium |
| Marketing Consent | Low |

## Technology Stack

**Programming Language:** Python

**Machine Learning and NLP:**
- Scikit-learn
- TF-IDF Vectorizer
- Logistic Regression
- NLTK

**Document Processing:**
- pdfplumber
- python-docx
- Pytesseract
- Pillow

**Desktop Application:**
- CustomTkinter

**Web Application:**
- Flask
- HTML
- CSS
- JavaScript

**Reports and Data:**
- ReportLab
- Pandas
- Joblib

## Machine Learning Model

RiskRadder uses a Logistic Regression classifier with a combination of word-level and character-level TF-IDF features.

The model is trained using labelled clauses belonging to ten risk categories and a No Risk category.

Model evaluation uses Repeated Stratified 5-Fold Cross-Validation with three repetitions.

The website reports an accuracy of approximately 81.55% (±3.14%). This is a cross-validation result, not a guarantee that every clause will be classified correctly.

## How It Works

1. **Input Document:** Upload a document, image, or paste Terms and Conditions text.
2. **Text Extraction:** Extract text from the selected input.
3. **Preprocessing:** Clean the text and split it into sentences.
4. **Classification:** Use the trained Machine Learning model to identify risk categories.
5. **Risk Assessment:** Assign severity levels and calculate the overall risk score.
6. **Explanation:** Display predefined explanations and recommendations.
7. **Report Generation:** View or download the analysis as a text or PDF report.

## Project Structure

```text
RiskRadder/
│
├── data/
│   └── training_data.csv
│
├── models/
│   └── risk_model.joblib
│
├── modules/
│   ├── classifier.py
│   ├── preprocessor.py
│   ├── file_reader.py
│   ├── risk_engine.py
│   ├── recommender.py
│   ├── report_generator.py
│   └── text_output.py
│
├── gui/
│   └── app.py
│
├── web/
│   └── index.html
│
├── reports/
│
├── main.py
├── server.py
├── train_model.py
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/LaxmiJalikatti/RiskRadder.git
cd RiskRadder
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Desktop Application

```bash
python main.py
```

### 6. Run the Web Application

```bash
python server.py
```

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

### OCR Setup

To analyze image files, install Tesseract OCR separately and ensure it is accessible to the application. The Python package alone does not install the Tesseract OCR engine.

## Limitations

- RiskRadder is an automated analysis tool and does not provide legal advice.
- Classification accuracy depends on the training dataset.
- Some risk categories may be classified less accurately than others.
- Poor image quality can affect OCR text extraction.
- Sentence splitting may occasionally cause a clause to be counted more than once.
- The system may not identify every possible risk in a legal document.

## Future Enhancements

- Android application support.
- Support for additional document formats.
- Expansion of the labelled training dataset.
- Support for multiple languages.
- Improved clause classification and explanations.
- Document comparison functionality.

## Project Information

**Project Title:** RiskRadder – AI-Powered Terms and Conditions Risk Analyzer

**Developed By:**
- Laxmi A J
- Dikshita

**Department:** Computer Science and Engineering

**College:** Jain College of Engineering, Belagavi

**Project Guides:**
- Prof. Rashmi Ingalagi
- Dr. Uttam Patil

## Disclaimer

RiskRadder is developed as an academic mini project. The results are intended for informational purposes only and should not be considered professional legal advice.

---

**Developed by Team RiskRadder**
