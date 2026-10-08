import os
import uuid
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.db.connection import get_db
from app.model.conversation import Conversation, Message
from app.model.document_chunks import DocumentChunk
from app.utils.embeddings import get_embedding

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
TOP_K = 5  # number of most relevant chunks to retrieve

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=GROQ_MODEL,
    temperature=0.3,
)

# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    userId: uuid.UUID
    question: str
    conversationId: int | None = None   # None = start a new conversation


class MessageOut(BaseModel):
    role: str
    content: str

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversationId: int
    answer: str


# ── Helpers ───────────────────────────────────────────────────────────────────
async def retrieve_relevant_chunks(
    query_embedding: list[float],
    user_id: uuid.UUID,
    db: AsyncSession,
    top_k: int = TOP_K,
) -> list[str]:
    """
    Perform cosine similarity search in pgvector filtered by userId.
    Returns the top_k most relevant text chunks.
    """
    result = await db.execute(
        select(DocumentChunk.content)
        .where(DocumentChunk.userId == user_id)
        .order_by(DocumentChunk.embedding.op("<->")(query_embedding))
        .limit(top_k)
    )
    return [row[0] for row in result.fetchall()]


def build_prompt(context_chunks: list[str], question: str) -> str:
    """Build the system prompt by injecting retrieved context."""
    if context_chunks:
        context = "\n\n---\n\n".join(context_chunks)
    else:
        context = "No relevant medical records found for this user."

    return f"""You are a helpful medical assistant called Aura AI. Answer the user's question based ONLY on the medical reports provided below.
If the answer is not found in the reports, say you don't have enough information.
Do not make up any medical information.

FORMATTING RULES (strictly follow these):
- Do NOT use markdown tables or pipe characters (|) under any circumstances.
- Use plain numbered or bullet lists for presenting multiple values or parameters.
- Use bold text (**text**) only for section headings or critical values.
- Present lab results like this format:
    • Total Cholesterol: 268 mg/dL (Reference: < 200 mg/dL) — High
    • LDL Cholesterol: 184 mg/dL (Reference: < 100 mg/dL) — High
- Keep the response clean, readable, and well structured with clear sections.
- Use short paragraphs and line breaks between sections.

MEDICAL REPORTS CONTEXT:
{context}

Answer the question clearly, concisely and in a well structured format."""


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with your medical reports",
    description="Ask a question about your medical reports. Uses RAG to retrieve relevant context from pgvector and answers via Groq LLM.",
)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    # 1. Get or create conversation
    if body.conversationId:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == body.conversationId,
                Conversation.userId == body.userId,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
    else:
        # Auto-generate title from first 60 chars of question
        title = body.question.strip()[:60]
        conversation = Conversation(userId=body.userId, title=title)
        db.add(conversation)
        await db.flush()
        await db.refresh(conversation)

    # 2. Load previous messages for context (last 10)
    history_result = await db.execute(
        select(Message)
        .where(Message.conversationId == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = list(reversed(history_result.scalars().all()))

    # 3. Embed the user's question
    query_embedding = get_embedding(body.question.strip())

    # 4. Retrieve top-K relevant chunks from user's reports
    chunks = await retrieve_relevant_chunks(
        query_embedding=query_embedding,
        user_id=body.userId,
        db=db,
    )

    # 5. Build system prompt with retrieved context
    system_prompt = build_prompt(chunks, body.question)

    # 6. Build message history for LLM
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))

    # Add current question
    lc_messages.append(HumanMessage(content=body.question.strip()))

    # 7. Call Groq LLM
    response = await llm.ainvoke(lc_messages)
    answer = response.content.strip()

    # 8. Save user message and assistant reply to DB
    db.add(Message(conversationId=conversation.id, role="user", content=body.question.strip()))
    db.add(Message(conversationId=conversation.id, role="assistant", content=answer))
    await db.commit()

    return ChatResponse(conversationId=conversation.id, answer=answer)


@router.get(
    "/conversations/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Get all conversations for a user",
)
async def get_conversations(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.userId == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()
    return conversations


@router.get(
    "/conversations/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
    summary="Get all messages in a conversation",
)
async def get_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Message)
        .where(Message.conversationId == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return messages


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a conversation and all its messages",
)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    await db.delete(conversation)
    await db.commit()
    return {"message": "Conversation deleted successfully."}
