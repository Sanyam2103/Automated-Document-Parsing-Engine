# GSA Document Analyzer

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![Framework](https://img.shields.io/badge/framework-FastAPI-green)

An intelligent, AI-powered system designed for the automated analysis of GSA (General Services Administration) document submissions. This project leverages a sophisticated **Hybrid Retrieval-Augmented Generation (RAG)** architecture to provide fast, accurate, and human-aligned compliance verification.

The system parses unstructured documents, validates them against deterministic business rules, redacts Personally Identifiable Information (PII), and uses a vector-based AI search to generate comprehensive compliance checklists, strategic negotiation briefs, and client-ready communications.

---

## ✨ Key Features

*   **Hybrid RAG Architecture**: Combines the reliability of rule-based validation with the contextual power of AI-driven retrieval for superior accuracy and explainability.
*   **Automated Document Processing**: Parses unstructured text from various document types (Company Profiles, Past Performance, Pricing) into structured data.
*   **Intelligent Compliance Analysis**: Automatically identifies compliance issues, from critical blocking errors to minor recommendations, and cites the specific GSA rules that apply.
*   **AI-Powered Content Generation**: Generates professional, context-aware outputs including:
    *   **Strategic Negotiation Briefs**: Internal summaries for procurement officers.
    *   **Client Communications**: Actionable emails for vendors detailing required fixes.
*   **PII Redaction**: Automatically detects and redacts sensitive information (like emails and phone numbers) to ensure data privacy and compliance with security standards.
*   **Scalable & Extensible Design**: Built on a modern, stateless architecture that is ready to scale from a single server to a distributed system of microservices.
*   **Interactive Frontend**: A clean, user-friendly interface to upload documents, trigger analysis, and view detailed results in real-time.

---

## 🏛️ Architecture Overview

The system is built on a modular, service-oriented architecture designed for scalability and maintainability.

1.  **Ingestion & Parsing**: Documents are uploaded via a FastAPI endpoint. A robust parsing module extracts structured data from unstructured text. PII is redacted at this stage.
2.  **Deterministic Validation**: The structured data is first run through a fast, rule-based validator that checks for clear, non-negotiable compliance issues (e.g., missing UEI, invalid DUNS format).
3.  **Hybrid RAG Analysis**:
    *   The descriptions of any issues found are used as semantic queries against a **Vector Store** of GSA rules.
    *   This retrieves only the most relevant rule snippets, providing focused context to the AI.
4.  **LLM Generation**: The validated data, identified issues, and retrieved rule contexts are passed to a Large Language Model (LLM) to generate the final analysis, brief, and client email.

This hybrid approach ensures that the system is both fast (by handling simple checks deterministically) and intelligent (by using AI for complex contextual analysis), providing the best of both worlds.

For a detailed explanation of the system's design, scalability roadmap, and extensibility patterns, please see **[ARCHITECTURE.md](architecture.md)**.

---

## 🛠️ Tech Stack

*   **Backend**: Python, FastAPI
*   **AI & Machine Learning**: Google Gemini, LangChain, Sentence-Transformers
*   **Vector Store**: ChromaDB
*   **Data Handling**: Pydantic
*   **Frontend**: HTML, CSS, JavaScript (no frameworks)
*   **Deployment**: Uvicorn (ready for Docker, Kubernetes)

---

## 🚀 Getting Started

### Prerequisites

*   Python 3.9+
*   An environment variable file (`.env`) with your `GOOGLE_API_KEY`.

### Installation

1.  **Clone the repository:**
    ```
    git clone https://github.com/Sanyam2103/Automated-Document-Parsing-Engine.git
    cd Automated-Document-Parsing-Engine
    ```

2.  **Create and activate a virtual environment:**
    ```
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    ```
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the root of the project and add your API key:
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    ```

### Running the Application

1.  **Start the FastAPI server:**
    ```
    uvicorn app.main:app --reload
    ```

2.  **Open your browser** -
3.  Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger UI.
- Or open [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html) for a minimal frontend.

4. **Run Tests**

```
test.bat
```
- Runs all required unit tests (missing UEI, invalid email, NAICS→SIN mapping, Past Performance, PII Redaction, RAG sanity test).

---

## 💻 Usage

The application is designed to be used through its web interface.

1.  **Load Documents**: Use the "Quick Samples" dropdown to load pre-filled vendor data or manually paste your document text into the text areas. You can add multiple documents for a single ingestion.
2.  **Ingest Documents**: Click the **"Ingest Documents"** button. This will upload, parse, and redact the documents, preparing them for analysis. A request ID will be generated.
3.  **Analyze Compliance**: Once ingestion is complete, click the **"Analyze"** button. The backend will perform the full hybrid analysis.
4.  **Review Results**: The results panel will update with the complete analysis, including the compliance status, a list of issues found, the parsed data, AI-generated content, and rule citations.
5.  **Use Debug Tools**: The debug panel at the bottom provides tools to check system health, test AI service connections, and inspect the raw data associated with a request ID.

---



## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

