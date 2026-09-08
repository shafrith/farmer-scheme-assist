# 🌾 Farmer Scheme Assist

> An AI-powered RAG application that helps farmers understand Indian government agricultural schemes using uploaded PDF documents, semantic search, web search, conversation memory, and AI safety guardrails.

Farmer Scheme Assist is a **Retrieval-Augmented Generation (RAG)** application built with **LangChain, Streamlit, FAISS, Hugging Face Embeddings, OpenAI, DuckDuckGo Search, and NeMo Guardrails**.

The application allows users to upload government agricultural scheme documents and ask questions in natural language. It first checks whether the question is within the application's scope, searches the uploaded documents for relevant information, and automatically falls back to an internet search when the uploaded documents do not contain the required answer.

---

## 🚀 Features

- 📄 Upload and process multiple PDF scheme documents
- 🔎 Semantic document search using FAISS
- 🧠 Hugging Face sentence embeddings
- 🤖 OpenAI-powered answer generation
- 🌐 Automatic web search fallback using DuckDuckGo
- 🛡️ NeMo Guardrails for out-of-scope question handling
- 💬 Conversation memory for contextual follow-up questions
- 💾 Persistent FAISS vector database
- 📋 Maintains a list of previously processed schemes
- ⚡ Streaming AI responses
- 🖥️ Interactive Streamlit interface
- 📊 LangSmith-compatible LangChain workflow tracing

---

## 🛠️ Technologies Used

- Python
- Streamlit
- LangChain
- LangChain Community
- LangChain OpenAI
- LangChain Hugging Face
- FAISS
- Hugging Face Embeddings
- OpenAI
- DuckDuckGo Search
- NeMo Guardrails
- LangSmith
- PyPDF

---

## 🧠 How the Application Works

The application follows this workflow:

```text
                 ┌─────────────────────┐
                 │   User asks a       │
                 │      question       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  NeMo Guardrails    │
                 │   Scope Checking    │
                 └──────────┬──────────┘
                            │
                    ┌───────┴────────┐
                    │                │
                 Out of Scope       Valid
                    │                │
                    ▼                ▼
                 Block        FAISS Retrieval
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Routing Grader  │
                            │ PDF or Web?     │
                            └────────┬────────┘
                                     │
                           ┌─────────┴─────────┐
                           │                   │
                        PDF_YES             WEB_SEARCH
                           │                   │
                           ▼                   ▼
                    Uploaded PDFs       DuckDuckGo Search
                           │                   │
                           └─────────┬─────────┘
                                     │
                                     ▼
                              Context + Memory
                                     │
                                     ▼
                              OpenAI LLM
                                     │
                                     ▼
                              Final Response
```

---

## 📄 Document Processing

Users can upload one or more PDF files from the Streamlit sidebar.

Each PDF is:

1. Temporarily saved to disk.
2. Loaded using `PyPDFLoader`.
3. Split into smaller chunks.
4. Converted into embeddings.
5. Added to the FAISS vector database.
6. Persisted locally for future application runs.

The application uses:

```text
Chunk Size    : 1000
Chunk Overlap : 200
```

This allows the application to retrieve relevant sections of large government scheme documents efficiently.

---

## 🔎 Semantic Search with FAISS

The application uses the Hugging Face embedding model:

```text
all-MiniLM-L6-v2
```

The generated embeddings are stored in a **FAISS vector database**.

When the user asks a question, the application retrieves the top 5 relevant document chunks:

```python
retriever = st.session_state.doc_memory.as_retriever(
    search_kwargs={"k": 5}
)
```

The retrieved content is then provided to the LLM as context.

---

## 🧭 Intelligent PDF / Web Routing

The application does not always perform an internet search.

A routing grader first checks whether the uploaded PDF documents contain enough information to answer the question.

The grader returns either:

```text
PDF_YES
```

or:

```text
WEB_SEARCH
```

### PDF_YES

If the uploaded documents contain the required information, the application uses the retrieved PDF content.

The UI displays:

```text
✅ Source: Uploaded Documents
```

### WEB_SEARCH

If the uploaded documents do not contain enough information, the application performs an internet search using DuckDuckGo.

The UI displays:

```text
🌐 Source: Internet Search
```

This creates a hybrid **RAG + Web Search** architecture.

---

## 🌐 Web Search

For questions that cannot be answered from the uploaded documents, the application uses:

```python
DuckDuckGoSearchResults()
```

The search query is enhanced with:

```text
agriculture farmer scheme India
```

This helps focus web search results on Indian agricultural schemes and farmer-related information.

