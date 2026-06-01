from langchain_ollama import OllamaLLM
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from src.logger import logging

def build_qa_chain(vectorstore):
    try:
        logging.info('Building QA chain')

        llm = OllamaLLM(
            model='llama3.2',
            temperature=0.1,
            base_url='http://localhost:11434'
        )

        memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key='answer'
        )

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(
                search_type='similarity',
                search_kwargs={'k': 4}
            ),
            memory=memory,
            return_source_documents=True,
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