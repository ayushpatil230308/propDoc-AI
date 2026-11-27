## 🚀 My Projects

### 📄 PropDoc AI – Smart Document Intelligence

AI-powered application for uploading, analyzing, questioning, and comparing PDF documents using OCR and OpenAI.

🔗 **Live Demo:** https://propdoc-ai-bhurnggnfd7ejy9t6gaapm.streamlit.app


## 🚀 Features

- 📄 Upload PDF documents
- 🔍 Extract text from PDF files
- 🧠 OCR support for scanned documents
- 🤖 AI-powered document analysis
- 💬 Ask questions about documents
- 🔄 Compare two PDF documents
- 📊 Find matching information and differences
- 🌐 Support for English, Marathi, and Hindi
- 📥 Download extracted text and AI reports
- 🔐 Secure OpenAI API key using Streamlit Secrets

## 🛠️ Technologies Used

- Python
- Streamlit
- OpenAI API
- PyMuPDF
- Tesseract OCR
- Pillow
- pytesseract

## 📂 Project Structure

```text
PropDoc-AI/
│
├── app.py
├── requirements.txt
├── packages.txt
├── secrets.toml.example
└── README.md
```

## ▶️ How to Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

## 🔑 OpenAI API Key

The application requires an OpenAI API key.

For Streamlit deployment, add the key to **Streamlit Secrets**:

```toml
OPENAI_API_KEY = "your-api-key"
```

**Do not upload your real API key to GitHub.**

## ☁️ Live Demo

🚀 **Live Demo:** Add your Streamlit app link here after deployment.

Example:

```text
https://your-project-name.streamlit.app
```

## 🔄 How It Works

```text
Upload PDF
    ↓
Extract Text / OCR
    ↓
AI Document Analysis
    ↓
Ask Questions
    ↓
Compare Documents
    ↓
Download Results
```

## ⚠️ Disclaimer

PropDoc AI provides document-reading and analysis assistance. It does not provide legal advice or guarantee the authenticity or legal validity of documents. Important information should be verified using official records and qualified professionals.