---

## 🛡️ NeMo Guardrails

The application uses **NeMo Guardrails** to control the type of questions users can ask.

The guardrails configuration is loaded from:

```text
./config
```

The application initializes the guardrails using:

```python
config = RailsConfig.from_path("./config")
guardrails = LLMRails(config)
```

Before the RAG workflow runs, the user's question is checked by the guardrails.

If the question is classified as out of scope, the application returns the guardrail response and does not continue to document retrieval or web search.

This provides an additional safety and scope-control layer.

---

## 💬 Conversation Memory

The application maintains conversation history using:

```python
InMemoryChatMessageHistory
```

This allows the chatbot to understand follow-up questions based on previous messages.

For example:

```text
User:
What is PM-KISAN?

Assistant:
PM-KISAN is...

User:
Who is eligible?

Assistant:
Farmers meeting the eligibility requirements...
```

The previous conversation is passed to the LLM through:

```python
MessagesPlaceholder(variable_name="chat_history")
```

The application also provides a **Clear Chat History** button in the sidebar.

---

## 💾 Persistent Vector Database

The FAISS database is saved locally in:

```text
faiss_index/
```

The application automatically loads the existing database when it starts.

The scheme names are stored separately in:

```text
faiss_index/schemes.json
```

This means previously processed documents do not need to be uploaded and processed again every time the application starts.

---

## ⚡ Streaming Responses

The application uses streaming for the final OpenAI response:

```python
ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True
)
```

The response is displayed progressively using Streamlit's:

```python
st.write_stream()
```

This provides a more interactive chatbot experience.

---

## 🔐 Environment Variables

Create a `.env` file in the project root.

Example:

```env
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=farmer-scheme-assist
```

Do not commit your `.env` file to GitHub.

Your `.gitignore` should contain:

```gitignore
# Environment variables
.env

# Data files
*.pdf
data/

# Python / Virtual Environment
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd

# Streamlit config
.streamlit/

# OS / Editor Files
.vscode/
.idea/
.DS_Store
Thumbs.db
```

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/farmer-scheme-assist.git
cd farmer-scheme-assist
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

---

## 📥 Install Dependencies

Install the required Python packages:

```bash
pip install streamlit
pip install python-dotenv
pip install langchain
pip install langchain-community
pip install langchain-openai
pip install langchain-huggingface
pip install langchain-text-splitters
pip install faiss-cpu
pip install sentence-transformers
pip install pypdf
pip install ddgs
pip install nemoguardrails
```

You can also create a `requirements.txt` file and install everything with:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Streamlit application with:

```bash
streamlit run app.py
```

After starting the application, Streamlit will provide a local URL similar to:

```text
http://localhost:8501
```

Open the URL in your browser.

---

## 📄 Upload Scheme Documents

When the application starts for the first time, the sidebar will show:

```text
No database found. Please upload a PDF to begin.
```

To add documents:

1. Open the sidebar.
2. Select **Add new PDF files**.
3. Upload one or more government scheme PDFs.
4. Click **Process & Add Documents**.
5. Wait for document processing to finish.
6. The FAISS database will be created automatically.

After processing, the application displays:

```text
✅ Database loaded and ready!
```

---

## 💡 Example Questions

You can ask questions such as:

```text
What are the benefits of PM-KISAN?
```

```text
Who is eligible for this scheme?
```

```text
What documents are required to apply?
```

```text
How much financial assistance is provided?
```

```text
How can a farmer apply for the scheme?
```

```text
What is the official eligibility criteria?
```

If the answer is not available in the uploaded documents, the application automatically performs a web search.

---

## 🏗️ RAG Pipeline

The application's RAG pipeline consists of the following stages:

### 1. Document Loading

```text
PDF
 ↓
PyPDFLoader
```

### 2. Text Splitting

```text
Document
 ↓
RecursiveCharacterTextSplitter
 ↓
Chunks
```

### 3. Embeddings

```text
Text Chunks
 ↓
Hugging Face Embeddings
 ↓
Vectors
```

### 4. Vector Storage

```text
Vectors
 ↓
FAISS
 ↓
faiss_index/
```

### 5. Retrieval

```text
User Question
 ↓
FAISS Similarity Search
 ↓
Top 5 Relevant Chunks
```

### 6. Routing

```text
Retrieved Context
 ↓
OpenAI Grader
 ↓
PDF_YES / WEB_SEARCH
```

### 7. Generation

```text
Context
+
Conversation History
+
User Question
 ↓
OpenAI
 ↓
Final Answer
```

