import os

import streamlit as st
from langchain.chat_models import AzureChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch

from workshop_oai_qa.chain import DocumentAssistantChain


@st.cache_resource
def conversation_chain():
    env_config = os.environ

    # Create Azure OpenAI Chat Model Client
    llm = AzureChatOpenAI(
        deployment_name=env_config["OPENAI_DEPLOYMENT_COMPLETION"],
        openai_api_base=env_config["OPENAI_API_BASE"],
        openai_api_version=env_config["OPENAI_API_VERSION"],
        openai_api_key=env_config["OPENAI_API_KEY"],
        openai_api_type="azure",
        streaming=True
    )

    # Create Azure OpenAI Embedding Model Client
    embeddings = OpenAIEmbeddings(
        model='text-embedding-ada-002',
        deployment=os.getenv('OPENAI_DEPLOYMENT_EMBEDDING'),
        openai_api_base=env_config["OPENAI_API_BASE"],
        openai_api_version=env_config["OPENAI_API_VERSION"],
        openai_api_key=env_config["OPENAI_API_KEY"],
        openai_api_type="azure",
    )

    # Create Azure Search Vector Store Client
    retriever = AzureSearch(
        azure_search_endpoint=env_config['AZURE_SEARCH_ENDPOINT'],
        azure_search_key=env_config['AZURE_SEARCH_KEY'],
        index_name=env_config['AZURE_SEARCH_INDEX'],
        embedding_function=embeddings.embed_query,
        search_type='hybrid',
    ).as_retriever(search_kwargs={'k': 5})

    # Return Document Assistant Chain
    return DocumentAssistantChain(
        llm=llm,
        retriever=retriever,
    )
