import os

import pytest
from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain.chat_models.base import BaseChatModel
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.embeddings import Embeddings
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.vectorstore import VectorStoreRetriever
from langchain.vectorstores import AzureSearch
from langchain.schema.messages import get_buffer_string

from workshop_oai_qa.chain import DocumentAssistantChain
from workshop_oai_qa.prompts.query_generation import QUERY_GENERATION_PROMPT
from workshop_oai_qa.prompts.retrieval_qa import RetrievalQAPrompt


@pytest.fixture(scope="module")
def env_config():
    load_dotenv()
    return os.environ


@pytest.fixture(scope="module")
def llm(env_config) -> BaseChatModel:
    return AzureChatOpenAI(
        deployment_name=env_config["OPENAI_DEPLOYMENT_COMPLETION"],
        openai_api_base=env_config["OPENAI_API_BASE"],
        openai_api_version=env_config["OPENAI_API_VERSION"],
        openai_api_key=env_config["OPENAI_API_KEY"],
        openai_api_type="azure",
    )


@pytest.fixture(scope="module")
def embeddings(env_config) -> Embeddings:
    return OpenAIEmbeddings(
        model='text-embedding-ada-002',
        deployment=os.getenv('OPENAI_DEPLOYMENT_EMBEDDING'),
        openai_api_base=env_config["OPENAI_API_BASE"],
        openai_api_version=env_config["OPENAI_API_VERSION"],
        openai_api_key=env_config["OPENAI_API_KEY"],
        openai_api_type="azure",
    )


@pytest.fixture(scope="module")
def retriever(embeddings, env_config) -> VectorStoreRetriever:
    return AzureSearch(
        azure_search_endpoint=env_config['AZURE_SEARCH_ENDPOINT'],
        azure_search_key=env_config['AZURE_SEARCH_KEY'],
        index_name=env_config['AZURE_SEARCH_INDEX'],
        embedding_function=embeddings.embed_query,
        search_type='hybrid',
    ).as_retriever(search_kwargs={'k': 5})


@pytest.fixture(scope="module")
def chain(llm, retriever) -> DocumentAssistantChain:
    return DocumentAssistantChain(
        llm=llm,
        retriever=retriever,
    )


def test_llm(llm: BaseLanguageModel):
    print(llm.invoke('Hello, world!'))


def test_embeddings(embeddings: Embeddings):
    print(embeddings.embed_query('Hello, world!'))


def test_retriever(retriever):
    print(retriever.get_relevant_documents('Hello, world!'))


def test_query_generation(llm: BaseChatModel):
    messages = QUERY_GENERATION_PROMPT.format_messages(input='What is transformers library?')
    print(messages)

    response = llm.predict_messages(messages)
    print(response)


def test_retrieval_qa(llm: BaseChatModel):
    messages = RetrievalQAPrompt().format_messages(
        input='What is transformers library?',
        history=[],
        documents=[],
    )
    print(get_buffer_string(messages))


def test_chain(chain: DocumentAssistantChain):
    response = chain({
        'input': 'What is transformers library?',
    })

    print(response)
    print(response['response'].content)


FOLLOW_UP_QUESTIONS = [
    "What are some examples of tasks that can be performed using the Transformers library?",
    "Can I use the Transformers library with different deep learning frameworks?",
    "How can I fine-tune a pretrained model using the Transformers library?"
]


def test_followups(chain: DocumentAssistantChain):
    text = 'Follow ups:\n' + '\n'.join(map(lambda x: f'<<{x}>>', FOLLOW_UP_QUESTIONS))

    follow_ups = chain.extract_follow_ups(text)
    assert follow_ups == FOLLOW_UP_QUESTIONS

    stripped = chain.strip_follow_ups(text)
    assert stripped == 'Follow ups:'


def test_citations(chain: DocumentAssistantChain):
    text = 'Hello world[citation1]! [citation2]'

    citations = chain.extract_citations(text)
    assert citations == ['citation1', 'citation2']

    replaced = chain.replace_citations(text, citations)
    assert replaced == 'Hello world[1]! [2]'
