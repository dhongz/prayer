from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

import weaviate
from backend.config.config import config


def main():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=config.OPENAI_API_KEY
    )

    weaviate_client = weaviate.connect_to_local()

    vdb = WeaviateVectorStore(client=weaviate_client,text_key="text", embedding=embeddings, index_name="node1")

    result = vdb.similarity_search_with_score("struggling with family issues")
    print(result)
if __name__ == "__main__":
    main()