from typing import List
from contextlib import asynccontextmanager
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

from app.db.database import get_vector_store
from app.models import Prayer, PrayerVerseRecommendation
from app.config.llm import oai_llm
from app.schemas.llm import Query, Relevance, Encouragement

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
    Using your internal knowledge of the Bible, identify a verse or passage that best aligns with the refined query and the overall context of the prayer. Choose a verse that clearly reflects the themes and emotional tone expressed in the prayer."""

    human_prompt = """Now, please reframe the following prayer accordingly: {prayer}"""

    system_message = SystemMessage(content=prompt)
    human_message = HumanMessage(content=human_prompt.format(prayer=prayer))

    messages = [system_message] + [human_message]

    return with_structure.invoke(messages)

async def verse_relevance(doc: Document, prayer: str):
    with_structure = oai_llm.with_structured_output(Relevance)
    relevance_prompt = """You are a Bible Verse Retrieval Assistant. Your task is to take a user's prayer and a Bible verse and determine if the verse is relevant to the prayer.

    Follow these steps:

    1. **Analyze the Prayer and Verse:**  
    Read the provided prayer and verse carefully and determine if the verse is relevant to the prayer.
    """

    human_prompt = """Now, please determine if the following verse is relevant to the following prayer: <prayer> {prayer} </prayer> and <verse> {verse} </verse>"""

    system_message = SystemMessage(content=relevance_prompt)
    human_message = HumanMessage(content=human_prompt.format(prayer=prayer, verse=doc.page_content))

    messages = [system_message] + [human_message]

    try: 
        results = await with_structure.ainvoke(messages)
        
        if results.is_relevant:
            # insight_prompt = """You are a Non-Denominational Christian Bible Verse Retrieval Assistant. Your task is to take a user's prayer and a Bible verse and provide an encouragement for the user ground in the verse and God's Word. Limit to 2 sentences. Take a personal relationship with God approach."""

            # human_prompt = """Please provide an encouragement for the following prayer based on the following verse: {verse} and prayer: {prayer}"""

            # system_message = SystemMessage(content=insight_prompt)
            # human_message = HumanMessage(content=human_prompt.format(prayer=prayer, verse=doc.page_content))

            # messages = [system_message] + [human_message]

            # with_structure = oai_llm.with_structured_output(Encouragement)
            # results = await with_structure.ainvoke(messages)
            # doc.metadata['encouragement'] = results.encouragement
            # print(doc)
            doc.metadata['encouragement'] = ""
            return doc
        else:
            return None

    except Exception as e:
        print(f"Error in verse_relevance: {str(e)}")
        raise

async def generate_verse_recommendations(prayer: Prayer) -> List[PrayerVerseRecommendation]:

    try:
        recommendations = []
        search_results = []  # Store results here
        
        # Get the search results within the vector store context
        async with get_verse_store() as vdb:
            query_result = optimize_query(prayer.transcription)
            search_results = await vdb.asimilarity_search_with_score(query_result.verse_text, k=10)
        
        for doc, score in search_results:
            relevance_result = await verse_relevance(doc, prayer.transcription)
            if relevance_result:
                recommendation = PrayerVerseRecommendation(
                    id=str(uuid.uuid4()),
                    prayer_id=prayer.id,
                    book_name=relevance_result.metadata['book_name'],
                    chapter_number=int(relevance_result.metadata['chapter_number']),
                    verse_number_start=int(relevance_result.metadata['verse_number_start']),
                    verse_number_end=int(relevance_result.metadata.get('verse_number_end', relevance_result.metadata['verse_number_start'])),
                    verse_text=relevance_result.page_content,
                    encouragement=relevance_result.metadata['encouragement'],
                    relevance_score=float(score)
                )
                recommendations.append(recommendation)   
        return recommendations
    except Exception as e:
        print(f"Error in generate_verse_recommendations: {str(e)}")
        raise
