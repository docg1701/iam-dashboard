#!/usr/bin/env python3
"""Script to clean all documents from database."""

import asyncio
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.database import get_async_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from sqlalchemy import select


async def clean_all_documents():
    """Clean all documents and chunks from database."""
    async for db_session in get_async_db():
        print("🧹 Cleaning all documents and chunks...")
        
        # Get all documents first
        result = await db_session.execute(select(Document))
        all_documents = result.scalars().all()
        print(f"Found {len(all_documents)} documents to clean")
        
        # Delete all chunks first (foreign key constraint)
        chunk_result = await db_session.execute(select(DocumentChunk))
        all_chunks = chunk_result.scalars().all()
        
        for chunk in all_chunks:
            await db_session.delete(chunk)
        print(f"  ✓ Deleted {len(all_chunks)} chunks")
        
        # Delete all documents
        for doc in all_documents:
            await db_session.delete(doc)
            print(f"  ✓ Deleted document {doc.filename}")
        
        await db_session.commit()
        
        # Clean upload directory
        upload_dir = Path("uploads")
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            print("  ✓ Cleaned upload directory")
        
        print(f"✅ Successfully cleaned {len(all_documents)} documents and all chunks")


async def main():
    """Main function."""
    print("Starting document cleanup...")
    await clean_all_documents()
    print("Document cleanup completed!")


if __name__ == "__main__":
    asyncio.run(main())