---

## 🧩 Main Components

### Streamlit

Provides the interactive web interface, sidebar, file upload, chat interface, status messages, and streaming output.

### PyPDFLoader

Loads text content from uploaded PDF documents.

### RecursiveCharacterTextSplitter

Splits large documents into smaller overlapping chunks suitable for embedding and retrieval.

### Hugging Face Embeddings

Uses:

```text
all-MiniLM-L6-v2
```

to convert text into numerical vector representations.

### FAISS

Stores and searches document embeddings efficiently.

### OpenAI

Used for:

- Routing/grading
- Final answer generation
- Context-aware responses

### DuckDuckGo

Provides web search when the uploaded documents do not contain the required answer.

### NeMo Guardrails

Checks user questions before the RAG workflow and prevents out-of-scope requests.

### LangChain Memory

Maintains conversation history so the chatbot can answer follow-up questions.

### LangSmith

Can be used to trace and monitor the LangChain workflow, including LLM calls and retrieval-related execution.

---

## 📊 LangSmith

The application can be integrated with LangSmith for observing and debugging the LangChain workflow.

Set the following variables in `.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=farmer-scheme-assist
```

LangSmith can help monitor:

- LLM calls
- Prompt execution
- Retrieval workflow
- Web search execution
- Chain execution
- Response generation
- Errors and latency

This is useful for debugging and improving the RAG pipeline.

---

## 🗂️ Generated Files

When documents are processed, the application creates:

```text
faiss_index/
```

and:

```text
faiss_index/schemes.json
```

The FAISS directory contains the locally persisted vector database.

`schemes.json` stores the names of uploaded scheme documents.

These generated files can be excluded from GitHub if you prefer to keep uploaded document data local.

---

## 🔄 Adding More Documents

The application supports adding new PDFs after the initial database has been created.

For example:

```text
Initial upload
    ↓
PM-KISAN.pdf
    ↓
FAISS database created

Later upload
    ↓
PMFBY.pdf
PM-KUSUM.pdf
    ↓
Documents added to existing FAISS database
```

Existing documents remain available for retrieval.

---

## 🧹 Clear Chat History

The sidebar contains:

```text
Clear Chat History
```

Clicking this button removes the current conversation history while keeping the document database intact.

---

## 🔒 Security Notes

Never commit API keys or secrets to GitHub.

Keep sensitive values inside `.env`:

```env
OPENAI_API_KEY=...
LANGCHAIN_API_KEY=...
```

Make sure `.env` is included in `.gitignore`.

Uploaded PDF files can also be excluded from GitHub using:

```gitignore
*.pdf
data/
```

---

## ⚠️ Important Notes

The application uses AI-generated responses. Users should verify important information such as:

- Eligibility requirements
- Financial assistance amounts
- Application deadlines
- Required documents
- Government rules
- Official application procedures

For official information, users should verify details with the relevant Government of India department or official government portal.

---

## 🎯 Project Objective

The main objective of Farmer Scheme Assist is to demonstrate how modern Generative AI technologies can be combined to build a practical agricultural information assistant.

The project demonstrates:

```text
Generative AI
      +
RAG
      +
Vector Database
      +
Semantic Search
      +
Web Search
      +
Conversation Memory
      +
AI Guardrails
      +
LangChain
      +
LangSmith
      +
Streamlit
```

This makes the application a practical example of a **production-oriented RAG architecture with safety controls and hybrid information retrieval**.

---

## 🚀 Future Improvements

Possible future enhancements include:

- 🔐 User authentication
- 👨‍🌾 Personalized scheme recommendations
- 🌐 Multilingual support including Tamil and Hindi
- 🎙️ Voice-based questions
- 📱 Mobile-friendly interface
- 🏛️ Integration with official government APIs
- 📚 Automatic government scheme document updates
- 🗃️ Metadata-based filtering
- 📊 Analytics dashboard
- 🧠 Improved query routing
- 🔍 Source citations for retrieved information
- ☁️ Cloud-based vector database
- 🚀 Deployment using Streamlit Cloud or other cloud platforms

---

## 📜 License

This project is created for educational and demonstration purposes.

You may modify and extend the project according to your requirements.

---

## 👨‍💻 Author

**Shafrith**

Built as a Generative AI / RAG learning project using:

**Python • LangChain • Streamlit • FAISS • Hugging Face • OpenAI • NeMo Guardrails • DuckDuckGo • LangSmith**

---

## ⭐ If You Like This Project

If you find this project useful, consider giving the repository a ⭐ on GitHub.
