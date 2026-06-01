import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from src.logger import logging

VECTORSTORE_DIR = 'vectorstore'

def get_embeddings():
    return SentenceTransformerEmbeddings(
        model_name='all-MiniLM-L6-v2'
    )

def create_vectorstore(chunks: list) -> Chroma:
    try:
        logging.info('Creating vector store')
        embeddings = get_embeddings()
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTORSTORE_DIR
        )
        logging.info('Vector store created')
        return vectorstore

    except Exception as e:
        logging.error(f'Error creating vector store: {str(e)}')
        raise

def load_vectorstore() -> Chroma:
    try:
        logging.info('Loading existing vector store')
        embeddings = get_embeddings()
        vectorstore = Chroma(
            persist_directory=VECTORSTORE_DIR,
            embedding_function=embeddings
        )
        return vectorstore

    except Exception as e:
        logging.error(f'Error loading vector store: {str(e)}')
        raise

def vectorstore_exists() -> bool:
    return os.path.exists(VECTORSTORE_DIR) and \
           len(os.listdir(VECTORSTORE_DIR)) > 0