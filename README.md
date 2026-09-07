# 🌾 Farmer Scheme Assist

> An AI-powered RAG application that helps farmers understand Indian government agricultural schemes using uploaded scheme documents, semantic search, and real-time web search.

Farmer Scheme Assist is an intelligent agricultural assistance application built using **LangChain, Retrieval-Augmented Generation (RAG), FAISS, Hugging Face Embeddings, OpenAI, Streamlit, and LangSmith**.

The application allows users to ask questions about Indian government farmer schemes in simple language. It follows a **document-first approach** by searching uploaded scheme documents and automatically falling back to web search when the required information is not available in the uploaded documents.

---

## 🚀 Key Features

### 📄 Multi-PDF Document Processing

- Upload multiple government agricultural scheme PDFs.
- Extract text from PDF documents using `PyPDFLoader`.
- Split documents into smaller chunks using `RecursiveCharacterTextSplitter`.
- Generate semantic embeddings using Hugging Face.
- Store and search document embeddings using FAISS.
- Retrieve the most relevant document sections for each question.

### 🔎 Retrieval-Augmented Generation (RAG)

The application uses Retrieval-Augmented Generation to provide answers grounded in the uploaded scheme documents.

```text
User Question
      ↓
Document Retrieval
      ↓
Relevant Document Chunks
      ↓
Context + Question
      ↓
OpenAI LLM
      ↓
Grounded Answer
```
## 🧠 Intelligent Query Routing

### An LLM-based grader determines how each question should be handled.
```
                         User Question
                              │
                              ▼
                       Query Grader LLM
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        OUT_OF_SCOPE       PDF_YES        WEB_SEARCH
              │               │               │
              ▼               ▼               ▼
        Reject Query     PDF Retrieval    Web Search
                              │               │
                              └───────┬───────┘
                                      │
                                      ▼
                              Final LLM Answer
```
