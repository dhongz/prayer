from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from langchain_weaviate.vectorstores import WeaviateVectorStore


import weaviate
import logging

from app.config import config
from app.config.llm import langchain_embeddings

logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
logging.getLogger("prayer-api").setLevel(logging.INFO)
logger = logging.getLogger("prayer-api")


engine = create_async_engine(
    config.ASYNC_DATABASE_URL,
    echo=True,  # Set to False in production
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Async dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



async def get_weaviate_client():
    try:
        client = weaviate.connect_to_custom(
            http_host=config.WEAVIATE_URL,
            http_port=8080,
            http_secure=False,
            grpc_host=config.WEAVIATE_URL,
            grpc_port=50051,
            grpc_secure=False,
            # headers={
            #     "X-OpenAI-Api-Key": settings.OPENAI_API_KEY
            # },
            # auth_credentials=weaviate.auth.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
        )
        return client
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {e}")
        raise

async def get_vector_store():
    client = await get_weaviate_client()
    vector_store = WeaviateVectorStore(
        client=client,
        index_name="node1",
        text_key="content",
        embedding=langchain_embeddings,
        # use_multi_tenancy=True
    )
    return vector_store, client  # Return both the store and client