import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from operator import itemgetter

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import DuckDuckGoSearchResults

load_dotenv()

st.set_page_config(page_title="Farmer Scheme Assist", page_icon="🌾", layout="wide")

# --- INITIALIZE MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
# Renamed from 'vector_store' to 'doc_memory' for easier understanding
if "doc_memory" not in st.session_state: 
    st.session_state.doc_memory = None
if "scheme_list" not in st.session_state:
    st.session_state.scheme_list = []

# --- SIDEBAR: MULTI-FILE UPLOAD (User-Friendly UI) ---
with st.sidebar:
    st.header("📂 Upload Scheme Documents")
    st.caption("Add your PDF files here so I can read them.")
    
    uploaded_files = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True)
    
    if st.button("Read Documents"):
        if uploaded_files:
            with st.spinner(f"Reading {len(uploaded_files)} documents. This might take a moment..."):
                all_chunks = []
                uploaded_names = []
                
                for uploaded_file in uploaded_files:
                    uploaded_names.append(uploaded_file.name.replace(".pdf", ""))
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # --- 1. Document loader: Reads the raw text out of the uploaded PDF file ---
                    loader = PyPDFLoader(tmp_file_path)
                    docs = loader.load()
                    
                    # --- 2. Text splitter: Breaks the long document down into smaller, manageable paragraphs ---
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = text_splitter.split_documents(docs)
                    
                    all_chunks.extend(chunks)
                    os.remove(tmp_file_path)
                
                # --- 3. Embedding: Converts the text paragraphs into numbers so the AI can understand meaning ---
                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                
                # --- 4. Vector store: Saves those numbers into a highly searchable, temporary database (FAISS) ---
                st.session_state.doc_memory = FAISS.from_documents(all_chunks, embeddings)
                
                st.session_state.scheme_list = uploaded_names
                
                st.success(f"✅ Success! I have finished reading {len(uploaded_files)} documents.")
        else:
            st.warning("Please upload at least one PDF file first.")
            
    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- MAIN UI: CHAT INTERFACE ---
st.title("🌾 Farmer Scheme Assist")
st.markdown("Hello! I am here to help you understand government agricultural schemes. Ask me anything about farming benefits.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("E.g., What are the benefits of PM-KISAN?"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.doc_memory is None:
        with st.chat_message("assistant"):
            st.warning("⚠️ Please upload your scheme documents on the left sidebar before we begin.")
        st.stop()

    with st.chat_message("assistant"):
        formatted_history = "\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages[:-1]]
        )
        available_schemes = "\n".join(f"- {name}" for name in st.session_state.scheme_list)

        # --- 5. Retriever: Searches our database for the top 5 paragraphs that best match the user's question ---
        retriever = st.session_state.doc_memory.as_retriever(search_kwargs={"k": 5})
        retrieved_docs = retriever.invoke(prompt)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
            
        doc_context = format_docs(retrieved_docs)

        # --- SELF-RAG GRADER: Domain Guardrail & Source Routing ---
        grader_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        grader_prompt = PromptTemplate.from_template(
            """You are a smart router for a Farmer Scheme Assistant. 
            Evaluate the user's question and choose ONE of three paths.
            
            1. First, is the question related to agriculture, farming, crops, weather, rural development, financial aid, or any government programs/acronyms (e.g., PM-KISAN, subsidies)?
               *Be lenient.* If the user asks about benefits, payouts, or acronyms that sound like government schemes, assume it is YES.
               If it is completely unrelated (e.g., video games, cooking, movies), output exactly: OUT_OF_SCOPE
               
            2. If YES, look at the Context. Does the Context contain sufficient information to answer the question?
               If YES, output exactly: PDF_YES
               If NO, output exactly: WEB_SEARCH
            
            Output ONLY one of those three exact phrases without any extra punctuation.

            Context:
            {context}

            Question: {question}
            """
        )
        
        with st.spinner("Thinking..."):
            route = grader_llm.invoke(
                grader_prompt.format(context=doc_context, question=prompt)
            ).content.strip().upper()

        # --- DECISION GATE ---
        if "OUT_OF_SCOPE" in route:
            # Domain Guardrail: Politely refuse non-farming questions
            st.caption("🛑 Out of Scope")
            out_of_scope_msg = "I specialize strictly in farmer schemes and agricultural topics. I'm afraid I cannot help with other subjects. Please feel free to ask me anything related to farming!"
            st.write(out_of_scope_msg)
            st.session_state.messages.append({"role": "assistant", "content": out_of_scope_msg})
            st.stop()
            
        elif "PDF_YES" in route:
            # Found in the uploaded documents
            st.caption("✅ Source: Uploaded Documents")
            final_context = doc_context
            
        else:
            # Farming related, but not in the documents: Search the web
            st.caption("🌐 Source: Internet Search")
            with st.spinner("I'm checking the internet for the latest farming information..."):
                web_search = DuckDuckGoSearchResults()
                # Appending keywords ensures DuckDuckGo focuses heavily on agricultural policy
                web_results = web_search.invoke(f"{prompt} agriculture farmer scheme India")
                final_context = f"Internet Search Results:\n{web_results}"

        # --- FINAL ANSWER GENERATION ---
        template = """You are a friendly, helpful agricultural assistant talking to a farmer.
        Use plain, simple language without technical jargon. 
        Use the provided context (from documents or the web) and the conversation history to answer their question.
        
        INVENTORY OF UPLOADED SCHEMES:
        {inventory}

        Conversation History:
        {chat_history}

        Context to base your answer on:
        {context}

        Question: {question}
        Answer:"""
        
        rag_prompt = PromptTemplate.from_template(template)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

        # --- LANGSMITH TRACED PIPELINE ---
        # Because LangSmith is active in the environment, this entire LCEL chain 
        # (the prompt formatting, LLM call, and string parsing) is automatically 
        # logged, timed, and evaluated in the LangSmith project dashboard.
        rag_chain = rag_prompt | llm | StrOutputParser()
        
        response_stream = rag_chain.stream({
            "context": final_context,
            "question": prompt,
            "chat_history": formatted_history,
            "inventory": available_schemes
        })
        
        # Stream the friendly response to the UI
        full_response = st.write_stream(response_stream)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})