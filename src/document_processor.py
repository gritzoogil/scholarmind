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

        if len(pages) == 0:
            raise ValueError('PDF appears to be empty or unreadable')
        logging.info(f'Loaded {len(pages)} pages')

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=['\n\n', '\n', '. ', ' ', '']
        )
        chunks = []
        for page in pages:
            page_chunks = splitter.split_documents([page])
            for chunk in page_chunks:
                chunk.metadata['page'] = page.metadata.get('page', 0)
                chunk.metadata['source'] = pdf_path
            chunks.extend(page_chunks)

        if len(chunks) == 0:
            raise ValueError('No text could be extracted from this PDF')

        logging.info(f'Split into {len(chunks)} chunks')

        return chunks

    except Exception as e:
        logging.error(f'Error processing PDF: {str(e)}')
        raise