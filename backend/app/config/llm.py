# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


oai_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
langchain_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")