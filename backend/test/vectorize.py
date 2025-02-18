from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore

import weaviate

from backend.config.config import config

print("Starting...")
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
# weaviate_client = weaviate.connect_to_local()
# db = WeaviateVectorStore.from_documents(docs, embeddings, client=weaviate_client)



embeddings = HuggingFaceInferenceAPIEmbeddings(
    api_key=config.HUGGINGFACE_API_KEY, model_name="sentence-transformers/all-MiniLM-l6-v2"
)


hello = "Hello, world!"

vector = embeddings.embed_query(hello)

print(vector)
