# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import sqlite3

import os
from app.config import config
from .prompts import system_prompt, user_prompt
from .state import ContinueAdding
import pickle
import multiprocessing
from functools import partial
import asyncio

from app.db.database import get_vector_store


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def process_single_book(checkpoint_path, db_file_path, book_order):
    """
    Process a single book and save checkpoints.
    """
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    docs = []
    
    book_table = "Book"
    verse_table = "ChapterVerse"
    
    # Get book info
    query = f'SELECT id, name, "order", numberOfChapters FROM {book_table} WHERE "id:1" = \'BSB\' AND "order" = {book_order}'
    cursor.execute(query)
    book = cursor.fetchone()
    
    if not book:
        return []
        
    book_id, book_name, order, num_chapters = book
    
    for chapter in range(1, num_chapters + 1):
        query = f'SELECT number, chapterNumber, bookId, translationId, text FROM {verse_table} WHERE "translationId" = "BSB" AND "bookId" = \'{book_id}\' AND "chapterNumber" = {chapter}'
        cursor.execute(query)
        verses = cursor.fetchall()
        
        agg_page_content = ""
        verse_start = None
        
        while verses:
            verse = verses.pop(0)
            verse_number, chapter_number, book_id, translation_id, text = verse
            
            if verse_start is None:
                verse_start = verse_number
            
            agg_page_content += " " + text
            
            with_continue = llm.with_structured_output(ContinueAdding)
            sys_prompt = SystemMessage(content=system_prompt)
            
            current_verses = HumanMessage(content=user_prompt.format(
                book_name=book_name,
                chapter_number=chapter_number,
                verse_number_start=verse_start,
                verse_number_end=verse_number,
                text=agg_page_content.strip()
            ))
            messages = [sys_prompt] + [current_verses]

            result = with_continue.invoke(messages)
            
            if not result.continue_adding or not verses:
                new_doc = Document(
                    page_content=agg_page_content.strip(),
                    metadata={
                        'verse_number_start': verse_start,
                        'verse_number_end': verse_number,
                        'chapter_number': chapter_number,
                        'book_id': book_id,
                        'book_name': book_name,
                        'translation_id': translation_id
                    }
                )
                docs.append(new_doc)
                
                # Save checkpoint with book order in filename
                book_checkpoint_path = checkpoint_path.replace('.pkl', f'_book_{book_order}.pkl')
                with open(book_checkpoint_path, 'wb') as f:
                    pickle.dump(docs, f)
                
                agg_page_content = ""
                verse_start = None
    
    conn.close()
    return docs

def load_documents_from_db() -> list:
    """
    Connects to a SQLite database and loads documents from the specified table.
    Processes books in parallel using multiprocessing.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_file_path = os.path.join(project_root, "data", "bible.eng.db")
    checkpoint_path = os.path.join(project_root, "data", "vectorize_checkpoint.pkl")
    
    all_docs = []
    
    # Load existing checkpoints if they exist
    for i in range(1, 67):
        book_checkpoint_path = checkpoint_path.replace('.pkl', f'_book_{i}.pkl')
        if os.path.exists(book_checkpoint_path):
            with open(book_checkpoint_path, 'rb') as f:
                book_docs = pickle.load(f)
                all_docs.extend(book_docs)
                print(f"Loaded checkpoint for book {i} with {len(book_docs)} documents")
    
    # Process remaining books in parallel
    with multiprocessing.Pool(processes=2) as pool:
        process_func = partial(process_single_book, checkpoint_path, db_file_path)
        remaining_books = [i for i in range(1, 67) 
                         if not os.path.exists(checkpoint_path.replace('.pkl', f'_book_{i}.pkl'))]
        
        # Process books in pairs
        for i in range(0, len(remaining_books), 2):
            book_pair = remaining_books[i:i+2]
            print(f"Processing books {book_pair} in parallel")
            results = pool.map(process_func, book_pair)
            for docs in results:
                all_docs.extend(docs)
    
    return all_docs


async def create_vector_store_from_docs(docs: list, vdb, tenant: str):
    """
    Creates a Weaviate vector store from a list of LangChain Documents.
    """
    await vdb.aadd_documents(docs, tenant=tenant)
    return 


async def main():
    # -----------------------------------------------
    # Configuration & Initialization
    # ----------------------------------------------
    # Initialize embeddings; you can switch providers if needed.

    # embeddings = HuggingFaceInferenceAPIEmbeddings(
    #     api_key=config.HUGGINGFACE_API_KEY,
    #     model_name="sentence-transformers/all-MiniLM-l6-v2"
    # )
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(project_root, "data")
    
    # Get all checkpoint files
    checkpoint_files = []
    for file in os.listdir(data_dir):
        if file.startswith("vectorize_checkpoint") and file.endswith(".pkl"):
            checkpoint_files.append(os.path.join(data_dir, file))
    
    print(f"Found {len(checkpoint_files)} checkpoint files")
    
    # Initialize vector store
    vdb, client = await get_vector_store()
    all_docs = []
    for checkpoint_file in checkpoint_files:
        try:
            with open(checkpoint_file, 'rb') as f:
                print(f"Loading checkpoint file: {checkpoint_file}")
                docs = pickle.load(f)
                all_docs.extend(docs)
                print(f"Loaded {len(docs)} documents from {checkpoint_file}")
        except Exception as e:
            print(f"Error loading {checkpoint_file}: {e}")
    
    print(f"Total documents loaded: {len(all_docs)}")
    
    # Create vector store from all documents
    if all_docs:
        try:
            await create_vector_store_from_docs(all_docs, vdb, "Bible")
            print("Successfully created vector store from all documents")
        except Exception as e:
            print(f"Error creating vector store: {e}")
    else:
        print("No documents found to process")
    # -----------------------------------------------
    # Load Documents from SQLite DB
    # -----------------------------------------------
    # docs = load_documents_from_db()
    # # -----------------------------------------------
    # # Create a Vector Store from Documents
    # # -----------------------------------------------
    # result = create_vector_store_from_docs(docs, vdb)
    print("Vector store has been created.")


if __name__ == "__main__":
    asyncio.run(main())