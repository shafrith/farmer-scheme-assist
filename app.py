import os
import tempfile
import json
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools import DuckDuckGoSearchResults

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# --- NEMO GUARDRAILS IMPORTS ---
from nemoguardrails import RailsConfig, LLMRails

# --- LANGSMITH OBSERVABILITY TRIGGER ---
load_dotenv()

st.set_page_config(page_title="Farmer Scheme Assist", page_icon="🌾", layout="wide")

# --- INITIALIZE NEMO GUARDRAILS ---
@st.cache_resource
def load_guardrails():
    config = RailsConfig.from_path("./config")
    return LLMRails(config)

guardrails = load_guardrails()

# --- INITIALIZE MEMORY & WIDGET STATES ---
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = InMemoryChatMessageHistory()

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "upload_success" not in st.session_state:
    st.session_state.upload_success = None

# Auto-load existing FAISS database if available
if "doc_memory" not in st.session_state: 
    if os.path.exists("faiss_index"):
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.doc_memory = FAISS.load_local(
            "faiss_index", embeddings, allow_dangerous_deserialization=True
        )
        if os.path.exists(os.path.join("faiss_index", "schemes.json")):
            with open(os.path.join("faiss_index", "schemes.json"), "r") as f:
                st.session_state.scheme_list = json.load(f)
        else:
            st.session_state.scheme_list = ["Previously uploaded schemes"]
    else:
        st.session_state.doc_memory = None
        st.session_state.scheme_list = []

# --- SIDEBAR: DOCUMENT INGESTION & MANAGEMENT ---
with st.sidebar:
    st.header("📂 Scheme Documents")
    
    if st.session_state.doc_memory is not None:
        st.success("✅ Database loaded and ready!")
        with st.expander("Currently Loaded Schemes"):
            for scheme in st.session_state.scheme_list:
                st.write(f"- {scheme}")
    else:
        st.caption("No database found. Please upload a PDF to begin.")
        
    st.divider()

    # Display persistent upload success message if set
    if st.session_state.upload_success:
        st.success(st.session_state.upload_success)
        st.session_state.upload_success = None  # Clear after displaying once

    uploaded_files = st.file_uploader(
        "Add new PDF files", 
        type=["pdf"], 
        accept_multiple_files=True,
        key=f"pdf_uploader_{st.session_state.uploader_key}"
    )

    if st.button("Process & Add Documents"):
        if uploaded_files:
            with st.spinner("Processing documents..."):
                all_chunks = []
                uploaded_names = []
                
                for uploaded_file in uploaded_files:
                    uploaded_names.append(uploaded_file.name.replace(".pdf", ""))
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                        
                    loader = PyPDFLoader(tmp_file_path)
                    docs = loader.load()
                    
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = text_splitter.split_documents(docs)
                    
                    all_chunks.extend(chunks)
                    os.remove(tmp_file_path)
                
                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                
                # Append to existing store or create new
                if st.session_state.doc_memory is None:
                    st.session_state.doc_memory = FAISS.from_documents(all_chunks, embeddings)
                    st.session_state.scheme_list = uploaded_names
                else:
                    st.session_state.doc_memory.add_documents(all_chunks)
                    for name in uploaded_names:
                        if name not in st.session_state.scheme_list:
                            st.session_state.scheme_list.append(name)
                
                # Persist FAISS index and scheme metadata locally
                st.session_state.doc_memory.save_local("faiss_index")
                with open(os.path.join("faiss_index", "schemes.json"), "w") as f:
                    json.dump(st.session_state.scheme_list, f)
                
                # Set success message & bump widget key to clear the file uploader box
                st.session_state.upload_success = f"✅ Successfully added {len(uploaded_files)} document(s)!"
                st.session_state.uploader_key += 1
                st.rerun()
        else:
            st.warning("Please select a PDF file first.")
                
    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.chat_memory.clear()
        st.rerun()

# --- MAIN UI: CHAT INTERFACE ---
st.title("🌾 Farmer Scheme Assist")
st.markdown("Hello! Ask me anything about farming schemes. I will check my database or search the web!")

for msg in st.session_state.chat_memory.messages:
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

if prompt := st.chat_input("E.g., What are the benefits of PM-KISAN?"):
    with st.chat_message("user"):
        st.write(prompt)

    if st.session_state.doc_memory is None:
        with st.chat_message("assistant"):
            st.warning("⚠️ Please upload your first scheme document on the left sidebar.")
        st.stop()

    with st.chat_message("assistant"):
        
        # 1. RUN NEMO GUARDRAILS (INPUT CHECK)
        rail_check = guardrails.generate(messages=[{"role": "user", "content": prompt}])
        
        if isinstance(rail_check, dict):
            rail_output = rail_check.get("content", "")
        elif isinstance(rail_check, list):
            rail_output = rail_check[0].get("content", "")
        else:
            rail_output = str(rail_check)
            
        if "Out of Scope" in rail_output:
            st.write(rail_output)
            st.session_state.chat_memory.add_user_message(prompt)
            st.session_state.chat_memory.add_ai_message(rail_output)
            st.stop()

        # 2. LOCAL VECTOR RETRIEVAL
        available_schemes = "\n".join(f"- {name}" for name in st.session_state.scheme_list)
        retriever = st.session_state.doc_memory.as_retriever(search_kwargs={"k": 6})
        doc_context = "\n\n".join(doc.page_content for doc in retriever.invoke(prompt))

        # 3. ROUTING GRADER (Handles full questions, scheme titles, and keywords)
        grader_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        grader_prompt = PromptTemplate.from_template(
            """You are a relevance grader for an agricultural scheme assistant.
            Evaluate whether the provided Context contains information relevant to the User Query.
            
            The User Query might be a full question OR simply a scheme name/keyword (e.g., 'PM Kisan Maan Dhan Yojana').
            
            Rules:
            1. If the Context contains facts, eligibility, benefits, descriptions, or rules related to the scheme or topic in the query, output exactly: PDF_YES
            2. Only if the Context is completely empty, irrelevant, or fails to mention the queried topic at all, output exactly: WEB_SEARCH
            
            Output ONLY one of those two phrases without punctuation.
            
            Context:
            {context}
            
            User Query: {question}"""
        )
        route = grader_llm.invoke(grader_prompt.format(context=doc_context, question=prompt)).content.strip().upper()

        if "PDF_YES" in route:
            st.caption("✅ Source: Uploaded Documents")
            final_context = doc_context
        else:
            st.caption("🌐 Source: Internet Search")
            with st.spinner("Searching the web for scheme information..."):
                web_search = DuckDuckGoSearchResults()
                final_context = f"Internet Search Results:\n{web_search.invoke(f'{prompt} agriculture farmer scheme India')}"

        # 4. FINAL ANSWER GENERATION (STREAMING WITH RUNNABLE MEMORY)
        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly, helpful agricultural assistant talking to a farmer.
            Use plain, simple language without technical jargon. 
            Use the provided context and the conversation history to answer the farmer's inquiry clearly.
            
            INVENTORY OF UPLOADED SCHEMES:
            {inventory}

            Context to base your answer on:
            {context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        rag_chain = rag_prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True) | StrOutputParser()
        
        chain_with_history = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: st.session_state.chat_memory,
            input_messages_key="question",
            history_messages_key="chat_history",
        )
        
        response_stream = chain_with_history.stream(
            {
                "context": final_context,
                "question": prompt,
                "inventory": available_schemes
            },
            config={"configurable": {"session_id": "farmer_session"}}
        )
        
        st.write_stream(response_stream)