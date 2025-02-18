# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

import sqlite3
import weaviate
import os
from backend.config.config import config


def load_documents_from_db() -> list:
    """
    Connects to a SQLite database and loads documents from the specified table.
    
    Expects the table to have columns: id, title, and content.
    Returns a list of LangChain Document objects.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_file_path = os.path.join(project_root, "data", "bible.eng.db")

    book_table = "Book"
    verse_table = "ChapterVerse"
    commentary_table = "CommentaryChapterVerse"


    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    # Adjust the query if your table has a different structure or columns.
    query = f'SELECT id, name FROM {book_table} WHERE "id:1" = \'BSB\''
    cursor.execute(query)
    books = cursor.fetchall()

    query = f'SELECT number, chapterNumber, bookId, translationId, text FROM {verse_table} WHERE "translationId" = "BSB"'
    cursor.execute(query)
    verses = cursor.fetchall()

    # John Gill Commentary
    # query = f'SELECT number, chapterNumber, bookId, commentaryId, text, name FROM {commentary_table} WHERE "id" = john-gill"'
    # cursor.execute(query)
    # verses = cursor.fetchall()
    # print(f"Found {len(verses)} verses")
    docs = []

    for verse in verses:
        verse_number, chapter_number, book_id, translation_id, text = verse
        
        # Find matching book name
        book_name = None
        for book in books:
            if book[0] == book_id:  # book[0] is the id
                book_name = book[1]  # book[1] is the name
                break
                
        if book_name:
            # Replace book_id with book_name in the verse tuple
            docs.append(Document(page_content=text, metadata={'verse_number': verse_number, 'chapter_number': chapter_number, 'book_id': book_id, 'book_name': book_name, 'translation_id': translation_id}))

        
    



    # docs = []
    # for row in rows:
    #     doc_id, title, content = row
    #     docs.append(Document(page_content=content, metadata={'id': doc_id, 'title': title}))

    conn.close()
    return docs


def create_vector_store_from_docs(docs: list, vdb):
    """
    Creates a Weaviate vector store from a list of LangChain Documents.
    """
    vdb.add_documents(docs)
    return 


def main():
    # -----------------------------------------------
    # Configuration & Initialization
    # ----------------------------------------------
    # Initialize embeddings; you can switch providers if needed.

    # embeddings = HuggingFaceInferenceAPIEmbeddings(
    #     api_key=config.HUGGINGFACE_API_KEY,
    #     model_name="sentence-transformers/all-MiniLM-l6-v2"
    # )
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=config.OPENAI_API_KEY
    )

    # Connect to Weaviate (adjust connection as needed)
    weaviate_client = weaviate.connect_to_local()
    vdb = WeaviateVectorStore(client=weaviate_client,text_key="text", embedding=embeddings, index_name="node1")

    # -----------------------------------------------
    # Load Documents from SQLite DB
    # -----------------------------------------------
    docs = load_documents_from_db()

    # # -----------------------------------------------
    # # Create a Vector Store from Documents
    # # -----------------------------------------------
    result = create_vector_store_from_docs(docs, vdb)
    print("Vector store has been created.")


if __name__ == "__main__":
    main()