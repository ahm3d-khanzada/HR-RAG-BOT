# filename: rag/query.py
import os
import asyncio
from typing import Dict, List
from dotenv import load_dotenv

from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

# Environment Validation
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

required_env_vars = {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "PINECONE_API_KEY": PINECONE_API_KEY,
    "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME
}

missing = [key for key, value in required_env_vars.items() if not value]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize Clients
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# Updated HR-Focused RAG Prompt
prompt = PromptTemplate.from_template(
    """
You are a professional, helpful, and confidential HR assistant for our company.
Your role is to answer questions based **only** on the HR documents and policies provided in the context below.

Rules:
- Answer clearly, politely, and concisely using only the provided context.
- If the question is about a policy, explain it accurately and refer to the source.
- For summary requests, provide a short, structured summary of key points.
- If the context does not contain enough relevant information or the user asks about something outside their access level, respond exactly with:
  "I'm sorry, I don't have access to that information or it's not covered in the available HR documents."
- Do NOT make up information, speculate, or give advice outside the documents.
- Always include relevant source document names at the end (e.g., "Source: Employee_Handbook_2025.pdf").

Question: {question}

Relevant HR Context (only documents you have access to):
{context}

Answer:
"""
)

# Create the RAG chain
rag_chain = prompt | llm

# Role-Filtered RAG Query (unchanged logic, updated messages)
async def answer_query(query: str, user_role: str) -> Dict[str, any]:
    """
    Perform a role-filtered RAG query against Pinecone.
    Uses the user's role as namespace to ensure they only see documents they have access to.

    Args:
        query (str): User's HR-related question
        user_role (str): One of: "Employee", "Team Lead", "HR Executive", "HR Manager"

    Returns:
        dict: {"answer": str, "sources": list[str]}
    """
    try:
        # 1. Generate query embedding
        embedding = await asyncio.to_thread(embed_model.embed_query, query)

        # 2. Query Pinecone - filter by user's role namespace
        results = await asyncio.to_thread(
            index.query,
            vector=embedding,
            top_k=5,
            include_metadata=True,
            namespace=user_role   # Critical: role-based access control
        )

        matches = results.get("matches", [])

        if not matches:
            return {
                "answer": "I'm sorry, I don't have access to that information or it's not covered in the available HR documents.",
                "sources": []
            }

        # 3. Extract context and sources
        context_parts = []
        sources = set()

        for match in matches:
            metadata = match["metadata"]
            text_chunk = metadata.get("text", "")
            source = metadata.get("source", "Unknown document")

            if text_chunk.strip():
                context_parts.append(text_chunk.strip())
                sources.add(source)

        if not context_parts:
            return {
                "answer": "I'm sorry, I don't have access to that information or it's not covered in the available HR documents.",
                "sources": []
            }

        context = "\n\n".join(context_parts)

        # 4. Generate answer using LLM
        response = await asyncio.to_thread(
            rag_chain.invoke,
            {"question": query, "context": context}
        )

        final_answer = response.content.strip()

        # 5. Append sources if any
        if sources:
            final_answer += f"\n\n**Sources:** {', '.join(sorted(sources))}"

        return {
            "answer": final_answer,
            "sources": list(sorted(sources))
        }

    except Exception as e:
        print(f"Error in HR RAG query for role '{user_role}': {str(e)}")
        return {
            "answer": "Sorry, something went wrong while processing your HR query. Please try again later.",
            "sources": []
        }