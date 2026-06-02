from langchain_ollama import OllamaLLM
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from src.logger import logging
from langchain_core.prompts import PromptTemplate

def build_qa_chain(vectorstore):
    try:
        logging.info('Building QA chain')

        llm = OllamaLLM(
            model='llama3.2',
            temperature=0.1,
            base_url='http://127.0.0.1:11434'
        )

        memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            output_key='answer'
        )

        custom_prompt = PromptTemplate(
            template="""You are ScholarMind, an expert AI research assistant. Your task is to answer the user's question accurately using only the provided context and conversation history.

        Guidelines:
        1. Be direct, objective, and specific.
        2. Rely heavily on the provided context. If the context contains partial information, use it to construct a factual, partial answer.
        3. If the context truly contains zero relevant information to answer the question, reply exactly with: "I'm sorry, but I cannot find that information in the provided document." Do not attempt to make up an answer.

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
            retriever=vectorstore.as_retriever(
                search_type='mmr',
                search_kwargs={
                    'k': 6,
                    'fetch_k': 20,
                    'lambda_mult': 0.7
                    }
            ),
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