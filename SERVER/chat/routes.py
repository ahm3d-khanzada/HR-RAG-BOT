import logging
from fastapi import APIRouter, Depends, Form, HTTPException, status
from typing import Dict, Any
from datetime import datetime

from auth.routes import get_current_user
from .chat_query import answer_query   
from .models import ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["HR Chat"],
    redirect_slashes=False
)

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask HR Questions",
    description="Query internal HR policies, leave, attendance, onboarding, etc. Answers are based only on documents you have access to based on your role."
)
async def hr_chat(
    message: str = Form(
        ...,
        min_length=1,
        max_length=2000,
        description="Your HR-related question or request"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    HR Assistant chat endpoint with strict role-based document access.
    """
    cleaned_message = message.strip()
    if not cleaned_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid question"
        )

    username = current_user.get("username", "unknown")
    user_role = current_user.get("role", "unknown")

    try:
        logger.info(
            f"HR chat request - user: {username} | role: {user_role} | query: {cleaned_message[:100]}..."
        )

        result = await answer_query(
            query=cleaned_message,
            user_role=user_role
        )

        logger.info(
            f"HR chat success - user: {username} | sources found: {len(result.get('sources', []))}"
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", [])
        )

    except Exception as e:
        logger.error(f"HR chat error for {username} (role: {user_role}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't process your HR question right now. Please try again later."
        )