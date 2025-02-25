import pickle
import os
import asyncio

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage

from .state import Query

from app.config.config import config
from app.config.llm import oai_llm
from app.db.database import get_vector_store


def view_checkpoints():
    """
    View the contents of vectorization checkpoint files.
    Displays information about each book's documents and their contents.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    checkpoint_base = os.path.join(project_root, "data", "vectorize_checkpoint_book_{}.pkl")
    
    total_docs = 0
    for book_num in range(1, 67):
        checkpoint_path = checkpoint_base.format(book_num)
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'rb') as f:
                docs = pickle.load(f)
                total_docs += len(docs)
                print(f"\nBook {book_num}:")
                print(f"Number of documents: {len(docs)}")
                if docs:
                    # Print details of first document
                    first_doc = docs[0]
                    print("\nFirst document metadata:")
                    for key, value in first_doc.metadata.items():
                        print(f"  {key}: {value}")
                    print(f"\nFirst document content preview: {first_doc.page_content[:200]}...")
                    
                    # Print details of last document
                    last_doc = docs[-1]
                    print("\nLast document metadata:")
                    for key, value in last_doc.metadata.items():
                        print(f"  {key}: {value}")
                    print(f"\nLast document content preview: {last_doc.page_content[:200]}...")
    
    print(f"\nTotal documents across all books: {total_docs}")

def optimize_query(prayer):
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
    Along with the recommended verse, provide a brief explanation of why you selected this verse and how it relates to the core themes of the prayer.


    For example, given the prayer:  
    "Lord, I'm feeling overwhelmed and lost in these uncertain times. I need a sign of hope and direction."  
    Your output might be:
    `Query(verse="I will instruct you and teach you in the way you should go; I will counsel you with my loving eye on you.", verse_details="Psalm 32:8 ", justification="This verse provides reassurance of divine guidance and hope, which aligns with the prayer's request for direction and support during uncertain times.")`"""
    
    human_prompt = """Now, please reframe the following prayer accordingly: {prayer}"""

    system_message = SystemMessage(content=prompt)
    human_message = HumanMessage(content=human_prompt.format(prayer=prayer))

    messages = [system_message] + [human_message]

    return with_structure.invoke(messages)

async def main():
    # Add this to test the new function
    # view_checkpoints()

    vdb, client = await get_vector_store()


    # prayer = "Dear Lord, I am feeling lost and need guidance. I need a sign of hope and direction."
    # query = optimize_query(prayer)
    # print(query)

    words = "money  and greed and lust"

    result = await vdb.asimilarity_search_with_score(words)
    print(result)
    # result = vdb.similarity_search_with_score("how do i go to heaven")
    # print(result)

if __name__ == "__main__":
    asyncio.run(main())