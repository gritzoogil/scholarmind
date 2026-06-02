import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_classic.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.logger import logging

VECTORSTORE_DIR = 'vectorstore'

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')
    return _embeddings

def create_parent_retriever(chunks: list, filename: str) -> ParentDocumentRetriever:
    try:
        logging.info(f'Creating parent retriever for: {filename}')
        embeddings = get_embeddings()

        vectorstore = Chroma(
            embedding_function=embeddings,
            persist_directory=None  # in-memory, no disk persistence needed
        )

        store = InMemoryStore()

        child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50
        )

        retriever = ParentDocumentRetriever(
            vectorstore=vectorstore,
            docstore=store,
            child_splitter=child_splitter,
            search_kwargs={'k':5}
        )

        retriever.add_documents(chunks)
        logging.info(f'Parent retriever created for: {filename}')
        return retriever

    except Exception as e:
        logging.error(f'Error creating parent retriever: {str(e)}')
        raise

def vectorstore_exists() -> bool:
    return os.path.exists(VECTORSTORE_DIR) and \
           len(os.listdir(VECTORSTORE_DIR)) > 0