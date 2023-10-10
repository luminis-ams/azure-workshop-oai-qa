import os
import time
import argparse
import logging

from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SimpleField,
    SearchField,
)
from dotenv import load_dotenv
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch

logger = logging.getLogger(__name__)


def main(args):
    # Load Markdown documents recursively from a directory
    logger.info("Loading documents...")
    loader = DirectoryLoader(
        path=args.documents_path, loader_cls=UnstructuredMarkdownLoader, glob="**/*.md"
    )
    docs = loader.load()

    # Split documents into chunks
    logger.info("Splitting documents...")
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=args.chunk_size,
        chunk_overlap=0,
        add_start_index=True,
    )
    docs = text_splitter.split_documents(docs)

    # Create Azure OpenAI Embedding Model Client
    logger.info("Connecting to Azure Cognitive Services...")
    os.environ["OPENAI_API_TYPE"] = "azure"
    assert "OPENAI_API_KEY" in os.environ, "OPENAI_API_KEY not set"
    assert "OPENAI_API_BASE" in os.environ, "OPENAI_API_BASE not set"
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        deployment=os.getenv("OPENAI_DEPLOYMENT_EMBEDDING"),
    )

    # Throttle embedding requests to 5 per second due to Azure OpenAI Services rate limits
    def embed_query_throttled(query: str):
        time.sleep(args.throttle)
        return embeddings.embed_query(query)

    # Create Azure Search Vector Store Client and define index schema
    vector_store: AzureSearch = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        embedding_function=embed_query_throttled,
        search_type="hybrid",
        fields=[
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_configuration="default",
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
            ),
            SearchableField(
                name="source",
                type=SearchFieldDataType.String,
            ),
        ],
    )

    # Index documents
    logger.info("Indexing documents...")
    vector_store.add_documents(docs)
    logger.info("Done!")


if __name__ == "__main__":
    load_dotenv(override=True)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--documents-path", type=str, default="data/transformers_docs_full"
    )
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--throttle", type=float, default=1.2)
    args = parser.parse_args()

    main(args)
