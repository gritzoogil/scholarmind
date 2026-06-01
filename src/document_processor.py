import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.logger import logging

def load_and_split_pdf(pdf_path: str) -> list:
    try:
        logging.info(f'Loading PDF: {pdf_path}')

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f'PDF not found: {pdf_path}')

        loader = PyPDFLoader(pdf_path)
        pages  = loader.load()
        logging.info(f'Loaded {len(pages)} pages')

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=['\n\n', '\n', '. ', ' ', '']
        )
        chunks = splitter.split_documents(pages)
        logging.info(f'Split into {len(chunks)} chunks')

        return chunks

    except Exception as e:
        logging.error(f'Error processing PDF: {str(e)}')
        raise