from typing import List
from contextlib import asynccontextmanager
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage, SystemMessage

from app.db.database import get_vector_store
from app.models import Prayer, PrayerVerseRecommendation
from app.config.llm import oai_llm
from app.schemas.llm import Query

@asynccontextmanager
async def get_verse_store():
    vector_store, client = None, None
    try:
        vector_store, client = await get_vector_store()
        yield vector_store
    finally:
        if client:
            print("Closing Weaviate client")
            client.close()
            print("Weaviate client closed")

def optimize_query(prayer: str) -> Query:
    with_structure = oai_llm.with_structured_output(Query)
    prompt = """You are a Bible Verse Retrieval Assistant. Your task is to take a user's prayer and reframe it into a refined search query that captures the core theological themes and concepts expressed in the prayer, without including any extraneous words that might skew vector embeddings.

   Follow these steps:

    1. **Analyze the Prayer:**  
    Read the provided prayer carefully and extract its key themes, emotions, and specific requests. Identify detailed aspects such as the emotional state (e.g., feeling overwhelmed, seeking hope), and any specific needs (e.g., guidance, strength, comfort).

    2. **Generate a Refined Query:**  
    Based on the extracted themes, construct a concise, focused query that captures these ideas without any extraneous words. The query should be a string of keywords or phrases that would optimally guide a vector search. For example, if the prayer mentions feeling lost and in need of guidance and hope, a refined query might be:  
    `guidance hope overcoming uncertainty`

    3. **Recommend a Bible Verse:**  
    Using your internal knowledge of the Bible, identify a verse or passage that best aligns with the refined query and the overall context of the prayer. Choose a verse that clearly reflects the themes and emotional tone expressed in the prayer.

    4. **Provide a Justification:**  
    Along with the recommended verse, provide a brief explanation of why you selected this verse and how it relates to the core themes of the prayer."""

    human_prompt = """Now, please reframe the following prayer accordingly: {prayer}"""

    system_message = SystemMessage(content=prompt)
    human_message = HumanMessage(content=human_prompt.format(prayer=prayer))

    messages = [system_message] + [human_message]

    return with_structure.invoke(messages)

async def generate_verse_recommendations(prayer: Prayer) -> List[PrayerVerseRecommendation]:
    print("=== Starting generate_verse_recommendations ===")
    try:
        recommendations = []
        search_results = []  # Store results here
        
        # Get the search results within the vector store context
        async with get_verse_store() as vdb:
            print("Got vector store connection")
            query_result = optimize_query(prayer.transcription)
            print(f"Query optimized: {query_result}")
            search_results = await vdb.asimilarity_search_with_score(query_result.verse_text, k=6)
            print(f"Found {len(search_results)} similar verses")
            print("About to exit vector store context")
        
        print(f"Search results outside context: {search_results}")
        # Process results outside the vector store context
        for doc, score in search_results:
            recommendation = PrayerVerseRecommendation(
                id=str(uuid.uuid4()),
                prayer_id=prayer.id,
                book_name=doc.metadata['book_name'],
                chapter_number=int(doc.metadata['chapter_number']),
                verse_number_start=int(doc.metadata['verse_number_start']),
                verse_number_end=int(doc.metadata.get('verse_number_end', doc.metadata['verse_number_start'])),
                verse_text=doc.page_content,
                justification=query_result.justification,
                relevance_score=float(score)
            )
            recommendations.append(recommendation)
        
        print(f"Generated {len(recommendations)} recommendations")    
        return recommendations
    except Exception as e:
        print(f"Error in generate_verse_recommendations: {str(e)}")
        raise
