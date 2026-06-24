"""
pdf_loader.py
Loads NCERT PDF using LangChain's PyPDFLoader and builds a FAISS vector store for RAG mode.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os


EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_pdf(pdf_path: str) -> list:
    """Load every page of the PDF and return list of LangChain Document objects."""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return docs


def get_full_text(docs: list) -> str:
    """Concatenate all page content into a single string (used for topic extraction)."""
    return "\n\n".join(d.page_content for d in docs if d.page_content.strip())


def build_vectorstore(docs: list) -> FAISS:
    """
    Split documents into chunks and embed them into a FAISS vector store.
    Used by RAG mode to search relevant content for a user query.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def search_vectorstore(vectorstore: FAISS, query: str, k: int = 4) -> str:
    """Search the vector store for chunks relevant to the user query."""
    results = vectorstore.similarity_search(query, k=k)
    context = "\n\n".join(r.page_content for r in results)
    return context
