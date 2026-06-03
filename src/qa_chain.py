from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from src.logger import logging
from langchain_core.prompts import PromptTemplate

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def build_qa_chain(retriever) -> ConversationalRetrievalChain:
    try:
        logging.info('Building QA chain')

        llm = ChatGroq(
            model='llama-3.1-8b-instant',
            temperature=0.1,
            api_key=os.environ.get('GROQ_API_KEY')
        )

        memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key='answer'
        )

        custom_prompt = PromptTemplate(
            template="""You are ScholarMind, an expert AI research assistant specializing in academic document analysis. 

        Your goal is to extract insights from fragmented document text, which may contain OCR typos, broken tables, or partial data.

        Instructions:
        1. **Analyze Aggressively**: The context contains raw page fragments. Piecing them together to form an coherent academic narrative is your core job. Summarize what is visible.
        2. **Absolute Data Grounding**: Never invent, assume, or extrapolate exact numerical values, percentages (e.g., 100%, 0%), or statistical conclusions. If a specific number or statistical decision (reject/accept null hypothesis) is not explicitly printed in the text, do not state it. 
        3. **Handle Messy Text**: Ignore formatting errors, split words (like "se ction"), or raw mathematical formulas when reading text. Focus purely on the underlying findings.
        4. **Fallback Rule**: Only say you cannot find the information if the text below is completely unrelated to the topic of the question.

        <context>
        {context}
        </context>

        <history>
        {chat_history}
        </history>

        Current Question: {question}

        Answer:""",
            input_variables=["context", "chat_history", "question"]
        )

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={'prompt': custom_prompt},
            verbose=False
        )

        logging.info('QA chain built successfully')
        return qa_chain

    except Exception as e:
        logging.error(f'Error building QA chain: {str(e)}')
        raise

def ask_question(qa_chain, question: str) -> dict:
    try:
        logging.info(f'Question: {question}')
        result = qa_chain.invoke({'question': question})

        sources = []
        for doc in result.get('source_documents', []):
            page = doc.metadata.get('page', 'unknown')
            sources.append({
                'page': page + 1,
                'excerpt': doc.page_content[:200] + '...'
            })

        return {
            'answer': result['answer'],
            'sources': sources
        }

    except Exception as e:
        logging.error(f'Error answering question: {str(e)}')
        raise