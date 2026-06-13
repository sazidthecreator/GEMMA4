import os
from typing import Optional

from fastapi import FastAPI
from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

app = FastAPI()
API_AUTH_TOKEN = os.getenv("VOCAL_CORE_API_TOKEN")
MAX_INPUT_LENGTH = int(os.getenv("VOCAL_CORE_MAX_INPUT_LENGTH", "4000"))

# Initializing Engine
llm = ChatOllama(model="gemma", temperature=0.6)
system_instruction = """[INSERT YOUR FULL SYSTEM PROMPT WITH FEW-SHOT EXAMPLES HERE]"""
prompt = ChatPromptTemplate.from_messages(
    [("system", system_instruction), ("human", "{text}")])
chain = prompt | llm


class TextRequest(BaseModel):
    text: str


def validate_api_token(authorization: Optional[str]):
    if not API_AUTH_TOKEN:
        return

    expected = f"Bearer {API_AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


@app.post("/transcreate")
async def transcreate(request: TextRequest, authorization: str | None = Header(default=None)):
    validate_api_token(authorization)

    text = request.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text must not be empty",
        )

    if len(text) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"text exceeds maximum length of {MAX_INPUT_LENGTH} characters",
        )

    try:
        response = chain.invoke({"text": text})
        return {"formatted_text": response.content}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription failed",
        )

# Run with: uvicorn vocal_core_api:app --reload --port 8000
