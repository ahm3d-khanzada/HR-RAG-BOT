# filename: docs/vectorstore.py
import os
import time
import asyncio
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import aiofiles
from fastapi import UploadFile

load_dotenv()

# Environment Variables Validation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

required = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "PINECONE_API_KEY": PINECONE_API_KEY,
    "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME
}
missing = [k for k, v in required.items() if not v]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Constants & Setup
UPLOAD_DIR = Path("./upload_docs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone serverless index: {PINECONE_INDEX_NAME}")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,           # text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print("Waiting for index to be ready...")
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(2)

index = pc.Index(PINECONE_INDEX_NAME)
print(f"Pinecone index '{PINECONE_INDEX_NAME}' connected successfully.")

# Async File Save Helper
async def save_uploaded_file_async(file: UploadFile, save_path: Path):
    """Save uploaded file asynchronously to disk"""
    content = await file.read()
    async with aiofiles.open(save_path, 'wb') as f:
        await f.write(content)
    print(f"File saved to disk: {save_path}")

# Main Async Ingestion Function
async def load_vectorstore_async(
    uploaded_files: List[UploadFile],
    role: str,
    doc_id: str
) -> None:
    """
    Async document ingestion pipeline with progress tracking.
    - Saves uploaded files temporarily
    - Loads, splits, embeds, and upserts to Pinecone
    - Uses role as namespace for access control
    """
    valid_roles = ["Employee", "Team Lead", "HR Executive", "HR Manager"]
    if role not in valid_roles:
        raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")

    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    loop = asyncio.get_running_loop()

    for file in uploaded_files:
        try:
            save_path = UPLOAD_DIR / file.filename

            print(f"Starting upload: {file.filename}")
            await save_uploaded_file_async(file, save_path)

            print(f"Loading document: {file.filename}")
            loader = PyPDFLoader(str(save_path))
            documents = await loop.run_in_executor(None, loader.load)

            if not documents:
                print(f"Warning: No content loaded from {file.filename}")
                os.remove(save_path)
                continue

            # 3. Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
                add_start_index=True
            )
            chunks = text_splitter.split_documents(documents)

            if not chunks:
                print(f"No meaningful chunks in {file.filename}")
                os.remove(save_path)
                continue

            print(f"→ {file.filename}: {len(chunks)} chunks created")

            # Prepare texts, ids, metadatas
            texts = [chunk.page_content for chunk in chunks]
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "text": chunk.page_content,
                    "source": file.filename,
                    "doc_id": doc_id,
                    "role": role,
                    "page": chunk.metadata.get("page"),
                    "start_index": chunk.metadata.get("start_index")
                }
                for chunk in chunks
            ]

            # 4. Generate embeddings with progress
            print(f"Generating embeddings ({len(texts)} chunks)...")
            embeddings = []
            for text in tqdm(texts, desc=f"Embedding {file.filename}"):
                emb = await embed_model.aembed_query(text)
                embeddings.append(emb)

            # 5. Prepare vectors for upsert
            vectors = list(zip(ids, embeddings, metadatas))

            # 6. Upsert in batches with progress
            print(f"Upserting {len(vectors)} vectors to Pinecone (namespace: {role})...")
            batch_size = 100
            total = len(vectors)
            with tqdm(total=total, desc="Upserting", unit="vec") as pbar:
                for i in range(0, total, batch_size):
                    batch = vectors[i:i + batch_size]
                    await loop.run_in_executor(
                        None,
                        lambda b=batch: index.upsert(
                            vectors=b,
                            namespace=role
                        )
                    )
                    pbar.update(len(batch))

            print(f"Successfully indexed: {file.filename} (doc_id: {doc_id})")

            os.remove(save_path)
            print(f"Temp file removed: {save_path}")

        except Exception as e:
            print(f"Error processing {file.filename}: {str(e)}")
            if save_path.exists():
                os.remove(save_path)
            continue

    print("\nAll documents processed and indexed successfully!")