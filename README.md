# 🌾 Farmer Scheme Assist

> An AI-powered RAG application that helps farmers understand Indian government agricultural schemes using uploaded PDF documents, semantic search, web search, conversation memory, and AI safety guardrails.

## 🚀 Features

- 📄 Upload multiple agricultural scheme PDF documents
- 🔍 Extract and split PDF content using LangChain
- 🧠 Generate embeddings using Hugging Face
- 🗂️ Store and search document embeddings using FAISS
- 🤖 Generate answers using OpenAI
- 🌐 Automatically search the web when information is not available in uploaded documents
- 🛡️ Agriculture-domain guardrail to reject unrelated questions
- 💬 Chat history / conversation memory
- ⚡ Streaming AI responses
- 📊 LangSmith integration for tracing and monitoring the RAG workflow
- 🖥️ Simple Streamlit user interface

## 🏗️ Architecture

```text
                     ┌──────────────────────┐
                     │   Streamlit Chat UI  │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  User Question       │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Document Retriever  │
                     │      FAISS           │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   Self-RAG Grader    │
                     │  Domain + Routing    │
                     └───────┬───────┬──────┘
                             │       │
                    PDF found│       │Not found
                             │       │
                             ▼       ▼
                       ┌────────┐ ┌─────────────┐
                       │  PDF   │ │ Web Search  │
                       │Context │ │ DuckDuckGo  │
                       └────┬───┘ └──────┬──────┘
                            │             │
                            └──────┬──────┘
                                   ▼
                         ┌──────────────────┐
                         │   OpenAI LLM     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Final Response  │
                         └──────────────────┘
```

## 🛠️ Technologies Used

- Python
- Streamlit
- LangChain
- LangChain Community
- LangChain OpenAI
- LangChain Hugging Face
- FAISS
- Hugging Face Sentence Transformers
- OpenAI
- DuckDuckGo Search
- PyPDF
- LangSmith

## 📁 Project Structure

```text
farmer-scheme-assist/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/farmer-scheme-assist.git
cd farmer-scheme-assist
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

Install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` file yet:

```bash
pip install streamlit python-dotenv langchain langchain-community langchain-openai langchain-huggingface langchain-text-splitters faiss-cpu pypdf sentence-transformers ddgs
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=farmer-scheme-assist
```

> ⚠️ Never commit your `.env` file or API keys to GitHub.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
```

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Open the application in your browser:

```text
http://localhost:8501
```

## 📄 How to Use

### Step 1 — Upload Documents

Use the **Upload Scheme Documents** section in the sidebar to upload one or more government agricultural scheme PDFs.

### Step 2 — Read Documents

Click **Read Documents**.

The application will:

1. Load the PDF documents using `PyPDFLoader`
2. Split the documents into smaller chunks
3. Generate embeddings using `all-MiniLM-L6-v2`
4. Store the embeddings in a FAISS vector database
5. Prepare the documents for semantic search

### Step 3 — Ask Questions

Ask questions such as:

```text
What are the benefits of PM-KISAN?
```

```text
Who is eligible for this scheme?
```

```text
How much financial assistance is provided?
```

### Step 4 — Intelligent Source Selection

The application uses a Self-RAG style routing process.

It checks whether:

- The question is related to agriculture or farmer schemes.
- The uploaded documents contain enough information to answer the question.

The application then selects one of three routes:

```text
PDF_YES
    ↓
Answer using uploaded documents

WEB_SEARCH
    ↓
Search the internet for additional information

OUT_OF_SCOPE
    ↓
Reject unrelated questions
```

## 🧠 RAG Workflow

The application follows a Retrieval-Augmented Generation workflow:

```text
PDF Documents
      ↓
PDF Loader
      ↓
Text Splitting
      ↓
Hugging Face Embeddings
      ↓
FAISS Vector Store
      ↓
Semantic Retrieval
      ↓
Relevant Context
      ↓
OpenAI LLM
      ↓
Final Answer
```

Instead of asking the LLM to answer only from its existing knowledge, the application retrieves relevant information from the uploaded documents and provides that information as context to the model.

## 🌐 Web Search Fallback

If the uploaded documents do not contain enough information to answer a farming-related question, the application automatically uses DuckDuckGo web search.

```text
User Question
      ↓
Check Uploaded Documents
      ↓
Information Available?
   ↙          ↘
 YES           NO
  ↓             ↓
PDF Context   Web Search
  ↓             ↓
  └──────┬──────┘
         ↓
      OpenAI
         ↓
   Final Answer
```

This allows the application to provide more current information when it is not available in the uploaded scheme documents.

## 🛡️ Domain Guardrail

The application includes an AI-powered domain guardrail.

Agriculture-related questions are allowed, including:

- Farmer schemes
- Government subsidies
- Crops
- Farming
- Agriculture
- Rural development
- Financial assistance
- Government programs

Unrelated questions are rejected.

Example:

```text
User:
What are the benefits of PM-KISAN?

Assistant:
Answers the question.
```

```text
User:
Who won the latest football match?

Assistant:
I specialize strictly in farmer schemes and agricultural topics.
```

## 📊 LangSmith Integration

The application is integrated with LangSmith for monitoring and tracing the LangChain workflow.

LangSmith can be used to inspect:

- RAG chain execution
- Prompt execution
- LLM calls
- Response generation
- Execution time
- Errors
- Trace information

Enable LangSmith using:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=farmer-scheme-assist
```

After running the application and asking questions, the LangChain traces will be available in the configured LangSmith project.

## 📦 Requirements

Recommended Python version:

```text
Python 3.11+
```

Main dependencies:

```text
streamlit
python-dotenv
langchain
langchain-community
langchain-openai
langchain-huggingface
langchain-text-splitters
faiss-cpu
pypdf
sentence-transformers
ddgs
```

## 🔐 Environment Variables

| Variable               | Description                           |
| ---------------------- | ------------------------------------- |
| `OPENAI_API_KEY`       | OpenAI API key used for LLM responses |
| `LANGCHAIN_TRACING_V2` | Enables LangSmith tracing             |
| `LANGCHAIN_API_KEY`    | LangSmith API key                     |
| `LANGCHAIN_PROJECT`    | LangSmith project name                |

## 🎯 Example Questions

Try asking:

- What is PM-KISAN?
- What are the benefits of PM-KISAN?
- Who is eligible for the scheme?
- How much financial assistance is provided?
- What documents are required?
- How can farmers apply?
- What government schemes are available for farmers?
- What subsidies are available for agriculture?

## ⚠️ Important Notes

- Uploaded documents are processed during the current Streamlit session.
- The FAISS vector store is maintained in Streamlit session state.
- The Hugging Face embedding model may be downloaded the first time it is used.
- Web search requires an active internet connection.
- OpenAI API usage may incur costs.
- LangSmith tracing is optional but recommended for monitoring the application.
- Always verify important government-scheme information using official government sources before making financial or eligibility decisions.

## 🚀 Future Enhancements

- 📌 Persistent vector database
- 🗣️ Multilingual support for Indian languages
- 🎙️ Voice-based farmer assistance
- 📚 More government scheme datasets
- 👨‍🌾 Personalized scheme recommendations
- ☁️ Cloud deployment

## 👨‍💻 Author

**Shafrith**

Built as a Generative AI / RAG learning project using LangChain, Streamlit, FAISS, Hugging Face, OpenAI, and LangSmith.

---

⭐ If you find this project useful, consider giving the repository a star!
