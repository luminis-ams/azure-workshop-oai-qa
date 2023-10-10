import re
from typing import Dict, Any, Optional, List
import logging

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains.base import Chain
from langchain.schema import ChatMessage, Document
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.vectorstore import VectorStoreRetriever

from workshop_oai_qa.prompts.query_generation import QUERY_GENERATION_PROMPT
from workshop_oai_qa.prompts.retrieval_qa import RetrievalQAPrompt

logger = logging.getLogger(__name__)


class AssistantMessage(ChatMessage):
    role: str = 'assistant'

    follow_ups: List[str]
    citations: List[Document]
    formatted_content: str


class DocumentAssistantChain(Chain):
    @property
    def input_keys(self) -> List[str]:
        """Keys expected to be in the chain input."""
        return ['input', 'history', 'callbacks']

    @property
    def output_keys(self) -> List[str]:
        """Keys expected to be in the chain output."""
        return [
            'query', 'documents', 'messages', 'response', 'reply', 'follow_ups', 'citations'
        ]

    llm: BaseLanguageModel
    retriever: VectorStoreRetriever

    def generate_search_query(self, input: str):
        """Generate a search query from the input question."""
        messages = QUERY_GENERATION_PROMPT.format_messages(input=input)
        response = self.llm.invoke(messages)

        return response.content

    def extract_follow_ups(self, response: str):
        """
        Extract follow up questions prompts from the response text.
        :param response:
        :return:
        """
        return re.findall(r'<<([^>>]+)>>', response)

    def strip_follow_ups(self, response: str):
        """
        Removes follow up questions prompts from the response text.
        :param response:
        :return:
        """
        return re.sub(r'<<([^>>]+)>>', '', response).strip()

    def extract_citations(self, response: str):
        """
        Extract citation references from the response text.
        :param response:
        :return:
        """
        return re.findall(r'\[([^\]]+)\]', response)

    def replace_citations(self, response: str, citations: List[str]):
        """
        Replace citation references with ordered numerical references.
        :param response:
        :param citations:
        :return:
        """
        for i, citation in enumerate(citations):
            response = response.replace(f'[{citation}]', f'[{i + 1}]')
        return response

    def _call(
            self, 
            inputs: Dict[str, Any], 
            run_manager: Optional[CallbackManagerForChainRun] = None
        ) -> Dict[str, Any]:
        logger.info(f'Running chain with inputs: {inputs}')

        # Generate search query from input question
        logger.info(f'Generating search query for input: {inputs["input"]}')
        query = self.generate_search_query(inputs['input'])

        # Retrieve relevant documents from search query
        logger.info(f'Running search query: {query}')
        documents = self.retriever.get_relevant_documents(query)

        # Generate Q&A prompt from input question, retrieved documents and chat history
        logger.info(f'Running Q&A')
        messages = RetrievalQAPrompt().format_messages(
            input=inputs['input'],
            history=inputs['history'],
            documents=documents,
        )

        # Generate response from Q&A prompt
        response = self.llm.predict_messages(
            messages,
            callbacks=inputs['callbacks'],
        )
        reply = response.content

        # Extract follow up questions and citations from response
        logger.info('Extracting citations')
        documents = {
            doc.metadata['source']: doc
            for doc in documents
        }
        citations = [
            documents[citation]
            for citation in self.extract_citations(reply)
            if citation in documents
        ]

        logger.info('Extracting follow ups')
        follow_ups = self.extract_follow_ups(reply)

        # Clean up response by removing follow-up questions and replacing citations
        logger.info('Stripping reply')
        reply = self.strip_follow_ups(reply)
        reply = self.replace_citations(reply, citations=[doc.metadata['source'] for doc in citations])

        return {
            'query': query,
            'documents': documents,
            'messages': messages,
            'response': response,
            'reply': AssistantMessage(
                content=response.content,
                formatted_content=reply,
                follow_ups=follow_ups,
                citations=citations
            ),
            'follow_ups': follow_ups,
            'citations': citations,
        }
